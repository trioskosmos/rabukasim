import copy
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from engine.models.ability import Ability

from engine.game.effects.choice_resolution import handle_choice
from engine.game.effects.condition_resolution import check_condition
from engine.game.effects.movement import move_member
from engine.game.effects.pending_effect_resolution import resolve_pending_effect
from engine.game.effects.rules import apply_system_rules
from engine.models.ability import (
    Ability,
    ConditionType,
    EffectType,
    ResolvingEffect,
    TriggerType,
)
from engine.models.opcodes import Opcode
from tools import bytecode_codec as ability_codec

try:
    from engine.game.numba_utils import JIT_AVAILABLE
except ImportError:
    JIT_AVAILABLE = False


class EffectMixin:
    """
    Mixin for GameState that handles effect resolution and choices.
    """

    def _process_rule_checks(self) -> None:
        """Rule 10: Rule Processing & Check Timing (Rule 9.5.3)."""
        looping = True
        while looping:
            looping = False
            rules_applied = apply_system_rules(self)
            if rules_applied:
                looping = True
            if self.triggered_abilities and not self.pending_choices:
                # DEBUG
                # print(f"DEBUG: Processing triggers. Count={len(self.triggered_abilities)}")
                # Optimize: Re-use pre-allocated buffers
                p_triggers = self._trigger_buffers
                p_triggers[0].clear()
                p_triggers[1].clear()

                for i, (pid, _ab, _ctx) in enumerate(self.triggered_abilities):
                    p_triggers[pid].append(i)
                ap = self.current_player
                if p_triggers[ap]:
                    idx = p_triggers[ap][0]
                    pid, ab, ctx = self.triggered_abilities.pop(idx)
                    # print(f"DEBUG: Popped trigger for player {pid} index {idx}")
                    self._play_automatic_ability(pid, ab, ctx)
                    looping = True
                    continue
                nap = 1 - ap
                if p_triggers[nap]:
                    idx = p_triggers[nap][0]
                    pid, ab, ctx = self.triggered_abilities.pop(idx)
                    # print(f"DEBUG: Popped trigger for player {pid} index {idx} (NAP)")
                    self._play_automatic_ability(pid, ab, ctx)
                    looping = True
                    continue

    def _check_remote_triggers(self, event_type: TriggerType, context: Dict[str, Any]) -> None:
        """Scan Hand/Discard for abilities that trigger from non-stage zones."""
        for pid in range(2):
            p = self.players[pid]
            zones = [("HAND", p.hand), ("DISCARD", p.discard), ("LIVE", p.live_zone)]
            for zone_name, zone_list in zones:
                for i, cid in enumerate(zone_list):
                    if cid < 0:
                        continue
                    card = self.member_db.get(cid) or self.live_db.get(cid)
                    if not card:
                        continue
                    for ab in card.abilities:
                        # Filter out conditions that should be evaluated per-effect or require selection context
                        # e.g. HAS_LIVE_CARD, COST_CHECK (if used as filter), OPPONENT_CHOICE
                        trigger_conditions = [
                            c
                            for c in ab.conditions
                            if c.type
                            not in (
                                ConditionType.HAS_LIVE_CARD,
                                ConditionType.COST_CHECK,
                                ConditionType.OPPONENT_CHOICE,
                                ConditionType.OPPONENT_HAS,
                            )
                        ]

                        if not all(self._check_condition(p, cond, context) for cond in trigger_conditions):
                            continue

                        if ab.trigger == event_type and any(
                            eff.effect_type == EffectType.TRIGGER_REMOTE for eff in ab.effects
                        ):
                            ctx = context.copy()
                            ctx.update({"zone": zone_name, "zone_index": i, "card_id": cid})
                            self.triggered_abilities.append((pid, ab, ctx))

    def _handle_cost(self, player_id: int, ability: Ability, context: Dict[str, Any] = None) -> bool:
        from engine.game.effects.cost_resolution import handle_cost

        if context is None:
            context = {}
        return handle_cost(self, player_id, ability, context)

    def _play_automatic_ability(self, player_id: int, ability: Ability, context: Dict[str, Any] = None) -> None:
        """Resolve an automatic ability (Rule 9.5)."""
        if context is None:
            context = {}
        if self.verbose:
            print(f"DEBUG: Entering _play_automatic_ability for player {player_id}")
        p = self.players[player_id]
        cid = context.get("card_id", -1)
        self.current_resolving_ability = ability
        self.current_resolving_ability_frame = getattr(ability, "sparse_frame_index", None)
        area = context.get("area", -1)
        if area >= 0 and p.stage[area] >= 0:
            cid = p.stage[area]
            if cid in self.member_db:
                self.current_resolving_member = self.member_db[cid].name
                self.current_resolving_member_id = cid

        # Ensure context has source_card_id and player_id for downstream resolution
        context["source_player_id"] = player_id
        if cid != -1:
            context["source_card_id"] = cid

        # Pre-check conditions EXCEPT those that are per-effect (evaluated after earlier effects run)
        per_effect_conditions = {
            ConditionType.HAS_LIVE_CARD,
            ConditionType.COST_CHECK,
            ConditionType.OPPONENT_CHOICE,
            ConditionType.OPPONENT_HAS,
            ConditionType.MODAL_ANSWER,
            # We don't need to blacklist others if we use the "gating" flag
        }

        # Conditions are checked if:
        # 1. They are not "per_effect" (delayed)
        # 2. They are explicitly marked as "gating" (default True for backward comp, but parser sets to False for filters)
        # Note: We treat "gating" defaults as True to be safe for old data, but parser sets False for conditions after Colon.
        pre_check_conditions = [
            c for c in ability.conditions if c.type not in per_effect_conditions and c.params.get("gating", True)
        ]

        if pre_check_conditions:
            # Only filter OUT if we have a target_card_id in context (which we don't here, it's activation)
            # But if a condition in pre_check_conditions fails, we skip activation.
            if not all(self._check_condition(p, cond, context) for cond in pre_check_conditions):
                if self.verbose:
                    print(f"Ability Gated: Condition failed for {p.player_id}")
                return

        if ability.costs:
            areal = context.get("area", -1)
            # Should match _pay_costs signature: (player, costs, source_area)
            if not self._pay_costs(p, ability.costs, source_area=areal):
                if not self.pending_choices:
                    # Failed to pay (e.g. not enough energy) and no choice queued -> Abort
                    return

                # Defer execution for auto-abilities
                abi_key = f"auto-{cid}"
                self.pending_activation = {
                    "ability": ability,
                    "context": {**context, "original_phase": self.phase},
                    "abi_key": abi_key,
                }
                return

        # Prefer the frame program path first. If we cannot resolve a frame
        # program, fall back to semantic compilation rather than stored bytecode.
        frame_program = getattr(ability, "frame_program", None)
        bytecode = []
        if isinstance(frame_program, dict) and frame_program.get("frames"):
            try:
                bytecode = ability_codec.model_to_bytecode(
                    ability_codec.frame_program_to_model(frame_program)
                )
            except Exception:
                bytecode = []
        if not bytecode:
            sparse_frame_index = getattr(ability, "sparse_frame_index", None)
            if isinstance(sparse_frame_index, dict) and sparse_frame_index.get("frames"):
                try:
                    bytecode = ability_codec.model_to_bytecode(
                        ability_codec.frame_program_to_model(sparse_frame_index)
                    )
                except Exception:
                    bytecode = []

        if bytecode:
            self.pending_effects.insert(0, bytecode)
        elif JIT_AVAILABLE and hasattr(self, "fast_mode") and self.fast_mode:
            bytecode = ability.compile()
            self.pending_effects.insert(0, bytecode)
        else:
            total = len(ability.effects)
            for i, phase_effect in enumerate(reversed(ability.effects)):
                step = total - i
                # COPY effect to prevent mutation of shared objects
                eff_copy = copy.copy(phase_effect)
                self.pending_effects.insert(0, ResolvingEffect(eff_copy, cid, step, total))
        while self.pending_effects and not self.pending_choices:
            pass
            self._resolve_pending_effect(0, context=context)

        if self.pending_choices:
            print(f"DEBUG: Pushed choices: {len(self.pending_choices)}")
            pass

        if not self.pending_choices:
            self.current_resolving_ability = None
            self.current_resolving_ability_frame = None
            self.current_resolving_member = None
            self.current_resolving_member_id = -1
            self.looked_cards = []  # Clear transient looked cards

    def _resolve_pending_effect(self, action: int, context: Optional[Dict[str, Any]] = None) -> None:
        resolve_pending_effect(self, action, context)

    def _check_condition(self, player: Any, cond: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        return check_condition(self, player, cond, context)

        """Evaluate a condition quadruple from bytecode."""
        p = self.active_player
        v = seg[1]
        a = seg[2]
        s = seg[3]

        # Decode slot/comparison
        real_slot = s & 0x0F
        comp_val = (s >> 4) & 0x0F
        comp_map = {0: "GE", 1: "LE", 2: "GT", 3: "LT", 4: "EQ"}
        comp = comp_map.get(comp_val, "GE")

        if self.verbose:
            print(f"DEBUG: BC_COND {opcode.name} v={v} a={a} slot={real_slot} comp={comp}")

        if opcode == Opcode.CHECK_COUNT_BLADES:
            val = p.get_total_blades(self.member_db)
        elif opcode == Opcode.CHECK_COUNT_HEARTS:
            hearts = p.get_total_hearts(self.member_db)
            if real_slot == 2:  # Excess
                val = self.excess_hearts_count if hasattr(self, "excess_hearts_count") else 0
            elif 0 <= a < 6:
                val = hearts[a]
            else:
                val = sum(hearts)
        elif opcode == Opcode.CHECK_COUNT_HAND:
            val = len(p.hand)
        elif opcode == Opcode.CHECK_COUNT_DISCARD:
            val = len(p.discard)
        elif opcode == Opcode.CHECK_COUNT_SUCCESS_LIVE:
            val = len(p.success_lives)
        elif opcode == Opcode.CHECK_COUNT_STAGE:
            val = sum(1 for cid in p.stage if cid >= 0)
        elif opcode == Opcode.CHECK_COUNT_ENERGY:
            val = p.count_untapped_energy()
        elif opcode == Opcode.CHECK_MODAL_ANSWER:
            val = self.last_choice_answer if hasattr(self, "last_choice_answer") else 0
        elif opcode == Opcode.CHECK_BATON:
            # Baton Pass logic: Check if the character ID of the card that was in this slot matches target 'v'
            prev_cid = getattr(self, "prev_cid", -1)
            if prev_cid >= 0:
                # Character ID is stored in card stats/db. We assume the compiler mapped the name correctly to a card ID 'v'.
                # For non-JIT, we check if the character name or card ID matches.
                if prev_cid in self.member_db:
                    # Check if the name matches the target card's name (simplest reliable check for SIC)
                    target_card = self.member_db.get(v)
                    if target_card:
                        val = 1 if self.member_db[prev_cid].name == target_card.name else 0
                    else:
                        val = 0
                else:
                    val = 0
            else:
                val = 0
            v = 1  # We set val to 1/0, and check if val == 1 (or >= 1)
        elif opcode == Opcode.CHECK_SCORE_COMPARE:
            # Attr mapping: 0=score, 1=cost, 2=heart, 3=cheer
            # Slot: 0=STAGE, 1=LIVEZONE, 2=EXCESS, but specifically for cost comparisons:
            # center=1, left=0, right=2 (we can reuse real_slot for this)
            opp = self.players[1 - p.player_id]
            if a == 1:  # Cost

                def get_cost(plyr, slot_idx):
                    if slot_idx in [0, 1, 2]:  # Area.LEFT, CENTER, RIGHT
                        cid = plyr.stage[slot_idx]
                        return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                    return sum(self.member_db[cid].cost for cid in plyr.stage if cid >= 0 and cid in self.member_db)

                val = get_cost(p, real_slot)
                # v is usually opponent's value if it's GT/LT vs opponent
                # If v=0 in bytecode, we assume comparison against opponent
                if v == 0:
                    v = get_cost(opp, real_slot)
            elif a == 0:  # Score
                val = sum(self.live_db[cid].score for cid in p.success_lives if cid in self.live_db)
                if v == 0:
                    v = sum(self.live_db[cid].score for cid in opp.success_lives if cid in self.live_db)
            elif a == 2:  # Heart
                hearts = p.get_total_hearts(self.member_db)
                val = sum(hearts)
                if v == 0:
                    o_hearts = opp.get_total_hearts(self.member_db)
                    v = sum(o_hearts)
            else:
                val = 0
        elif opcode == Opcode.CHECK_TURN_1:
            val = 1 if self.turn_number == 1 else 0
            v = 1
        elif opcode == Opcode.CHECK_IS_CENTER:
            val = 1 if context.get("area") == 1 else 0
            v = 1
        elif opcode == Opcode.CHECK_LIFE_LEAD:
            opp = self.players[1 - p.player_id]
            val = 1 if len(p.success_lives) > len(opp.success_lives) else 0
            v = 1
        elif opcode == Opcode.CHECK_OPPONENT_ENERGY_DIFF:
            opp = self.players[1 - p.player_id]
            val = len(opp.energy_zone) - len(p.energy_zone)
        elif opcode == Opcode.CHECK_DECK_REFRESHED:
            val = 1 if p.deck_refreshed_this_turn else 0
            v = 1
        elif opcode == Opcode.CHECK_AREA_CHECK:
            # Check if current execution context is in the specified area (Zone)
            # v: Area ID (0=Left, 1=Center, 2=Right)
            current_area = context.get("area", -1)
            # 3D Secure Verification: Make sure strictly equals
            if current_area == -1:
                return False
            # Normalize to avoid type mismatch
            return int(current_area) == int(v)
        else:
            return True  # Unknown conditions pass by default in this context

        if comp == "GE":
            return val >= v
        elif comp == "LE":
            return val <= v
        elif comp == "GT":
            return val > v
        elif comp == "LT":
            return val < v
        else:
            return val == v

    def _resolve_effect_opcode(self, opcode: Opcode, seg: Any, context: Dict[str, Any]) -> None:
        from engine.game.effects.effect_opcode_resolution import resolve_effect_opcode

        resolve_effect_opcode(self, opcode, seg, context)

    def _handle_choice(self, action: int) -> None:
        handle_choice(self, action)

    def _move_member(self, player: Any, from_idx: int, to_idx: int) -> None:
        move_member(player, from_idx, to_idx)










