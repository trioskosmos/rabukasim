from __future__ import annotations

import random
from typing import Any, Dict, Optional

import numpy as np

from engine.game.effects.choices import queue_target_hand_choice
from engine.game.effects.metadata import _describe_ability
from engine.models.ability import (
    ConditionType,
    Effect,
    EffectType,
    ResolvingEffect,
    TargetType,
)
from engine.models.enums import Group, Unit
from engine.models.opcodes import Opcode


def resolve_condition_opcode(game: Any, opcode: Any, seg: Any, context: Dict[str, Any]) -> bool:
    self = game
    p = self.active_player
    v = seg[1]
    a = seg[2]
    s = seg[3]

    real_slot = s & 0x0F
    comp_val = (s >> 4) & 0x0F
    comp_map = {0: "GE", 1: "LE", 2: "GT", 3: "LT", 4: "EQ"}
    comp = comp_map.get(comp_val, "GE")

    def compare(val: int, target: int) -> bool:
        if comp == "GE":
            return val >= target
        if comp == "LE":
            return val <= target
        if comp == "GT":
            return val > target
        if comp == "LT":
            return val < target
        return val == target

    name = getattr(opcode, "name", str(opcode))

    if name == "CHECK_COUNT_BLADES":
        val = p.get_total_blades(self.member_db)
    elif name == "CHECK_COUNT_HEARTS":
        hearts = p.get_total_hearts(self.member_db)
        if real_slot == 2:
            val = getattr(self, "excess_hearts_count", 0)
        elif 0 <= a < 6:
            val = hearts[a]
        else:
            val = sum(hearts)
    elif name == "CHECK_COUNT_HAND":
        val = len(p.hand)
    elif name == "CHECK_COUNT_DISCARD":
        val = len(p.discard)
    elif name == "CHECK_COUNT_SUCCESS_LIVE":
        val = len(p.success_lives)
    elif name == "CHECK_COUNT_STAGE":
        val = sum(1 for cid in p.stage if cid >= 0)
    elif name == "CHECK_COUNT_ENERGY":
        val = p.count_untapped_energy()
    elif name == "CHECK_MODAL_ANSWER":
        val = getattr(self, "last_choice_answer", 0)
    elif name == "CHECK_BATON":
        prev_cid = getattr(self, "prev_cid", -1)
        if prev_cid >= 0 and prev_cid in self.member_db:
            target_card = self.member_db.get(v)
            val = 1 if target_card and self.member_db[prev_cid].name == target_card.name else 0
        else:
            val = 0
        v = 1
    elif name == "CHECK_SCORE_COMPARE":
        opp = self.players[1 - p.player_id]
        if a == 1:
            def get_cost(plyr, slot_idx):
                if slot_idx in [0, 1, 2]:
                    cid = plyr.stage[slot_idx]
                    return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                return sum(self.member_db[cid].cost for cid in plyr.stage if cid >= 0 and cid in self.member_db)

            val = get_cost(p, real_slot)
            if v == 0:
                v = get_cost(opp, real_slot)
        elif a == 0:
            val = sum(self.live_db[cid].score for cid in p.success_lives if cid in self.live_db)
            if v == 0:
                v = sum(self.live_db[cid].score for cid in opp.success_lives if cid in self.live_db)
        elif a == 2:
            hearts = p.get_total_hearts(self.member_db)
            val = sum(hearts)
            if v == 0:
                v = sum(opp.get_total_hearts(self.member_db))
        else:
            val = 0
    elif name == "CHECK_TURN_1":
        val = 1 if self.turn_number == 1 else 0
        v = 1
    elif name == "CHECK_IS_CENTER":
        val = 1 if context.get("area") == 1 else 0
        v = 1
    elif name == "CHECK_LIFE_LEAD":
        opp = self.players[1 - p.player_id]
        val = 1 if len(p.success_lives) > len(opp.success_lives) else 0
        v = 1
    elif name == "CHECK_OPPONENT_ENERGY_DIFF":
        opp = self.players[1 - p.player_id]
        val = len(opp.energy_zone) - len(p.energy_zone)
    elif name == "CHECK_DECK_REFRESHED":
        val = 1 if p.deck_refreshed_this_turn else 0
        v = 1
    elif name == "CHECK_AREA_CHECK":
        current_area = context.get("area", -1)
        return int(current_area) == int(v) if current_area != -1 else False
    else:
        return True

    return compare(val, v)


def resolve_pending_effect(game: Any, action: int, context: Optional[Dict[str, Any]] = None) -> None:
    self = game
    if not hasattr(self, "pending_effects") or not self.pending_effects:
        return

    resolving_effect = self.pending_effects.pop(0)

    # Handle bytecode (list of ints) from fast_mode
    if isinstance(resolving_effect, list):
        # Execute all opcodes in the bytecode segment
        # Each instruction is 4 ints: [Opcode, Value, Attr, TargetSlot]
        # Execute opcodes with condition/jump support
        i = 0
        while i < len(resolving_effect):
            op = resolving_effect[i]
            if op == int(Opcode.RETURN):
                break

            negated = False
            base_op = op
            if base_op >= 1000:
                negated = True
                base_op -= 1000

            if 200 <= base_op < 300:
                # Condition Opcode
                met = resolve_condition_opcode(self, Opcode(base_op), resolving_effect[i : i + 4], context)
                if self.verbose:
                    print(f"DEBUG: Bytecode Condition {Opcode(base_op).name} Met={met} Negated={negated}")
                if negated:
                    met = not met
                if not met:
                    if self.verbose:
                        print("DEBUG: Condition failed, breaking bytecode segment")
                    if hasattr(self, "log_rule"):
                        self.log_rule("Effect", "Requirement not met. Skipping remaining effects.")
                    break  # Stop current segment
            elif base_op == 30:  # Opcode.SELECT_MODE
                # Handle Bytecode Branching
                # Layout: [30, NumOptions, 0, 0] followed by NumOptions * [JUMP, Offset, 0, 0]
                num_options = resolving_effect[i + 1]
                branch_bytecodes = []

                # Offsets are relative to the JUMP instruction
                # Jump table starts at i + 4
                current_base = i + 4

                # We need to compute start/end for each branch
                # Start of branch K = JumpTable[K] location + Offset

                starts = []
                for k in range(num_options):
                    jump_instr_idx = current_base + (k * 4)
                    offset = resolving_effect[jump_instr_idx + 1]
                    # Target IP = (jump_instr_idx / 4) + offset
                    # Convert to array index:
                    target_idx = jump_instr_idx + (offset * 4)
                    starts.append(target_idx)

                # End of branch K is implicitly Start of K+1, or End of Block
                # NOTE: This assumes branches are contiguous and ordered, which Ability.compile() does.
                end_of_block = len(resolving_effect)

                for k in range(num_options):
                    start = starts[k]
                    end = starts[k + 1] if k < num_options - 1 else end_of_block
                    # Slice bytecode
                    branch_code = resolving_effect[start:end]
                    branch_bytecodes.append(branch_code)

                # Default text for "Choose Player" if detected
                options_text = ["Option " + str(k + 1) for k in range(num_options)]

                # Push choice with bytecode options
                self.pending_choices.append(
                    (
                        "SELECT_MODE",
                        {
                            **(context or {}),
                            "options": options_text,
                            "options_bytecode": branch_bytecodes,
                            "effect_description": "驕ｸ謚槭＠縺ｦ縺上□縺輔＞",
                        },
                    )
                )
                return  # Stop this block, wait for choice
            else:
                self._resolve_effect_opcode(
                    Opcode(base_op), resolving_effect[i : i + 4], context or {}
                )  # Use context

            i += 4
        return

    # Handle unwrapping if it's a ResolvingEffect wrapper (Rule 1.3: Wrapper handling)
    if hasattr(resolving_effect, "effect"):
        effect = resolving_effect.effect
        source_id = resolving_effect.source_card_id
        step_progress = f"{resolving_effect.step_index}/{resolving_effect.total_steps}"
    else:
        # Legacy/Testing support for raw Effect objects
        effect = resolving_effect
        source_id = -1
        step_progress = "?"

    ctx = context or {}
    p = self.players[ctx.get("source_player_id", self.current_player)]

    # Dynamic Value Resolution
    if effect.value_cond != ConditionType.NONE:
        if effect.value_cond == ConditionType.COUNT_STAGE:
            effect.value = len([c for c in p.stage if c >= 0])
        elif effect.value_cond == ConditionType.COUNT_HAND:
            effect.value = len(p.hand)
        elif effect.value_cond == ConditionType.COUNT_DISCARD:
            effect.value = len(p.discard)
        elif effect.value_cond == ConditionType.COUNT_ENERGY:
            effect.value = len(p.energy_zone)
        elif effect.value_cond == ConditionType.COUNT_SUCCESS_LIVE:
            effect.value = len(p.success_lives)
        elif effect.value_cond == ConditionType.COUNT_LIVE_ZONE:
            effect.value = len(p.live_zone)
    opp_idx = 1 - p.player_id

    # Inject source metadata into context for downstream choices
    source_name = self.current_resolving_member or "Unknown"
    source_img = ""
    if source_id != -1:
        if source_id in self.member_db:
            source_name = self.member_db[source_id].name
            source_img = self.member_db[source_id].img_path
        elif source_id in self.live_db:
            source_name = self.live_db[source_id].name
            source_img = self.live_db[source_id].img_path

    target_player_id = opp_idx if effect.target == TargetType.OPPONENT else p.player_id
    target_p = self.players[target_player_id]

    choice_metadata = {
        "player_id": p.player_id,
        "target_player_id": target_player_id,
        "source_card_id": source_id,
        "source_img": source_img,
        "step_progress": step_progress,
        "source_member": source_name,
        "source_ability": _describe_ability(self.current_resolving_ability) if self.current_resolving_ability else "",
    }

    if hasattr(self, "log_rule"):
        # Enhanced Logging
        source_name = "Unknown Source"
        if source_id != -1:
            if source_id in self.member_db:
                source_name = self.member_db[source_id].name
            elif source_id in self.live_db:
                source_name = self.live_db[source_id].name
        elif self.current_resolving_member:
            source_name = self.current_resolving_member

        ability_text = ""
        if self.current_resolving_ability:
            ability_preview = _describe_ability(self.current_resolving_ability)
            ability_text = f" [{ability_preview[:20]}...]"

        msg = f"{source_name}: Resolving {effect.effect_type.name}{ability_text} (Val: {effect.value})"
        self.log_rule("Rule 9.7", msg)

    # --- REPLACEMENT EFFECTS (Rule 9.8) ---
    indices_to_remove = []
    replaced = False
    for i, ce in enumerate(p.continuous_effects):
        ce_eff = ce["effect"]
        if ce_eff.effect_type == EffectType.REPLACE_EFFECT:
            targets_type = ce_eff.params.get("replaces")
            if targets_type == effect.effect_type.name:
                if self.verbose:
                    print(f"Effect {effect.effect_type.name} replaced by {ce_eff.raw_text}")

                if "modifier" in ce_eff.params:
                    mod = ce_eff.params["modifier"]
                    if mod == "double":
                        effect.value *= 2
                    elif mod == "add":
                        effect.value += ce_eff.params.get("value", 0)
                    elif mod == "prevent":
                        replaced = True

                elif "new_effect_type" in ce_eff.params:
                    new_eff_type = EffectType[ce_eff.params["new_effect_type"]]
                    new_val = ce_eff.params.get("new_value", 0)
                    new_eff = Effect(new_eff_type, new_val, TargetType.SELF, ce_eff.params.get("new_params", {}))
                    # Rule 9.8.1: Replacement effect inherits source or uses CE source
                    eff_src = ce.get("source_card_id", source_id)
                    self.pending_effects.insert(0, ResolvingEffect(new_eff, eff_src, 1, 1))
                    replaced = True

                if ce.get("expiry") == "ONE_SHOT":
                    indices_to_remove.append(i)

                if replaced:
                    break

    for i in sorted(indices_to_remove, reverse=True):
        p.continuous_effects.pop(i)

    if replaced:
        return

    if p.negate_next_effect:
        p.negate_next_effect = False
        if self.verbose:
            print(f"Effect: Effect {effect.effect_type} negated by current effect mitigation.")
        return

    # --- SPECIALIZED RECOVERY HANDLERS (Must be before generic TargetType checks) ---
    if effect.effect_type == EffectType.RECOVER_LIVE:
        if self.verbose:
            print(f"DEBUG: RECOVER_LIVE - Player {p.player_id} Discard: {p.discard}")
            print(f"DEBUG: RECOVER_LIVE - Live DB Keys count: {len(self.live_db)}")
        live_cards_in_discard = [cid for cid in p.discard if int(cid) in self.live_db]
        if self.verbose:
            print(f"DEBUG: RECOVER_LIVE - Found: {live_cards_in_discard}")

        group_filter = effect.params.get("group")
        if group_filter:
            # Convert string to Group/Unit enum
            target_group = Group.from_japanese_name(group_filter)
            target_unit = Unit.from_japanese_name(group_filter)

            filtered_live_cards = []
            for cid in live_cards_in_discard:
                card = self.live_db.get(int(cid))
                if not card:
                    continue

                card_groups = getattr(card, "groups", [])
                card_units = getattr(card, "units", [])

                match_group = target_group != Group.OTHER and target_group in card_groups
                match_unit = target_unit != Unit.OTHER and target_unit in card_units

                if match_group or match_unit:
                    filtered_live_cards.append(cid)
            live_cards_in_discard = filtered_live_cards

        if live_cards_in_discard:
            self.pending_choices.append(
                (
                    "SELECT_FROM_DISCARD",
                    {
                        **choice_metadata,
                        "cards": live_cards_in_discard,
                        "count": effect.value,
                        "filter": "live",
                        "effect": "return_to_hand",
                        "effect_description": "蝗槫庶縺吶ｋ繝ｩ繧､繝悶ｒ驕ｸ繧薙〒縺上□縺輔＞",
                    },
                )
            )
        return

    elif effect.effect_type == EffectType.RECOVER_MEMBER:
        member_cards_in_discard = [cid for cid in p.discard if int(cid) in self.member_db]
        group_filter = effect.params.get("group")
        if group_filter:
            target_group = Group.from_japanese_name(group_filter)
            target_unit = Unit.from_japanese_name(group_filter)

            filtered_member_cards = []
            for cid in member_cards_in_discard:
                card = self.member_db.get(int(cid))
                if not card:
                    continue

                card_groups = getattr(card, "groups", [])
                card_units = getattr(card, "units", [])

                match_group = target_group != Group.OTHER and target_group in card_groups
                match_unit = target_unit != Unit.OTHER and target_unit in card_units

                if match_group or match_unit:
                    filtered_member_cards.append(cid)
            member_cards_in_discard = filtered_member_cards

        cost_max = effect.params.get("cost_max")
        if cost_max is not None:
            member_cards_in_discard = [
                cid for cid in member_cards_in_discard if self.member_db[cid].cost <= cost_max
            ]

        if member_cards_in_discard:
            self.pending_choices.append(
                (
                    "SELECT_FROM_DISCARD",
                    {
                        **choice_metadata,
                        "cards": member_cards_in_discard,
                        "count": effect.value,
                        "filter": "member",
                        "effect": effect.params.get("to", "return_to_hand"),
                        "effect_description": "蝗槫庶縺吶ｋ繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                    },
                )
            )
        return

    if effect.effect_type == EffectType.COLOR_SELECT:
        self.pending_choices.append(
            (
                "COLOR_SELECT",
                {
                    **choice_metadata,
                    "choices": effect.params.get("choices", ["pink", "red", "yellow", "green", "blue", "purple"]),
                    "count": effect.value,
                    "effect_description": "濶ｲ繧帝∈繧薙〒縺上□縺輔＞",
                },
            )
        )
        return

    elif effect.effect_type == EffectType.ACTIVATE_MEMBER:
        if effect.params.get("target") == "energy":
            # Filter for tapped energy
            tapped_indices = [i for i, tapped in enumerate(p.tapped_energy) if tapped and i < len(p.energy_zone)]
            tapped_cards = [p.energy_zone[i] for i in tapped_indices]

            if not tapped_cards:
                return

            # If we need to choose X, and we have enough or fewer, we might just untap them?
            # But usually "Choose 1" implies choice. Though if count >= available, auto-pick?
            # Game usually forces manual choice for "Choose".
            # However, for energy, they are often identical unless different cards.
            # Let's use SELECT_FROM_LIST

            self.pending_choices.append(
                (
                    "SELECT_FROM_LIST",
                    {
                        **choice_metadata,
                        "cards": tapped_cards,
                        "count": effect.value,
                        "reason": "activate_energy",
                        "effect_description": f"豢ｻ蜍輔＆縺帙ｋ繧ｨ繝ｼ繝ｫ繧畜{effect.value}譫夐∈繧薙〒縺上□縺輔＞",
                    },
                )
            )
            return

        if effect.params.get("all") or effect.params.get("target") == "all":
            p.tapped_members[:] = False
            return

        if effect.target == TargetType.MEMBER_SELF:
            area = ctx.get("area", -1)
            if area >= 0:
                p.tapped_members[area] = False
        else:
            self.pending_choices.append(
                (
                    "TARGET_MEMBER",
                    {
                        **choice_metadata,
                        "effect": "activate",
                        "effect_description": "豢ｻ蜍輔＆縺帙ｋ繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                        "is_optional": effect.is_optional,
                    },
                )
            )
        return

    if effect.effect_type == EffectType.MOVE_TO_DISCARD and effect.target == TargetType.CARD_HAND:
        if len(p.hand) > 0:
            queue_target_hand_choice(
                self,
                choice_metadata,
                "discard",
                "謇区惆縺九ｉ謐ｨ縺ｦ繧九き繝ｼ繝峨ｒ驕ｸ繧薙〒縺上□縺輔＞",
                effect.params,
            )
        return

    if effect.target == TargetType.CARD_HAND and effect.effect_type != EffectType.SWAP_CARDS:
        if len(p.hand) > 0:
            queue_target_hand_choice(
                self,
                choice_metadata,
                "select",
                "謇区惆縺九ｉ繧ｫ繝ｼ繝峨ｒ驕ｸ繧薙〒縺上□縺輔＞",
                effect.params,
            )
        return
    elif effect.target == TargetType.MEMBER_SELECT:
        if any(cid >= 0 for cid in p.stage):
            self.pending_choices.append(
                (
                    "TARGET_MEMBER",
                    {
                        **choice_metadata,
                        "effect": "buff",
                        "target_effect": effect,
                        "effect_description": f"{effect.effect_type.name}縺ｮ蟇ｾ雎｡繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                        "is_optional": False,
                    },
                )
            )
        return

    if effect.effect_type == EffectType.SELECT_MODE:
        options = effect.modal_options or effect.params.get("options", [])
        self.pending_choices.append(
            (
                "SELECT_MODE",
                {
                    **choice_metadata,
                    "options": options,
                    "effect_description": "莉･荳九°繧・縺､驕ｸ繧薙〒縺上□縺輔＞",
                    "is_optional": False,
                },
            )
        )
        return
    elif effect.effect_type == EffectType.COLOR_SELECT:
        self.pending_choices.append(
            (
                "COLOR_SELECT",
                {
                    **choice_metadata,
                    "effect_description": "繝上・繝医・濶ｲ繧帝∈繧薙〒縺上□縺輔＞",
                    "is_optional": False,
                },
            )
        )
        return

    if effect.effect_type == EffectType.REVEAL_CARDS:
        count = effect.value
        if effect.params.get("per_member_all"):
            count = int(np.sum(p.stage >= 0)) + int(np.sum(self.inactive_player.stage >= 0))

        source = effect.params.get("from", "deck")
        if source == "deck":
            self.looked_cards = []
            for _ in range(count):
                if p.main_deck:
                    self.looked_cards.append(p.main_deck.pop(0))
        return

    if effect.effect_type == EffectType.CHEER_REVEAL:
        if p.main_deck:
            card = p.main_deck.pop(0)
            self.looked_cards = [card]
        return

    if effect.target == TargetType.MEMBER_NAMED:
        name = effect.params.get("target_name", "")
        found_slot = -1
        for i, cid in enumerate(p.stage):
            if cid >= 0 and cid in self.member_db:
                if name in self.member_db[cid].name:
                    found_slot = i
                    break
        if found_slot >= 0:
            ctx = ctx.copy() if ctx else {}
            ctx["area"] = found_slot
            target_for_logic = TargetType.MEMBER_SELF
        else:
            return
    else:
        target_for_logic = effect.target

    if effect.effect_type == EffectType.DRAW:
        should_draw = True
        draw_count = effect.value

        if effect.params.get("condition") == "has_live_in_looked":
            # Nozomi Logic: Check if looked_cards contains a live card
            has_live = any(cid in self.live_db for cid in self.looked_cards)
            should_draw = has_live

        if effect.params.get("multiplier") == "energy":
            req = effect.params.get("req_per_unit", 1)
            count = len(p.energy_zone)
            draw_count = count // req if req > 0 else 0
        elif "per_energy" in effect.params:
            # Kanon Logic (Liella Starter 001)
            req = effect.params.get("per_energy", 1)
            count = len(p.energy_zone)
            # Scaling: (count // req) * base_value
            draw_count = (count // req) * effect.value if req > 0 else effect.value

        if should_draw and draw_count > 0:
            self._draw_cards(p, draw_count)

    elif effect.effect_type == EffectType.GRANT_ABILITY:
        # Sumire Logic (Liella Starter 004)
        # Grants constant Score +1 until end of turn.
        source_id = source_id if source_id != -1 else ctx.get("source_card_id", -1)
        p.continuous_effects.append(
            {
                "source_card_id": source_id,
                "effect": Effect(EffectType.BOOST_SCORE, effect.value, TargetType.SELF),
                "expiry": "TURN_END",
            }
        )

    elif effect.effect_type == EffectType.TAP_OPPONENT:
        opp = self.inactive_player
        if any(cid >= 0 for cid in opp.stage):
            if effect.params.get("target") == "all":
                cost_max = effect.params.get("cost_max", 999)
                for i, cid in enumerate(opp.stage):
                    if cid >= 0:
                        card = self.member_db[cid]
                        if card.cost <= cost_max:
                            opp.tapped_members[i] = True
                return

            # Detect "Opponent chooses" logic (e.g., Nico)
            is_opponent_choice = (
                self.current_resolving_ability and "逶ｸ謇九・" in self.current_resolving_ability.raw_text
            )

            if is_opponent_choice:
                # Opponent chooses their own member to tap
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **choice_metadata,
                            "player_id": self.inactive_player.player_id,
                            "effect": "tap_self_chosen",
                            "effect_description": "繧ｦ繧ｧ繧､繝医↓縺吶ｋ閾ｪ蛻・・繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                            "is_optional": False,
                        },
                    )
                )
            else:
                self.pending_choices.append(
                    (
                        "TARGET_OPPONENT_MEMBER",
                        {
                            **choice_metadata,
                            "effect": "tap",
                            "effect_description": "逶ｸ謇九・繝｡繝ｳ繝舌・繧帝∈繧薙〒繧ｿ繝・・縺励※縺上□縺輔＞",
                            "is_optional": False,
                        },
                    )
                )

    elif effect.effect_type == EffectType.MOVE_TO_DECK:
        pos = effect.params.get("position", "top")
        to_energy = effect.params.get("to_energy_zone", False) or effect.params.get(
            "to_energy_deck", False
        )  # Ambiguous in some parses
        source = effect.params.get("from", "discard")

        # Extract card from source
        card = None
        if source == "discard" and p.discard:
            card = p.discard.pop()
        elif source == "energy_deck" and p.energy_deck:
            card = p.energy_deck.pop(0)  # Energy deck is usually top-card
        elif source == "hand" and p.hand:
            # Should have a choice, but if automatic (e.g. random or top), just pop
            card = p.hand.pop(0)

        if card is not None:
            if to_energy:
                p.energy_zone.append(card)
                p.tapped_energy[len(p.energy_zone) - 1] = effect.params.get(
                    "rest", True
                )  # Default rested for Liella
            else:
                target_deck = p.main_deck
                if pos == "top":
                    target_deck.insert(0, card)
                else:
                    target_deck.append(card)

    elif effect.effect_type == EffectType.MOVE_MEMBER:
        self.pending_choices.append(
            (
                "TARGET_MEMBER_SLOT",
                {
                    **choice_metadata,
                    "reason": "position_change",
                    "count": 1,
                    "effect_description": "遘ｻ蜍輔☆繧九Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                },
            )
        )
        self.pending_choices.append(
            (
                "TARGET_MEMBER_SLOT",
                {
                    **choice_metadata,
                    "reason": "position_change",
                    "count": 1,
                    "effect_description": "遘ｻ蜍募・繧帝∈繧薙〒縺上□縺輔＞",
                },
            )
        )

    elif effect.effect_type == EffectType.SWAP_ZONE:
        live_cards = p.success_lives
        if not live_cards or not p.hand:
            return
        self.pending_choices.append(
            (
                "SELECT_SWAP_SOURCE",
                {
                    **choice_metadata,
                    "cards": live_cards.copy(),
                    "source": "success_live",
                    "effect_description": "莠､謠帙↓蜃ｺ縺吶Λ繧､繝悶ｒ驕ｸ繧薙〒縺上□縺輔＞",
                },
            )
        )

    elif effect.effect_type == EffectType.DRAW:
        self._draw_cards(p, effect.value)

    elif effect.effect_type == EffectType.ADD_BLADES:
        val = effect.value
        if effect.params.get("multiplier"):
            if effect.params.get("per_live"):
                val *= len(p.success_lives)
            elif effect.params.get("per_energy"):
                val *= len(p.energy_zone)
            elif effect.params.get("per_member"):
                val *= int(np.sum(p.stage >= 0))
        p.continuous_effects.append(
            {
                "effect": Effect(EffectType.ADD_BLADES, val, effect.target, effect.params),
                "target_slot": ctx.get("area", -1) if target_for_logic == TargetType.MEMBER_SELF else -1,
                "expiry": effect.params.get("until", "turn_end").upper(),
            }
        )
    elif effect.effect_type == EffectType.RESTRICTION:
        r_type = str(effect.params.get("type", "unknown")).lower()
        if r_type == "live":
            p.cannot_live = True
        else:
            p.restrictions.add(r_type)
        p.continuous_effects.append(
            {
                "effect": Effect(EffectType.RESTRICTION, 0, TargetType.SELF, {"type": r_type}),
                "expiry": effect.params.get("until", "turn_end").upper(),
            }
        )

    elif effect.effect_type == EffectType.MODIFY_SCORE_RULE:
        p.continuous_effects.append({"effect": effect, "expiry": effect.params.get("until", "turn_end").upper()})

    elif effect.effect_type == EffectType.LOOK_DECK:
        # Rule 10.2: Refresh if needed before looking
        if not target_p.main_deck:
            self._resolve_deck_refresh(target_p)

        count = min(effect.value, len(target_p.main_deck))
        print(
            f"DEBUG: Executing LOOK_DECK count={count} deck={len(target_p.main_deck)} value={effect.value} target={target_player_id}"
        )
        self.looked_cards = []
        for _ in range(count):
            if target_p.main_deck:
                self.looked_cards.append(target_p.main_deck.pop(0))

    elif effect.effect_type == EffectType.LOOK_AND_CHOOSE:
        # Logic Update: If looked_cards is empty, check if we need to look first (Atomic Look & Choose)
        look_count = effect.params.get("look_count", 0)
        target_player_id = effect.params.get("target_player_id", self.current_player)
        # Default to active player if not specified
        target_p = self.players[target_player_id] if target_player_id in (0, 1) else self.active_player

        if not self.looked_cards and look_count > 0:
            print(f"DEBUG: Atomic LOOK_AND_CHOOSE executing look for {look_count} cards.")
            for _ in range(look_count):
                if target_p.main_deck:
                    self.looked_cards.append(target_p.main_deck.pop(0))

        print(f"DEBUG: LOOK_AND_CHOOSE. looked_cards={self.looked_cards}")
        if self.looked_cards:
            # If count is 0, just discard everything (Mill logic)
            count = effect.params.get("count", effect.value)
            if count <= 0:
                self.active_player.discard.extend(self.looked_cards)
                self.looked_cards = []
            else:
                valid_cards = self.looked_cards.copy()

                # Apply Group/Unit Filter from params (e.g. "縺ｿ繧峨￥繧峨・繝ｼ縺擾ｼ・)
                group_filter = effect.params.get("group")
                if group_filter:
                    target_group = Group.from_japanese_name(group_filter)
                    target_unit = Unit.from_japanese_name(group_filter)
                    filtered_by_group = []
                    for cid in valid_cards:
                        card = self.member_db.get(cid) or self.live_db.get(cid)
                        if not card:
                            continue
                        # Check if card matches EITHER the Group OR the Unit
                        # (some filters might be Series, others might be Units)
                        # Also safely handle missing attributes
                        card_groups = getattr(card, "groups", [])
                        card_units = getattr(card, "units", [])

                        # Note: Group.from_japanese_name returns OTHER (99) if not found.
                        # Unit.from_japanese_name returns OTHER or similar fallback.
                        # We check if the target is actually present.
                        match_group = target_group != Group.OTHER and target_group in card_groups
                        match_unit = target_unit != Unit.OTHER and target_unit in card_units

                        # Special case: If the string specifically parses to OTHER (not found),
                        # we might want to fail? But current logic returns OTHER.
                        # If "縺ｿ繧峨￥繧峨・繝ｼ縺・ -> Unit.MIRA_CRA_PARK (15), Group.OTHER (99).
                        # So match_unit will be True.

                        if match_group or match_unit:
                            filtered_by_group.append(cid)
                    valid_cards = filtered_by_group
                # Filter if ability has conditions acting as choice filters
                if self.current_resolving_ability and self.current_resolving_ability.conditions:
                    filtered = []
                    for cid in valid_cards:
                        # Context for filtering
                        filter_ctx = {**choice_metadata, "target_card_id": int(cid), "check_candidate": True}
                        # Only check conditions that are relevant to filtering?
                        # For now, check all. If activation conditions (like Turn 1) are present,
                        # they usually don't depend on "target_card_id" and should remain True if already met.
                        if all(
                            self._check_condition(p, c, filter_ctx)
                            for c in self.current_resolving_ability.conditions
                        ):
                            filtered.append(cid)
                    valid_cards = filtered

                # Determine the effect based on destination
                dest = effect.params.get("destination", "hand")
                any_number = effect.params.get("any_number", False)
                effect.params.get("reorder", False)

                reason = "look_and_choose"
                desc = "Choose a card to put into your hand"

                if dest == "deck_top":
                    reason = "look_and_reorder"
                    if any_number:
                        desc = "Choose any number of cards from the top of the deck"
                    else:
                        desc = "Choose a card from the top of the deck"

                self.pending_choices.append(
                    (
                        "SELECT_FROM_LIST",
                        {
                            **choice_metadata,
                            "cards": valid_cards,
                            "reason": reason,
                            "effect_description": desc,
                            "is_optional": any_number,  # "any number" implies optional
                            **effect.params,
                        },
                    )
                )

    elif effect.effect_type == EffectType.SWAP_CARDS:
        count = effect.value
        source = effect.params.get("from", "hand")
        target = effect.params.get("target", "discard")
        effect.params.get("draw_on_discard", True)

        if source == "deck" and target == "discard":
            # Direct mill from deck to discard (e.g., Nozomi SD1-007, Hanayo SD1-008)
            milled = []
            for _ in range(count):
                if p.main_deck:
                    card = p.main_deck.pop(0)
                    p.discard.append(card)
                    milled.append(card)
            # Store milled cards for conditional effects (e.g., "if Live card was milled")
            self.looked_cards = milled
        elif target == "discard":
            # Discard from hand (requires user selection)
            params = {**choice_metadata, "count": effect.value, "is_optional": effect.is_optional, **effect.params}
            if "draw_on_discard" not in params:
                if effect.effect_type == EffectType.SWAP_CARDS:
                    params["draw_on_discard"] = True
                    params["total_count"] = effect.value

                self.pending_choices.append(
                    (
                        "DISCARD_SELECT",
                        params,
                    )
                )

    elif effect.effect_type == EffectType.TAP_MEMBER:
        # Tap self or another member
        if effect.target == TargetType.MEMBER_SELF:
            p.tapped_members[self.current_resolving_member_id] = True
        elif effect.target == TargetType.MEMBER_OTHER:
            # This usually requires a choice if not specified, but for simple parsing
            # we might just tap the resolving member if target is ambiguous
            if self.current_resolving_member_id >= 0:
                p.tapped_members[self.current_resolving_member_id] = True
        elif effect.target == TargetType.MEMBER_SELECT:
            # Generate choice
            self.pending_choices.append(
                (
                    "MEMBER_SELECT",
                    {
                        **choice_metadata,
                        "effect": "tap",
                        "effect_description": "繧ｿ繝・・縺吶ｋ繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                        "is_optional": effect.is_optional,
                    },
                )
            )

    elif effect.effect_type == EffectType.ADD_HEARTS:
        val = effect.value
        if effect.params.get("multiplier"):
            if effect.params.get("per_live"):
                val *= len(p.success_lives)
            elif effect.params.get("per_energy"):
                val *= len(p.energy_zone)
            elif effect.params.get("per_member"):
                val *= int(np.sum(p.stage >= 0))
        p.continuous_effects.append(
            {
                "effect": Effect(EffectType.ADD_HEARTS, val, effect.target, effect.params),
                "target_slot": ctx.get("area", -1) if target_for_logic == TargetType.MEMBER_SELF else -1,
                "expiry": effect.params.get("until", "turn_end").upper(),
            }
        )

    elif effect.effect_type == EffectType.BUFF_POWER:
        val = effect.value
        if effect.params.get("multiplier"):
            if effect.params.get("per_live"):
                val *= len(p.success_lives)
            elif effect.params.get("per_energy"):
                val *= len(p.energy_zone)
            elif effect.params.get("per_member"):
                val *= int(np.sum(p.stage >= 0))

        p.continuous_effects.append(
            {
                "effect": Effect(EffectType.ADD_BLADES, val, target_for_logic, effect.params),
                "target_slot": ctx.get("area", -1) if target_for_logic == TargetType.MEMBER_SELF else -1,
                "expiry": effect.params.get("until", "turn_end").upper(),
            }
        )

    elif effect.effect_type == EffectType.BOOST_SCORE:
        final_val = effect.value
        if effect.params.get("per_live_in_looked"):
            final_val = sum(1 for cid in self.looked_cards if cid in self.live_db)

        for ce in p.continuous_effects:
            if (
                ce["effect"].effect_type == EffectType.REPLACE_EFFECT
                and ce["effect"].params.get("replaces") == "score_boost"
            ):
                final_val = ce["effect"].value
                break
        p.live_score_bonus += int(final_val)
        if effect.params.get("until"):
            p.continuous_effects.append(
                {
                    "effect": Effect(EffectType.BOOST_SCORE, int(final_val), effect.target, effect.params),
                    "expiry": effect.params.get("until").upper(),
                }
            )

    elif effect.effect_type == EffectType.REPLACE_EFFECT:
        p.continuous_effects.append({"effect": effect, "expiry": effect.params.get("until", "live_end").upper()})

    elif effect.effect_type == EffectType.SET_SCORE:
        p.live_score_bonus = effect.value
        ctx["set_score_override"] = effect.value

    elif effect.effect_type == EffectType.BATON_TOUCH_MOD:
        p.baton_touch_limit = effect.value

    elif effect.effect_type == EffectType.REDUCE_COST:
        p.continuous_effects.append({"effect": effect, "expiry": effect.params.get("until", "turn_end").upper()})

    elif effect.effect_type == EffectType.REDUCE_HEART_REQ:
        p.continuous_effects.append({"effect": effect, "expiry": effect.params.get("until", "live_end").upper()})

    elif effect.effect_type == EffectType.NEGATE_EFFECT:
        self.inactive_player.negate_next_effect = True

    elif effect.effect_type == EffectType.IMMUNITY:
        p.restrictions.add("immunity")

    elif effect.effect_type == EffectType.RECOVER_LIVE:
        live_in_discard = [cid for cid in p.discard if cid in self.live_db]
        if live_in_discard:
            self.pending_choices.append(
                (
                    "SELECT_FROM_DISCARD",
                    {
                        **choice_metadata,
                        "cards": live_in_discard,
                        "count": effect.value,
                        "effect_description": "謗ｧ縺亥ｮ､縺九ｉ謇区惆縺ｫ蜉縺医ｋ繝ｩ繧､繝悶き繝ｼ繝峨ｒ驕ｸ繧薙〒縺上□縺輔＞",
                        "destination": "hand",
                    },
                )
            )

    elif effect.effect_type == EffectType.RECOVER_MEMBER:
        members_in_discard = [cid for cid in p.discard if cid in self.member_db]
        if members_in_discard:
            self.pending_choices.append(
                (
                    "SELECT_FROM_DISCARD",
                    {
                        **choice_metadata,
                        "cards": members_in_discard,
                        "count": effect.value,
                        "effect_description": "謗ｧ縺亥ｮ､縺九ｉ謇区惆縺ｫ蜉縺医ｋ繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                        "destination": "hand",
                    },
                )
            )

    elif effect.effect_type == EffectType.SWAP_CARDS:
        targets = [p]
        if effect.params.get("both_players"):
            targets = self.players

        for tp in targets:
            if effect.params.get("target") == "discard":
                # Simple discard
                self.pending_choices.append(
                    (
                        "TARGET_HAND",
                        {
                            **choice_metadata,
                            "player_id": tp.player_id,
                            "effect": "discard",
                            "count": effect.value,
                            "effect_description": f"謗ｧ縺亥ｮ､縺ｫ鄂ｮ縺乗焔譛ｭ繧畜{effect.value}譫夐∈繧薙〒縺上□縺輔＞",
                            **effect.params,
                        },
                    )
                )
            else:
                # Generic swap (discard X, draw X)
                # For now just handle the draw part after discard if needed
                # But LL-PR-004-PR uses it for discard.
                pass

    elif effect.effect_type == EffectType.ADD_TO_HAND:
        if effect.params.get("from") == "discard":
            # Check for specific filters
            candidates = p.discard
            if effect.params.get("filter") == "member":
                candidates = [cid for cid in p.discard if cid in self.member_db]
            elif effect.params.get("filter") == "live":
                candidates = [cid for cid in p.discard if cid in self.live_db]

            if candidates:
                self.pending_choices.append(
                    (
                        "SELECT_FROM_DISCARD",
                        {
                            **choice_metadata,
                            "cards": candidates,
                            "count": effect.value,
                            "effect_description": "謗ｧ縺亥ｮ､縺九ｉ謇区惆縺ｫ蜉縺医ｋ繧ｫ繝ｼ繝峨ｒ驕ｸ繧薙〒縺上□縺輔＞",
                            "destination": "hand",
                            "filter": effect.params.get("filter", "all"),
                        },
                    )
                )
            else:
                # No candidates, ability fizzles or does nothing
                pass
        elif effect.params.get("from") == "deck":
            self._draw_cards(p, effect.value)

    elif effect.effect_type == EffectType.TRIGGER_REMOTE:
        zone = effect.params.get("from", "discard")
        if zone == "discard":
            members_in_discard = [cid for cid in p.discard if cid in self.member_db]
            if members_in_discard:
                self.pending_choices.append(
                    (
                        "SELECT_FROM_DISCARD",
                        {
                            **choice_metadata,
                            "cards": members_in_discard,
                            "count": 1,
                            "filter": "member_with_ability",
                            "destination": "trigger_ability",
                            "effect_description": "蜉ｹ譫懊ｒ逋ｺ蜍輔☆繧九Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                        },
                    )
                )

    elif effect.effect_type == EffectType.PLAY_MEMBER_FROM_HAND:
        if len(p.hand) > 0:
            self.pending_choices.append(
                (
                    "TARGET_HAND",
                    {
                        **choice_metadata,
                        "effect": "place_member",
                        "effect_description": f"謇区惆縺九ｉ繝｡繝ｳ繝舌・繧畜{effect.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
                        "count": effect.value,
                        **effect.params,
                    },
                )
            )

    elif effect.effect_type == EffectType.ENERGY_CHARGE:
        source = effect.params.get("from", "deck")
        count = effect.value
        if source == "deck" or source == "energy_deck":
            src_list = p.main_deck if source == "deck" else p.energy_deck
            for _ in range(count):
                if not src_list and source == "deck":
                    self._resolve_deck_refresh(p)
                if src_list:
                    p.energy_zone.append(src_list.pop(0))
                    p.tapped_energy[len(p.energy_zone) - 1] = effect.params.get("rest", False)
        elif source == "hand":
            self.pending_choices.append(
                (
                    "TARGET_HAND",
                    {
                        **choice_metadata,
                        "effect": "energy_charge",
                        "count": count,
                        "effect_description": "繧ｨ繝ｼ繝ｫ縺ｫ縺吶ｋ謇区惆繧帝∈繧薙〒縺上□縺輔＞",
                        **effect.params,
                    },
                )
            )

    elif effect.effect_type == EffectType.SET_BLADES:
        # Apply as a continuous effect to the target member (or source if self)
        target_slot = ctx.get("area", -1)  # Usually self for "becomes X"
        if target_slot >= 0:
            p.continuous_effects.append(
                {
                    "effect": effect,
                    "target_slot": target_slot,
                    "expiry": "TURN_END",  # Usually stat changes are turn-based unless specified otherwise
                    "source_card_id": source_id,
                }
            )

    elif effect.effect_type == EffectType.FLAVOR_ACTION:
        # Check if this flavor action is for formation change
        text_param = effect.params.get("text", "")
        if "formation" in text_param.lower():
            # This is a formation change flavor action
            self.pending_choices.append(
                (
                    "CHOOSE_FORMATION",
                    {
                        **choice_metadata,
                        "player_id": opp_idx,
                        "title": text_param if text_param else "Choose formation",
                        "options": [
                            "Choco Mint",
                            "Strawberry Flavor",
                            "Cookies & Cream",
                            "You",
                            "Anything else",
                        ],
                        "reason": "flavor_action_formation",
                    },
                )
            )
        else:
            # Regular flavor action
            self.pending_choices.append(
                (
                    "MODAL_CHOICE",
                    {
                        **choice_metadata,
                        "player_id": opp_idx,
                        "title": "What do you like?",
                        "options": [
                            "Choco Mint",
                            "Strawberry Flavor",
                            "Cookies & Cream",
                            "You",
                            "Anything else",
                        ],
                        "reason": "flavor_action",
                    },
                )
            )

    elif effect.effect_type == EffectType.ORDER_DECK:
        if not p.main_deck:
            self._resolve_deck_refresh(p)
        position = effect.params.get("position", "top")
        shuffle = effect.params.get("shuffle", False)
        count = min(effect.value, len(p.main_deck))
        top_cards = []
        for _ in range(count):
            if p.main_deck:
                top_cards.append(p.main_deck.pop(0))
        if not top_cards:
            return
        if shuffle:
            random.shuffle(top_cards)
            if position == "bottom":
                p.main_deck.extend(top_cards)
            else:
                for c in reversed(top_cards):
                    p.main_deck.insert(0, c)
        else:
            self.pending_choices.append(
                (
                    "SELECT_ORDER",
                    {
                        **choice_metadata,
                        "cards": top_cards,
                        "ordered": [],
                        "position": position,
                        "effect_description": "繧ｫ繝ｼ繝峨・鬆・分繧帝∈繧薙〒縺上□縺輔＞",
                    },
                )
            )

    elif effect.effect_type == EffectType.PLACE_UNDER:
        target_area = ctx.get("area", -1)
        source_zone = effect.params.get("from", "hand")
        if source_zone == "hand" and target_area >= 0:
            self.pending_choices.append(
                (
                    "TARGET_HAND",
                    {
                        **choice_metadata,
                        "effect": "place_under",
                        "target_area": target_area,
                        "count": effect.value,
                        **effect.params,
                    },
                )
            )
        elif source_zone == "energy" and target_area >= 0:
            if p.energy_zone:
                self.pending_choices.append(
                    (
                        "SELECT_FROM_LIST",
                        {
                            **choice_metadata,
                            "cards": p.energy_zone,
                            "count": effect.value,
                            "reason": "place_under_from_energy",
                            "target_area": target_area,
                            "effect_description": f"繝｡繝ｳ繝舌・縺ｮ荳九↓鄂ｮ縺上お繝ｼ繝ｫ繧畜{effect.value}譫夐∈繧薙〒縺上□縺輔＞",
                            **effect.params,
                        },
                    )
                )
            else:
                # No energy to place
                pass

    elif effect.effect_type == EffectType.SEARCH_DECK:
        group = effect.params.get("group")
        cost_max = effect.params.get("cost_max")
        targets = []
        for cid in p.main_deck:
            if cid in self.member_db:
                m = self.member_db[cid]
                if group and Group.from_japanese_name(group) not in m.groups:
                    continue
                if cost_max is not None and m.cost > cost_max:
                    continue
                targets.append(cid)
            elif cid in self.live_db:
                l = self.live_db[cid]
                if group and Group.from_japanese_name(group) not in l.groups:
                    continue
                targets.append(cid)
        if targets:
            self.pending_choices.append(
                (
                    "SELECT_FROM_LIST",
                    {
                        **choice_metadata,
                        "cards": targets,
                        "reason": "search_deck",
                        "shuffle": True,
                        "effect_description": "繝・ャ繧ｭ縺九ｉ蜉縺医ｋ繧ｫ繝ｼ繝峨ｒ驕ｸ繧薙〒縺上□縺輔＞",
                    },
                )
            )
        else:
            random.shuffle(p.main_deck)

    elif effect.effect_type == EffectType.FORMATION_CHANGE:
        members = [(i, cid) for i, cid in enumerate(p.stage) if cid >= 0]
        if members:
            self.pending_choices.append(
                (
                    "SELECT_FORMATION_SLOT",
                    {
                        **choice_metadata,
                        "slot_index": 0,
                        "available_members": members,
                        "new_stage": [-1, -1, -1],
                        "effect_description": "遘ｻ蜍輔☆繧九Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                    },
                )
            )

    elif effect.effect_type == EffectType.TRANSFORM_COLOR:
        # Rule 11.12: Transformation effects.
        # Usually lasts until LIVE_END.
        self.active_player.continuous_effects.append(
            {
                "effect": effect,
                "source_card_id": source_id,
                "expiry": "LIVE_END",
            }
        )



__all__ = ["resolve_pending_effect"]


