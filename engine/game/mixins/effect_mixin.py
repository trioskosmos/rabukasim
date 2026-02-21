import copy
import random
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import numpy as np

if TYPE_CHECKING:
    from engine.models.ability import Ability, Cost, Effect

from engine.game.enums import Phase
from engine.models.ability import (
    Ability,
    AbilityCostType,
    ConditionType,
    Cost,
    Effect,
    EffectType,
    ResolvingEffect,
    TargetType,
    TriggerType,
)
from engine.models.enums import Group, Unit
from engine.models.opcodes import Opcode

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
            rules_applied = True
            while rules_applied:
                rules_applied = False
                for p in self.players:
                    p.meta_rules.clear()
                    # Optimize: Only check cards known to have META_RULE effects
                    for cid in p.stage:
                        if cid >= 0 and cid in self._meta_rule_cards:
                            # Direct lookups for hot path
                            for ab in self.member_db[cid].abilities:
                                if ab.trigger == TriggerType.CONSTANT:
                                    for eff in ab.effects:
                                        if eff.effect_type == EffectType.META_RULE:
                                            p.meta_rules.add(str(eff.params.get("type", "")))
                    for zone in [p.live_zone, p.success_lives]:
                        for cid in zone:
                            if cid in self._meta_rule_cards:
                                for ab in self.live_db[cid].abilities:
                                    if ab.trigger == TriggerType.CONSTANT:
                                        for eff in ab.effects:
                                            if eff.effect_type == EffectType.META_RULE:
                                                p.meta_rules.add(str(eff.params.get("type", "")))
                    if not p.main_deck and p.discard:
                        p.main_deck = p.discard[:]
                        p.discard = []
                        if self.fast_mode:
                            np.random.shuffle(p.main_deck)
                        else:
                            random.shuffle(p.main_deck)
                        rules_applied = True
                    for i in range(3):
                        if p.stage[i] < 0 and p.stage_energy_count[i] > 0:
                            # Rule 10.5.3: Energy in empty member area -> Energy Deck
                            if hasattr(self, "log_rule"):
                                self.log_rule(
                                    "Rule 10.5.3", f"Reclaiming energy from empty slot {i} for player {p.player_id}."
                                )
                            # Inline optimization for clear_stage_energy
                            count = p.stage_energy_count[i]
                            if count > 0:
                                p.energy_deck.extend(p.stage_energy_vec[i, :count])
                                p.stage_energy_vec[i, :] = 0
                                p.stage_energy_count[i] = 0
                                rules_applied = True

                    if self.yell_cards and int(self.phase) not in (Phase.PERFORMANCE_P1, Phase.PERFORMANCE_P2):
                        for cid in self.yell_cards:
                            self.players[self.current_player].discard.append(cid)
                        self.yell_cards = []
                        rules_applied = True
                    old_game_over = self.game_over
                    self.check_win_condition()
                    if self.game_over and not old_game_over:
                        rules_applied = True
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

    def _resolve_source_metadata(
        self, source_card_id: Optional[int], ability: "Ability", reason: str = "effect"
    ) -> Dict[str, Any]:
        """Helper to resolve standardized source metadata for UI/Logs."""
        if source_card_id is None:
            # Fallback if no specific source ID provided
            return {
                "source_card_id": -1,
                "source_img": "",
                "source_member": "Unknown Source",
                "source_ability": ability.raw_text,
                "step_progress": "?",
                "reason": reason,
            }

        # Try member DB
        if source_card_id in self.member_db:
            card = self.member_db[source_card_id]
            return {
                "source_card_id": source_card_id,
                "source_card_no": getattr(card, "card_no", "Unknown"),
                "source_img": getattr(card, "img_path", ""),
                "source_member": card.name,
                "source_ability": ability.raw_text,
                "step_progress": "?",
                "reason": reason,
            }

        # Try live DB
        if source_card_id in self.live_db:
            card = self.live_db[source_card_id]
            return {
                "source_card_id": source_card_id,
                "source_card_no": getattr(card, "card_no", "Unknown"),
                "source_img": getattr(card, "img_path", ""),
                "source_member": card.name,
                "source_ability": ability.raw_text,
                "step_progress": "?",
                "reason": reason,
            }

        return {
            "source_card_id": source_card_id,
            "source_img": "",
            "source_member": f"Card {source_card_id}",
            "source_ability": ability.raw_text,
            "step_progress": "?",
            "reason": reason,
        }

    def _handle_cost(self, player_id: int, ability: Ability, context: Dict[str, Any] = {}) -> bool:
        """Handle ability costs (Rule 9.7.2). Returns True if cost paid/resolved."""
        p = self.players[player_id]
        cid = context.get("source_card_id")

        # Use new helper to ensure consistent metadata
        cost_metadata = self._resolve_source_metadata(cid, ability, reason="cost")
        cost_metadata["step_progress"] = "Cost"

        for cost in ability.costs:
            if cost.cost_type == AbilityCostType.TAP_MEMBER:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0:
                        p.tapped_members[area] = True
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "tap",
                                "effect_description": "タップするメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                    return False  # Cost requires choice, so not fully paid yet
            elif cost.cost_type == AbilityCostType.TAP_SELF:
                area = context.get("area", -1)
                if area >= 0:
                    p.tapped_members[area] = True
            elif cost.cost_type == AbilityCostType.DISCARD_HAND:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "discard",
                                "effect_description": f"手札から{cost.value}枚捨ててください",
                                "is_optional": cost.is_optional,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False  # Cannot pay cost
            elif cost.cost_type == AbilityCostType.TAP_ENERGY:
                tapped_indices = [
                    i for i, tapped in enumerate(p.tapped_energy) if not tapped and i < len(p.energy_zone)
                ]
                untapped_cards = [p.energy_zone[i] for i in tapped_indices]

                if len(untapped_cards) < cost.value:
                    return False  # Not enough untapped energy

                self.pending_choices.append(
                    (
                        "SELECT_FROM_LIST",
                        {
                            **cost_metadata,
                            "cards": untapped_cards,
                            "count": cost.value,
                            "reason": "tap_energy",
                            "effect_description": f"タップするエールを{cost.value}枚選んでください",
                        },
                    )
                )
                return False
            elif cost.cost_type == AbilityCostType.PAY_ENERGY:
                if p.energy_count < cost.value:
                    return False  # Not enough energy
                p.energy_count -= cost.value
            elif cost.cost_type == AbilityCostType.REST_MEMBER:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0:
                        p.rested_members[area] = True
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "rest",
                                "effect_description": "レストするメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_HAND:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0 and p.stage[area] >= 0:
                        p.hand.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.rested_members[area] = False
                        p.stage_energy[area].clear()
                    else:
                        return False
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": "手札に戻すメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.DISCARD_MEMBER:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0 and p.stage[area] >= 0:
                        p.discard.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.rested_members[area] = False
                        p.stage_energy[area].clear()
                    else:
                        return False
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "discard_member",
                                "effect_description": "捨てるメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.DISCARD_LIVE:
                if len(p.live_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_LIVE",
                            {
                                **cost_metadata,
                                "effect": "discard",
                                "effect_description": f"ライブゾーンから{cost.value}枚捨ててください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.REMOVE_LIVE:
                if len(p.live_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_LIVE",
                            {
                                **cost_metadata,
                                "effect": "remove",
                                "effect_description": f"ライブゾーンから{cost.value}枚除外してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.REMOVE_MEMBER:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0 and p.stage[area] >= 0:
                        self.removed_cards.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.rested_members[area] = False
                        p.stage_energy[area].clear()
                    else:
                        return False
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "remove_member",
                                "effect_description": "除外するメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.RETURN_LIVE_TO_HAND:
                if len(p.live_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_LIVE",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"ライブゾーンから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_LIVE_TO_DECK:
                if len(p.live_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_LIVE",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": f"ライブゾーンから{cost.value}枚デッキに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.REVEAL_HAND_ALL:
                # Rule 9.6.2: Reveal all cards in hand.
                if hasattr(self, "log_rule"):
                    from engine.game.state_utils import get_base_id

                    hand_nos = []
                    for cid in p.hand:
                        bid = get_base_id(cid)
                        c = self.member_db.get(bid) or self.live_db.get(bid)
                        hand_nos.append(f"{c.card_no}" if c else f"#{cid}")
                    self.log_rule("Rule 9.6.2", f"Player {p.player_id} reveals their hand: {', '.join(hand_nos)}")
                return True
            elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_DECK:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0 and p.stage[area] >= 0:
                        p.main_deck.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.rested_members[area] = False
                        p.stage_energy[area].clear()
                        random.shuffle(p.main_deck)
                    else:
                        return False
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": "デッキに戻すメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_HAND:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_member",
                                "effect_description": f"手札からメンバーを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_HAND:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_live",
                                "effect_description": f"手札からライブを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_HAND:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_energy",
                                "effect_description": f"手札からエールを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DISCARD:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_member",
                                "effect_description": f"捨て札からメンバーを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DISCARD:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_live",
                                "effect_description": f"捨て札からライブを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DISCARD:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_energy",
                                "effect_description": f"捨て札からエールを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DECK:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member",
                                "effect_description": f"デッキからメンバーを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DECK:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live",
                                "effect_description": f"デッキからライブを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DECK:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy",
                                "effect_description": f"デッキからエールを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.REVEAL_HAND:
                # This cost doesn't require a choice, just a state change
                p.revealed_hand = True
            elif cost.cost_type == AbilityCostType.SHUFFLE_DECK:
                random.shuffle(p.main_deck)
            elif cost.cost_type == AbilityCostType.DRAW_CARD:
                for _ in range(cost.value):
                    self._draw_card(player_id)
            elif cost.cost_type == AbilityCostType.DISCARD_TOP_DECK:
                for _ in range(cost.value):
                    if p.main_deck:
                        p.discard.append(p.main_deck.pop(0))
                    else:
                        return False  # Cannot pay cost
            elif cost.cost_type == AbilityCostType.REMOVE_TOP_DECK:
                for _ in range(cost.value):
                    if p.main_deck:
                        self.removed_cards.append(p.main_deck.pop(0))
                    else:
                        return False  # Cannot pay cost
            elif cost.cost_type == AbilityCostType.RETURN_DISCARD_TO_DECK:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": f"捨て札から{cost.value}枚デッキに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_REMOVED_TO_DECK:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": f"除外ゾーンから{cost.value}枚デッキに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_REMOVED_TO_HAND:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"除外ゾーンから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_REMOVED_TO_DISCARD:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"除外ゾーンから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_SUCCESS:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_energy",
                                "effect_description": f"成功ライブからエールを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.DISCARD_SUCCESS_LIVE:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "discard",
                                "effect_description": f"成功ライブから{cost.value}枚捨ててください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.REMOVE_SUCCESS_LIVE:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "remove",
                                "effect_description": f"成功ライブから{cost.value}枚除外してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_SUCCESS_LIVE_TO_HAND:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"成功ライブから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_SUCCESS_LIVE_TO_DECK:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": f"成功ライブから{cost.value}枚デッキに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_SUCCESS_LIVE_TO_DISCARD:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"成功ライブから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_SUCCESS:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_member",
                                "effect_description": f"成功ライブからメンバーを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_SUCCESS:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_live",
                                "effect_description": f"成功ライブからライブを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_REMOVED:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_energy",
                                "effect_description": f"除外ゾーンからエールを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_REMOVED:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_member",
                                "effect_description": f"除外ゾーンからメンバーを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_REMOVED:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_live",
                                "effect_description": f"除外ゾーンからライブを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_TO_DECK:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": f"エールゾーンから{cost.value}枚デッキに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_TO_HAND:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"エールゾーンから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.DISCARD_ENERGY:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "discard",
                                "effect_description": f"エールゾーンから{cost.value}枚捨ててください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.REMOVE_ENERGY:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "remove",
                                "effect_description": f"エールゾーンから{cost.value}枚除外してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_STAGE_ENERGY_TO_DECK:
                # This cost type is for returning energy from a specific stage area
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "return_stage_energy_to_deck",
                                "effect_description": f"ステージのエールから{cost.value}枚デッキに戻してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_STAGE_ENERGY_TO_HAND:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "return_stage_energy_to_hand",
                                "effect_description": f"ステージのエールから{cost.value}枚手札に戻してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.DISCARD_STAGE_ENERGY:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "discard_stage_energy",
                                "effect_description": f"ステージのエールから{cost.value}枚捨ててください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.REMOVE_STAGE_ENERGY:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "remove_stage_energy",
                                "effect_description": f"ステージのエールから{cost.value}枚除外してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_STAGE_ENERGY:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_energy_from_stage_energy",
                                "effect_description": f"ステージのエールから{cost.value}枚エールゾーンに配置してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_STAGE_ENERGY:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_member_from_stage_energy",
                                "effect_description": f"ステージのエールからメンバーを{cost.value}枚配置してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_STAGE_ENERGY:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_live_from_stage_energy",
                                "effect_description": f"ステージのエールからライブを{cost.value}枚配置してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_HAND_TO_STAGE_ENERGY:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_stage_energy",
                                "effect_description": f"手札からエールを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_HAND_TO_STAGE_ENERGY:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_stage_energy",
                                "effect_description": f"手札からメンバーを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_HAND_TO_STAGE_ENERGY:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_stage_energy",
                                "effect_description": f"手札からライブを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DISCARD_TO_STAGE_ENERGY:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_stage_energy",
                                "effect_description": f"捨て札からエールを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DISCARD_TO_STAGE_ENERGY:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_stage_energy",
                                "effect_description": f"捨て札からメンバーを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DISCARD_TO_STAGE_ENERGY:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_stage_energy",
                                "effect_description": f"捨て札からライブを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DECK_TO_STAGE_ENERGY:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_stage_energy",
                                "effect_description": f"デッキからエールを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DECK_TO_STAGE_ENERGY:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_stage_energy",
                                "effect_description": f"デッキからメンバーを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DECK_TO_STAGE_ENERGY:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_stage_energy",
                                "effect_description": f"デッキからライブを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_SUCCESS_TO_STAGE_ENERGY:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_stage_energy",
                                "effect_description": f"成功ライブからエールを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_SUCCESS_TO_STAGE_ENERGY:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_stage_energy",
                                "effect_description": f"成功ライブからメンバーを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_SUCCESS_TO_STAGE_ENERGY:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_stage_energy",
                                "effect_description": f"成功ライブからライブを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_REMOVED_TO_STAGE_ENERGY:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_stage_energy",
                                "effect_description": f"除外ゾーンからエールを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_REMOVED_TO_STAGE_ENERGY:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_stage_energy",
                                "effect_description": f"除外ゾーンからメンバーを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_REMOVED_TO_STAGE_ENERGY:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_stage_energy",
                                "effect_description": f"除外ゾーンからライブを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_STAGE_ENERGY_TO_SUCCESS:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "return_stage_energy_to_success",
                                "effect_description": f"ステージのエールから{cost.value}枚成功ライブに戻してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_STAGE_ENERGY_TO_DISCARD:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "return_stage_energy_to_discard",
                                "effect_description": f"ステージのエールから{cost.value}枚捨て札に戻してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_STAGE_ENERGY_TO_REMOVED:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "return_stage_energy_to_removed",
                                "effect_description": f"ステージのエールから{cost.value}枚除外ゾーンに戻してください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_TO_SUCCESS:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "return_to_success",
                                "effect_description": f"エールゾーンから{cost.value}枚成功ライブに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_TO_DISCARD:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"エールゾーンから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_TO_REMOVED:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "return_to_removed",
                                "effect_description": f"エールゾーンから{cost.value}枚除外ゾーンに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_SUCCESS:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0 and p.stage[area] >= 0:
                        p.success_lives.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.rested_members[area] = False
                        p.stage_energy[area].clear()
                    else:
                        return False
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "return_to_success",
                                "effect_description": "成功ライブに戻すメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_DISCARD:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0 and p.stage[area] >= 0:
                        p.discard.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.rested_members[area] = False
                        p.stage_energy[area].clear()
                    else:
                        return False
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": "捨て札に戻すメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_REMOVED:
                if cost.target == TargetType.MEMBER_SELF:
                    area = context.get("area", -1)
                    if area >= 0 and p.stage[area] >= 0:
                        self.removed_cards.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.rested_members[area] = False
                        p.stage_energy[area].clear()
                    else:
                        return False
                else:
                    self.pending_choices.append(
                        (
                            "TARGET_MEMBER",
                            {
                                **cost_metadata,
                                "effect": "return_to_removed",
                                "effect_description": "除外ゾーンに戻すメンバーを選んでください",
                                "is_optional": False,
                            },
                        )
                    )
                return False
            elif cost.cost_type == AbilityCostType.RETURN_LIVE_TO_SUCCESS:
                if len(p.live_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_LIVE",
                            {
                                **cost_metadata,
                                "effect": "return_to_success",
                                "effect_description": f"ライブゾーンから{cost.value}枚成功ライブに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_LIVE_TO_DISCARD:
                if len(p.live_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_LIVE",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"ライブゾーンから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_LIVE_TO_REMOVED:
                if len(p.live_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_LIVE",
                            {
                                **cost_metadata,
                                "effect": "return_to_removed",
                                "effect_description": f"ライブゾーンから{cost.value}枚除外ゾーンに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_DISCARD_TO_HAND:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"捨て札から{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_DISCARD_TO_SUCCESS:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "return_to_success",
                                "effect_description": f"捨て札から{cost.value}枚成功ライブに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_DISCARD_TO_REMOVED:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "return_to_removed",
                                "effect_description": f"捨て札から{cost.value}枚除外ゾーンに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_DECK_TO_HAND:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"デッキから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_DECK_TO_DISCARD:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"デッキから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_DECK_TO_SUCCESS:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_success",
                                "effect_description": f"デッキから{cost.value}枚成功ライブに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_DECK_TO_REMOVED:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_removed",
                                "effect_description": f"デッキから{cost.value}枚除外ゾーンに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_SUCCESS_LIVE_TO_DISCARD:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"成功ライブから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_SUCCESS_LIVE_TO_REMOVED:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "return_to_removed",
                                "effect_description": f"成功ライブから{cost.value}枚除外ゾーンに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_SUCCESS_LIVE_TO_HAND:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"成功ライブから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_SUCCESS_LIVE_TO_DECK:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": f"成功ライブから{cost.value}枚デッキに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_REMOVED_TO_DISCARD:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"除外ゾーンから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_REMOVED_TO_SUCCESS:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "return_to_success",
                                "effect_description": f"除外ゾーンから{cost.value}枚成功ライブに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_REMOVED_TO_DECK:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "return_to_deck",
                                "effect_description": f"除外ゾーンから{cost.value}枚デッキに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_REMOVED_TO_HAND:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"除外ゾーンから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_DECK_TO_HAND:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_hand",
                                "effect_description": f"エールデッキから{cost.value}枚手札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_DECK_TO_DISCARD:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_discard",
                                "effect_description": f"エールデッキから{cost.value}枚捨て札に戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_DECK_TO_SUCCESS:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_success",
                                "effect_description": f"エールデッキから{cost.value}枚成功ライブに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.RETURN_ENERGY_DECK_TO_REMOVED:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "return_to_removed",
                                "effect_description": f"エールデッキから{cost.value}枚除外ゾーンに戻してください",
                                "is_optional": False,
                                "count": cost.value,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_DECK:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy",
                                "effect_description": f"エールデッキからエールを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_DECK:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member",
                                "effect_description": f"エールデッキからメンバーを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_DECK:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live",
                                "effect_description": f"エールデッキからライブを{cost.value}枚配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_DECK_TO_STAGE_ENERGY:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_stage_energy",
                                "effect_description": f"エールデッキからエールを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_DECK_TO_STAGE_ENERGY:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_stage_energy",
                                "effect_description": f"エールデッキからメンバーを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_DECK_TO_STAGE_ENERGY:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_stage_energy",
                                "effect_description": f"エールデッキからライブを{cost.value}枚ステージのエールに配置してください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_DECK_TO_HAND:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_hand",
                                "effect_description": f"エールデッキからエールを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_DECK_TO_HAND:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_hand",
                                "effect_description": f"エールデッキからメンバーを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_DECK_TO_HAND:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_hand",
                                "effect_description": f"エールデッキからライブを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_DECK_TO_DISCARD:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_discard",
                                "effect_description": f"エールデッキからエールを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_DECK_TO_DISCARD:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_discard",
                                "effect_description": f"エールデッキからメンバーを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_DECK_TO_DISCARD:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_discard",
                                "effect_description": f"エールデッキからライブを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_DECK_TO_SUCCESS:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_success",
                                "effect_description": f"エールデッキからエールを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_DECK_TO_SUCCESS:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_success",
                                "effect_description": f"エールデッキからメンバーを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_DECK_TO_SUCCESS:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_success",
                                "effect_description": f"エールデッキからライブを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_DECK_TO_REMOVED:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_removed",
                                "effect_description": f"エールデッキからエールを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_DECK_TO_REMOVED:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_removed",
                                "effect_description": f"エールデッキからメンバーを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_DECK_TO_REMOVED:
                if len(p.energy_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_removed",
                                "effect_description": f"エールデッキからライブを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DECK_TO_HAND:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_hand",
                                "effect_description": f"デッキからエールを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DECK_TO_HAND:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_hand",
                                "effect_description": f"デッキからメンバーを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DECK_TO_HAND:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_hand",
                                "effect_description": f"デッキからライブを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DECK_TO_DISCARD:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_discard",
                                "effect_description": f"デッキからエールを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DECK_TO_DISCARD:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_discard",
                                "effect_description": f"デッキからメンバーを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DECK_TO_DISCARD:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_discard",
                                "effect_description": f"デッキからライブを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DECK_TO_SUCCESS:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_success",
                                "effect_description": f"デッキからエールを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DECK_TO_SUCCESS:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_success",
                                "effect_description": f"デッキからメンバーを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DECK_TO_SUCCESS:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_success",
                                "effect_description": f"デッキからライブを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DECK_TO_REMOVED:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_removed",
                                "effect_description": f"デッキからエールを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DECK_TO_REMOVED:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_removed",
                                "effect_description": f"デッキからメンバーを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DECK_TO_REMOVED:
                if len(p.main_deck) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DECK",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_removed",
                                "effect_description": f"デッキからライブを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DISCARD_TO_HAND:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_hand",
                                "effect_description": f"捨て札からエールを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DISCARD_TO_HAND:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_hand",
                                "effect_description": f"捨て札からメンバーを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DISCARD_TO_HAND:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_hand",
                                "effect_description": f"捨て札からライブを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DISCARD_TO_SUCCESS:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_success",
                                "effect_description": f"捨て札からエールを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DISCARD_TO_SUCCESS:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_success",
                                "effect_description": f"捨て札からメンバーを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DISCARD_TO_SUCCESS:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_success",
                                "effect_description": f"捨て札からライブを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_DISCARD_TO_REMOVED:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_removed",
                                "effect_description": f"捨て札からエールを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_DISCARD_TO_REMOVED:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_removed",
                                "effect_description": f"捨て札からメンバーを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_DISCARD_TO_REMOVED:
                if len(p.discard) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_DISCARD",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_removed",
                                "effect_description": f"捨て札からライブを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_HAND_TO_DISCARD:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_discard",
                                "effect_description": f"手札からエールを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_HAND_TO_DISCARD:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_discard",
                                "effect_description": f"手札からメンバーを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_HAND_TO_DISCARD:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_discard",
                                "effect_description": f"手札からライブを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_HAND_TO_SUCCESS:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_success",
                                "effect_description": f"手札からエールを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_HAND_TO_SUCCESS:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_success",
                                "effect_description": f"手札からメンバーを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_HAND_TO_SUCCESS:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_success",
                                "effect_description": f"手札からライブを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_HAND_TO_REMOVED:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_removed",
                                "effect_description": f"手札からエールを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_HAND_TO_REMOVED:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_removed",
                                "effect_description": f"手札からメンバーを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_HAND_TO_REMOVED:
                if len(p.hand) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_HAND",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_removed",
                                "effect_description": f"手札からライブを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_SUCCESS_TO_HAND:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_hand",
                                "effect_description": f"成功ライブからエールを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_SUCCESS_TO_HAND:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_hand",
                                "effect_description": f"成功ライブからメンバーを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_SUCCESS_TO_HAND:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_hand",
                                "effect_description": f"成功ライブからライブを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_SUCCESS_TO_DISCARD:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_discard",
                                "effect_description": f"成功ライブからエールを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_SUCCESS_TO_DISCARD:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_discard",
                                "effect_description": f"成功ライブからメンバーを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_SUCCESS_TO_DISCARD:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_discard",
                                "effect_description": f"成功ライブからライブを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_SUCCESS_TO_REMOVED:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_removed",
                                "effect_description": f"成功ライブからエールを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_SUCCESS_TO_REMOVED:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_removed",
                                "effect_description": f"成功ライブからメンバーを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_SUCCESS_TO_REMOVED:
                if len(p.success_lives) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_SUCCESS_LIVES",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_removed",
                                "effect_description": f"成功ライブからライブを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_REMOVED_TO_HAND:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_hand",
                                "effect_description": f"除外ゾーンからエールを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_REMOVED_TO_HAND:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_hand",
                                "effect_description": f"除外ゾーンからメンバーを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_REMOVED_TO_HAND:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_hand",
                                "effect_description": f"除外ゾーンからライブを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_REMOVED_TO_DISCARD:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_discard",
                                "effect_description": f"除外ゾーンからエールを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_REMOVED_TO_DISCARD:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_discard",
                                "effect_description": f"除外ゾーンからメンバーを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_REMOVED_TO_DISCARD:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_discard",
                                "effect_description": f"除外ゾーンからライブを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_REMOVED_TO_SUCCESS:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_success",
                                "effect_description": f"除外ゾーンからエールを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_REMOVED_TO_SUCCESS:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_success",
                                "effect_description": f"除外ゾーンからメンバーを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_REMOVED_TO_SUCCESS:
                if len(self.removed_cards) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_REMOVED",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_success",
                                "effect_description": f"除外ゾーンからライブを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_ZONE_TO_HAND:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_hand",
                                "effect_description": f"エールゾーンからエールを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_ZONE_TO_HAND:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_hand",
                                "effect_description": f"エールゾーンからメンバーを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_ZONE_TO_HAND:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_hand",
                                "effect_description": f"エールゾーンからライブを{cost.value}枚手札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_ZONE_TO_DISCARD:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_discard",
                                "effect_description": f"エールゾーンからエールを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_ZONE_TO_DISCARD:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_discard",
                                "effect_description": f"エールゾーンからメンバーを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_ZONE_TO_DISCARD:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_discard",
                                "effect_description": f"エールゾーンからライブを{cost.value}枚捨て札に加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_ZONE_TO_SUCCESS:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_success",
                                "effect_description": f"エールゾーンからエールを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_ZONE_TO_SUCCESS:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_success",
                                "effect_description": f"エールゾーンからメンバーを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_ZONE_TO_SUCCESS:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_success",
                                "effect_description": f"エールゾーンからライブを{cost.value}枚成功ライブに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_ENERGY_ZONE_TO_REMOVED:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_energy_to_removed",
                                "effect_description": f"エールゾーンからエールを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_ENERGY_ZONE_TO_REMOVED:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_member_to_removed",
                                "effect_description": f"エールゾーンからメンバーを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_ENERGY_ZONE_TO_REMOVED:
                if len(p.energy_zone) > 0:
                    self.pending_choices.append(
                        (
                            "TARGET_ENERGY_ZONE",
                            {
                                **cost_metadata,
                                "effect": "place_live_to_removed",
                                "effect_description": f"エールゾーンからライブを{cost.value}枚除外ゾーンに加えてください",
                                "is_optional": False,
                                "count": cost.value,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_STAGE_ENERGY_TO_HAND:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_energy_from_stage_energy_to_hand",
                                "effect_description": f"ステージのエールから{cost.value}枚手札に加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_STAGE_ENERGY_TO_HAND:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_member_from_stage_energy_to_hand",
                                "effect_description": f"ステージのエールからメンバーを{cost.value}枚手札に加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_STAGE_ENERGY_TO_HAND:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_live_from_stage_energy_to_hand",
                                "effect_description": f"ステージのエールからライブを{cost.value}枚手札に加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_STAGE_ENERGY_TO_DISCARD:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_energy_from_stage_energy_to_discard",
                                "effect_description": f"ステージのエールから{cost.value}枚捨て札に加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_STAGE_ENERGY_TO_DISCARD:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_member_from_stage_energy_to_discard",
                                "effect_description": f"ステージのエールからメンバーを{cost.value}枚捨て札に加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_STAGE_ENERGY_TO_DISCARD:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_live_from_stage_energy_to_discard",
                                "effect_description": f"ステージのエールからライブを{cost.value}枚捨て札に加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_STAGE_ENERGY_TO_SUCCESS:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_energy_from_stage_energy_to_success",
                                "effect_description": f"ステージのエールから{cost.value}枚成功ライブに加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_STAGE_ENERGY_TO_SUCCESS:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_member_from_stage_energy_to_success",
                                "effect_description": f"ステージのエールからメンバーを{cost.value}枚成功ライブに加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_STAGE_ENERGY_TO_SUCCESS:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_live_from_stage_energy_to_success",
                                "effect_description": f"ステージのエールからライブを{cost.value}枚成功ライブに加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_ENERGY_FROM_STAGE_ENERGY_TO_REMOVED:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_energy_from_stage_energy_to_removed",
                                "effect_description": f"ステージのエールから{cost.value}枚除外ゾーンに加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.ENERGY.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_MEMBER_FROM_STAGE_ENERGY_TO_REMOVED:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_member_from_stage_energy_to_removed",
                                "effect_description": f"ステージのエールからメンバーを{cost.value}枚除外ゾーンに加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.MEMBER.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            elif cost.cost_type == AbilityCostType.PLACE_LIVE_FROM_STAGE_ENERGY_TO_REMOVED:
                area = context.get("area", -1)
                if area >= 0 and p.stage_energy[area]:
                    self.pending_choices.append(
                        (
                            "SELECT_FROM_LIST",
                            {
                                **cost_metadata,
                                "cards": p.stage_energy[area],
                                "count": cost.value,
                                "reason": "place_live_from_stage_energy_to_removed",
                                "effect_description": f"ステージのエールからライブを{cost.value}枚除外ゾーンに加えてください",
                                "zone": "STAGE_ENERGY",
                                "zone_index": area,
                                "filter_group": Group.LIVE.name,
                            },
                        )
                    )
                    return False
                else:
                    return False
            else:
                # Unknown cost type, or cost type that doesn't require choice
                pass
        return True  # All costs paid or no costs

    def _play_automatic_ability(self, player_id: int, ability: Ability, context: Dict[str, Any]) -> None:
        """Resolve an automatic ability (Rule 9.5)."""
        if self.verbose:
            print(f"DEBUG: Entering _play_automatic_ability for player {player_id}")
        p = self.players[player_id]
        cid = context.get("card_id", -1)
        self.current_resolving_ability = ability
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
                self.pending_activation = {"ability": ability, "context": context, "abi_key": abi_key}
                return

        # Prepare metadata for progress tracking
        if JIT_AVAILABLE and hasattr(self, "fast_mode") and self.fast_mode:
            bytecode = ability.compile()
            # Push the compiled bytecode as a single "effect" to pending_effects
            # _resolve_pending_effect will then pass it to _resolve_effect_opcode
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
            self.current_resolving_member = None
            self.current_resolving_member_id = -1
            self.looked_cards = []  # Clear transient looked cards

    def _resolve_pending_effect(self, action: int, context: Optional[Dict[str, Any]] = None) -> None:
        """Resolve top effect from stack"""
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
                    met = self._resolve_condition_opcode(Opcode(base_op), resolving_effect[i : i + 4], context)
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
                                "effect_description": "選択してください",
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
            "source_ability": self.current_resolving_ability.raw_text if self.current_resolving_ability else "",
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
                ability_text = f" [{self.current_resolving_ability.raw_text[:20]}...]"

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
                            "effect_description": "回収するライブを選んでください",
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
                            "effect_description": "回収するメンバーを選んでください",
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
                        "effect_description": "色を選んでください",
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
                            "effect_description": f"活動させるエールを{effect.value}枚選んでください",
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
                            "effect_description": "活動させるメンバーを選んでください",
                            "is_optional": False,
                        },
                    )
                )
            return

        if effect.target == TargetType.CARD_HAND and effect.effect_type != EffectType.SWAP_CARDS:
            if len(p.hand) > 0:
                effect_desc = (
                    "手札から捨てるカードを選んでください"
                    if effect.effect_type == EffectType.SWAP_CARDS
                    else "手札からカードを選んでください"
                )
                self.pending_choices.append(
                    (
                        "TARGET_HAND",
                        {
                            **choice_metadata,
                            "effect": "discard" if effect.effect_type == EffectType.SWAP_CARDS else "select",
                            "effect_description": effect_desc,
                            "is_optional": False,
                            **effect.params,
                        },
                    )
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
                            "effect_description": f"{effect.effect_type.name}の対象メンバーを選んでください",
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
                        "effect_description": "以下から1つ選んでください",
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
                        "effect_description": "ハートの色を選んでください",
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
                    self.current_resolving_ability and "相手は" in self.current_resolving_ability.raw_text
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
                                "effect_description": "ウェイトにする自分のメンバーを選んでください",
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
                                "effect_description": "相手のメンバーを選んでタップしてください",
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
                        "effect_description": "移動するメンバーを選んでください",
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
                        "effect_description": "移動先を選んでください",
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
                        "effect_description": "交換に出すライブを選んでください",
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
            r_type = effect.params.get("type", "unknown")
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

                    # Apply Group/Unit Filter from params (e.g. "みらくらぱーく！")
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
                            # If "みらくらぱーく" -> Unit.MIRA_CRA_PARK (15), Group.OTHER (99).
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
                    reorder = effect.params.get("reorder", False)

                    reason = "look_and_choose"
                    desc = "手札に加えるカードを選んでください"

                    if dest == "deck_top":
                        reason = "look_and_reorder"
                        if any_number:
                            desc = "デッキの上に置くカードを選んでください（0枚でもよい）"
                        else:
                            desc = "デッキの上に置くカードを選んでください"

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
            draw_on_discard = effect.params.get("draw_on_discard", True)

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
                            "effect_description": "タップするメンバーを選んでください",
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
                            "effect_description": "控え室から手札に加えるライブカードを選んでください",
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
                            "effect_description": "控え室から手札に加えるメンバーを選んでください",
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
                                "effect_description": f"控え室に置く手札を{effect.value}枚選んでください",
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
                                "effect_description": "控え室から手札に加えるカードを選んでください",
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
                                "effect_description": "効果を発動するメンバーを選んでください",
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
                            "effect_description": f"手札からメンバーを{effect.value}枚配置してください",
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
                            "effect_description": "エールにする手札を選んでください",
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
            if "何が好き" in text_param or "formation" in text_param.lower():
                # This is a formation change flavor action
                self.pending_choices.append(
                    (
                        "CHOOSE_FORMATION",
                        {
                            **choice_metadata,
                            "player_id": opp_idx,
                            "title": text_param if text_param else "何が好き？",
                            "options": [
                                "チョコミント",
                                "ストロベリーフレイバー",
                                "クッキー＆クリーム",
                                "あなた",
                                "それ以外",
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
                            "title": "何が好き？",
                            "options": [
                                "チョコミント",
                                "ストロベリーフレイバー",
                                "クッキー＆クリーム",
                                "あなた",
                                "それ以外",
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
                            "effect_description": "カードの順番を選んでください",
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
                                "effect_description": f"メンバーの下に置くエールを{effect.value}枚選んでください",
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
                            "effect_description": "デッキから加えるカードを選んでください",
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
                            "effect_description": "移動するメンバーを選んでください",
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

    def _check_condition(self, player: Any, cond: Any, context: Optional[Dict[str, Any]] = None) -> bool:
        if context is None:
            context = {}
        met = False
        if self.verbose:
            print(f"DEBUG: Checking condition {cond.type} Params: {cond.params} CTX: {context}")
        if cond.type == ConditionType.NONE:
            met = True
        elif cond.type == ConditionType.SCORE_COMPARE:
            if cond.params.get("type") == "score":
                val = sum(self.live_db[cid].score for cid in player.success_lives if cid in self.live_db)
                req = cond.params.get("value", 0)
                comp = cond.params.get("comparison", "GE")
                if comp == "GE":
                    met = val >= req
                elif comp == "GT":
                    met = val > req
                elif comp == "LE":
                    met = val <= req
                elif comp == "LT":
                    met = val < req
                else:
                    met = val == req
            elif cond.params.get("type") == "cost":
                opp = self.players[1 - player.player_id]
                target_zone = cond.params.get("zone", "STAGE")

                def get_cost_in_zone(p, z):
                    if z == "CENTER_STAGE" or z == "OPPONENT_CENTER_STAGE":
                        cid = p.stage[1]
                        return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                    elif z == "LEFT_STAGE" or z == "OPPONENT_LEFT_STAGE":
                        cid = p.stage[0]
                        return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                    elif z == "RIGHT_STAGE" or z == "OPPONENT_RIGHT_STAGE":
                        cid = p.stage[2]
                        return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                    return sum(self.member_db[cid].cost for cid in p.stage if cid >= 0 and cid in self.member_db)

                my_cost = get_cost_in_zone(player, target_zone)
                opp_cost = get_cost_in_zone(
                    opp, "OPPONENT_" + target_zone if "OPPONENT_" not in target_zone else target_zone
                )

                # Default to comparing vs opponent if no fixed value
                req = cond.params.get("value", opp_cost)
                val = my_cost

                comp = cond.params.get("comparison", "GE")
                if comp == "GE":
                    met = val >= req
                elif comp == "GT":
                    met = val > req
                elif comp == "LE":
                    met = val <= req
                elif comp == "LT":
                    met = val < req
                else:
                    met = val == req
        elif cond.type == ConditionType.AREA_CHECK:
            req_area = cond.params.get("value")
            current_area = context.get("area")
            # Infer area from card_id if missing
            if current_area is None and "card_id" in context:
                cid = context["card_id"]
                for i, c in enumerate(player.stage):
                    if c == cid:
                        current_area = i
                        break
            met = current_area == req_area
        elif cond.type == ConditionType.TURN_1:
            met = self.turn_number == 1
        elif cond.type == ConditionType.IS_CENTER:
            met = context.get("area") == 1
        elif cond.type == ConditionType.HAS_MEMBER:
            name = cond.params.get("name")
            area = cond.params.get("area")
            found = False
            for i, cid in enumerate(player.stage):
                if cid >= 0 and cid in self.member_db:
                    m = self.member_db[cid]
                    if name and name in m.name:
                        if area == "CENTER_STAGE" and i != 1:
                            continue
                        if area == "LEFT_STAGE" and i != 0:
                            continue
                        if area == "RIGHT_STAGE" and i != 2:
                            continue
                        found = True
                        break
            met = found
        elif cond.type == ConditionType.COUNT_STAGE:
            met = sum(1 for cid in player.stage if cid >= 0) >= cond.params.get("min", 0)
        elif cond.type == ConditionType.LIFE_LEAD:
            met = len(player.success_lives) > len(self.players[1 - player.player_id].success_lives)
        elif cond.type == ConditionType.COUNT_GROUP:
            group_str = cond.params.get("group", "").strip("「」")
            zone = cond.params.get("zone", "STAGE")
            min_count = cond.params.get("count", cond.params.get("min", 0))
            if not group_str:
                return False
            target_group = Group.from_japanese_name(group_str)
            target_unit = Unit.from_japanese_name(group_str)
            count = 0
            cards = []
            if cond.params.get("context") == "revealed":
                cards = self.looked_cards
            elif "OPPONENT_" in zone:
                opp = self.players[1 - player.player_id]
                oz = zone.replace("OPPONENT_", "")
                if oz == "STAGE":
                    cards = [c for c in opp.stage if c >= 0]
                elif oz == "DISCARD":
                    cards = opp.discard
                elif oz == "HAND":
                    cards = opp.hand
                elif oz == "DECK":
                    cards = opp.main_deck
                elif oz == "LIVE_ZONE":
                    cards = opp.live_zone
                elif oz == "CENTER_STAGE":
                    cards = [opp.stage[1]] if opp.stage[1] >= 0 else []
                elif oz == "LEFT_STAGE":
                    cards = [opp.stage[0]] if opp.stage[0] >= 0 else []
                elif oz == "RIGHT_STAGE":
                    cards = [opp.stage[2]] if opp.stage[2] >= 0 else []
            elif zone == "STAGE":
                cards = [c for c in player.stage if c >= 0]
            elif zone == "DISCARD":
                cards = player.discard
            elif zone == "HAND":
                cards = player.hand
            elif zone == "DECK":
                cards = player.main_deck
            elif zone == "LIVE_ZONE":
                cards = player.live_zone
            elif zone == "CENTER_STAGE":
                cards = [player.stage[1]] if player.stage[1] >= 0 else []
            elif zone == "LEFT_STAGE":
                cards = [player.stage[0]] if player.stage[0] >= 0 else []
            elif zone == "RIGHT_STAGE":
                cards = [player.stage[2]] if player.stage[2] >= 0 else []
            for cid in cards:
                try:
                    cid_int = int(cid)
                except ValueError:
                    continue
                card = self.member_db.get(cid_int) or self.live_db.get(cid_int)
                if card:
                    groups = getattr(card, "groups", [])
                    units = getattr(card, "units", [])
                    is_match = target_group in groups or target_unit in units
                    if is_match:
                        count += 1
            met = count >= min_count
        elif cond.type == ConditionType.HAS_COLOR:
            active_hearts = player.get_total_hearts(self.member_db)
            color_map = {"赤": 1, "青": 4, "緑": 3, "黄": 2, "紫": 5, "ピンク": 0}
            idx = color_map.get(str(cond.params.get("color", "")))
            met = active_hearts[idx] > 0 if idx is not None else False
        elif cond.type == ConditionType.OPPONENT_HAND_DIFF:
            diff_val = len(self.players[1 - player.player_id].hand) - len(player.hand)
            req_diff = cond.params.get("diff", 0)
            comp = cond.params.get("comparison", "GT")
            if comp == "GT":
                met = diff_val >= req_diff
            elif comp == "LT":
                met = (
                    diff_val <= req_diff
                )  # Or strictly less? Usually "Less than X" means < X or <= X depending on wording. Usually existing logic uses inclusive.
            else:
                met = diff_val == req_diff
        elif cond.type == ConditionType.HAND_INCREASED:
            # Check how many cards added to hand this turn
            # hand_added_turn tracks timestamps (turn numbers) of additions
            count = sum(1 for t in player.hand_added_turn if t == self.turn_number)
            met = count >= cond.params.get("min", 1)
        elif cond.type == ConditionType.COUNT_ENERGY:
            met = len(player.energy_zone) >= cond.params.get("min", 0)
        elif cond.type == ConditionType.HAS_LIVE_CARD:
            # Check if looked_cards (milled/revealed) contains a live card
            if self.looked_cards:
                met = any(cid in self.live_db for cid in self.looked_cards)
            else:
                met = len(player.live_zone) > 0

        elif cond.type == ConditionType.COUNT_HAND:
            met = len(player.hand) >= cond.params.get("min", 0)
        elif cond.type == ConditionType.COUNT_DISCARD:
            met = len(player.discard) >= cond.params.get("min", 0)
        elif cond.type == ConditionType.SELF_IS_GROUP:
            cid = context.get("card_id")
            req_group = Group.from_japanese_name(cond.params.get("group", ""))
            card = self.member_db.get(cid) or self.live_db.get(cid)
            met = req_group in getattr(card, "groups", []) if card else False
        elif cond.type == ConditionType.MODAL_ANSWER:
            met = context.get("answer") == cond.params.get("answer")
        elif cond.type == ConditionType.HAND_HAS_NO_LIVE:
            met = not any(cid in self.live_db for cid in player.hand)
        elif cond.type == ConditionType.COUNT_SUCCESS_LIVE:
            met = len(player.success_lives) >= cond.params.get("min", 0)
        elif cond.type == ConditionType.GROUP_FILTER:
            group_str = cond.params.get("group", "")
            if not group_str:
                met = False
            else:
                target_group = Group.from_japanese_name(group_str)
                target_unit = Unit.from_japanese_name(group_str)
                cards = []
                if cond.params.get("context") == "revealed":
                    cards = self.looked_cards
                elif cond.params.get("context") == "live_zone":
                    cards = player.live_zone
                elif "zone" in cond.params:
                    z = cond.params["zone"]
                    if "OPPONENT_" in z:
                        opp = self.players[1 - player.player_id]
                        oz = z.replace("OPPONENT_", "")
                        if oz == "STAGE":
                            cards = [c for c in opp.stage if c >= 0]
                        elif oz == "DISCARD":
                            cards = opp.discard
                        elif oz == "HAND":
                            cards = opp.hand
                        elif oz == "DECK":
                            cards = opp.main_deck
                        elif oz == "LIVE_ZONE":
                            cards = opp.live_zone
                        elif oz == "CENTER_STAGE":
                            cards = [opp.stage[1]] if opp.stage[1] >= 0 else []
                        elif oz == "LEFT_STAGE":
                            cards = [opp.stage[0]] if opp.stage[0] >= 0 else []
                        elif oz == "RIGHT_STAGE":
                            cards = [opp.stage[2]] if opp.stage[2] >= 0 else []
                    elif z == "STAGE":
                        cards = [c for c in player.stage if c >= 0]
                    elif z == "DISCARD":
                        cards = player.discard
                    elif z == "HAND":
                        cards = player.hand
                    elif z == "DECK":
                        cards = player.main_deck
                    elif z == "LIVE_ZONE":
                        cards = player.live_zone
                    elif z == "CENTER_STAGE":
                        cards = [player.stage[1]] if player.stage[1] >= 0 else []
                    elif z == "LEFT_STAGE":
                        cards = [player.stage[0]] if player.stage[0] >= 0 else []
                    elif z == "RIGHT_STAGE":
                        cards = [player.stage[2]] if player.stage[2] >= 0 else []
                elif context.get("card_id") is not None:
                    cards = [context["card_id"]]
                else:
                    cards = [c for c in player.stage if c >= 0]

                # Filter out self if requested
                if cond.params.get("exclude_self") and context.get("card_id") is not None:
                    cards = [c for c in cards if c != context["card_id"]]

                match_count = 0
                for cid in cards:
                    card = self.member_db.get(cid) or self.live_db.get(cid)
                    if card and (
                        target_group in getattr(card, "groups", []) or target_unit in getattr(card, "units", [])
                    ):
                        match_count += 1
                met = match_count >= cond.params.get("min", cond.params.get("count", 1))

        elif cond.type == ConditionType.COST_CHECK:
            # If we have a target card in context, check its cost
            target_cid = context.get("target_card_id")
            if target_cid is not None:
                val = (self.member_db.get(target_cid) or self.live_db.get(target_cid)).cost
                req = cond.params.get("value", 0)
                comp = cond.params.get("comparison", "GE")
                if comp == "GE":
                    met = val >= req
                elif comp == "GT":
                    met = val > req
                elif comp == "LE":
                    met = val <= req
                elif comp == "LT":
                    met = val < req
                else:
                    met = val == req
            else:
                # Fallback: check source card or stage
                target_ids = []
                if context.get("card_id") is not None:
                    target_ids = [context["card_id"]]
                else:
                    target_ids = [c for c in player.stage if c >= 0]

                req = cond.params.get("value", 0)
                comp = cond.params.get("comparison", "LE")
                for cid in target_ids:
                    card = self.member_db.get(cid) or self.live_db.get(cid)
                    if not card:
                        continue
                    val = card.cost
                    is_match = val <= req if comp == "LE" else val >= req
                    if is_match:
                        met = True
                        break

        elif cond.type == ConditionType.OPPONENT_CHOICE or cond.type == ConditionType.HAS_CHOICE:
            met = True

        elif cond.type == ConditionType.OPPONENT_HAS:
            opp = self.players[1 - player.player_id]
            req_name = cond.params.get("name")
            if req_name:
                met = any(
                    req_name in (self.member_db[cid].name if cid in self.member_db else "")
                    for cid in opp.stage
                    if cid >= 0
                )
            else:
                met = any(cid >= 0 for cid in opp.stage)
        elif cond.type == ConditionType.DECK_REFRESHED:
            met = player.deck_refreshed_this_turn
        elif cond.type == ConditionType.HAS_KEYWORD:
            cid = context.get("card_id")
            keyword = cond.params.get("keyword")
            card = self.member_db.get(cid) or self.live_db.get(cid)
            if not card:
                met = False
            elif keyword == "Blade Heart":
                # Special handling for Blade Heart icon check
                met = getattr(card, "total_blade_hearts", lambda: 0)() > 0
            else:
                met = keyword in getattr(card, "keywords", [])
        elif cond.type == ConditionType.HAS_MOVED:
            tid = context.get("card_id", player.stage[context.get("area", -1)] if context.get("area", -1) >= 0 else -1)
            met = tid in player.moved_members_this_turn if tid >= 0 else False
        elif cond.type == ConditionType.OPPONENT_ENERGY_DIFF:
            diff_val = len(self.players[1 - player.player_id].energy_zone) - len(player.energy_zone)
            req_diff = cond.params.get("diff", 0)
            comp = cond.params.get("comparison", "GE")
            if comp == "GE":
                met = diff_val >= req_diff
            elif comp == "GT":
                met = diff_val > req_diff
            elif comp == "LE":
                met = diff_val <= req_diff
            elif comp == "LT":
                met = diff_val < req_diff
            else:
                met = diff_val == req_diff
        elif cond.type == ConditionType.RARITY_CHECK:
            cid = context.get("card_id")
            card = self.member_db.get(cid) or self.live_db.get(cid)
            # Rarity is likely stored in 'rare' or 'rarity' attribute, possibly extra field
            rarity = getattr(card, "rare", getattr(card, "rarity", ""))
            met = rarity == cond.params.get("rare")
        elif cond.type == ConditionType.COUNT_LIVE_ZONE:
            met = len(player.live_zone) >= cond.params.get("min", 0)
        elif cond.type == ConditionType.COUNT_BLADES:
            req = cond.params.get("min", cond.params.get("count", 1))
            val = player.get_total_blades(self.member_db)
            comp = cond.params.get("comparison", "GE")
            if comp == "GE":
                met = val >= req
            elif comp == "GT":
                met = val > req
            elif comp == "LE":
                met = val <= req
            elif comp == "LT":
                met = val < req
            else:
                met = val == req
        elif cond.type == ConditionType.COUNT_HEARTS:
            req = cond.params.get("min", cond.params.get("count", 1))
            # Determine color index
            c_idx = -1
            c_name = cond.params.get("color")
            color_map = {"pink": 0, "red": 1, "yellow": 2, "green": 3, "blue": 4, "purple": 5}
            jp_map = {"ピンク": 0, "赤": 1, "黄": 2, "緑": 3, "青": 4, "紫": 5}

            if c_name is not None:
                if isinstance(c_name, int):
                    c_idx = c_name
                elif c_name in color_map:
                    c_idx = color_map[c_name]
                elif c_name in jp_map:
                    c_idx = jp_map[c_name]

            # Fallback: Infer from source card
            if c_idx == -1:
                scid = context.get("source_card_id", -1)
                if scid != -1:
                    scard = self.member_db.get(int(scid)) or self.live_db.get(int(scid))
                    if scard and hasattr(scard, "hearts"):
                        # Find first non-zero heart
                        for i, h in enumerate(scard.hearts):
                            if i < 6 and h > 0:
                                c_idx = i
                                break

            val = 0
            target_cid = context.get("target_card_id")
            if target_cid is not None:
                print(f"DEBUG: Checking Heart Filter. Target={target_cid} ColorIdx={c_idx} Req={req}")
                # Filter Mode: Check Candidate Card
                card = self.member_db.get(int(target_cid)) or self.live_db.get(int(target_cid))
                if card:
                    # Check hearts (Member) or required_hearts (Live)
                    check_hearts = getattr(card, "hearts", getattr(card, "required_hearts", None))
                    if check_hearts is not None:
                        if c_idx != -1 and c_idx < len(check_hearts):
                            val = check_hearts[c_idx]
                        elif c_idx == -1:
                            val = sum(check_hearts[:6])
            else:
                # Activation Mode: Check Player Stage
                active_hearts = player.get_total_hearts(self.member_db)
                if c_idx != -1:
                    val = active_hearts[c_idx]
                else:
                    val = sum(active_hearts)

            comp = cond.params.get("comparison", "GE")
            if comp == "GE":
                met = val >= req
            elif comp == "GT":
                met = val > req
            elif comp == "LE":
                met = val <= req
            elif comp == "LT":
                met = val < req
            else:
                met = val == req

        elif cond.type == ConditionType.HAS_CHOICE:
            met = True
        elif cond.type == ConditionType.OPPONENT_CHOICE:
            # Check if this card specifically was tapped/chosen by opponent this turn
            cid = context.get("card_id")
            if cid is not None:
                met = cid in player.members_tapped_by_opponent_this_turn
            else:
                met = False
        elif cond.type == ConditionType.TYPE_CHECK:
            # Check if a card is of a specific type (member/live)
            card_type = cond.params.get("card_type", "member")
            zone = cond.params.get("zone", "")

            # Determine which cards to check based on zone
            cards_to_check = []
            if zone == "DISCARDED_THIS":
                cards_to_check = context.get("discarded_cards", [])
            elif zone == "REVEALED_THIS":
                cards_to_check = self.looked_cards
            elif context.get("target_card_id") is not None:
                cards_to_check = [context["target_card_id"]]
            elif context.get("card_id") is not None:
                cards_to_check = [context["card_id"]]

            if card_type == "member":
                met = any(cid in self.member_db for cid in cards_to_check)
            elif card_type == "live":
                met = any(cid in self.live_db for cid in cards_to_check)
            else:
                met = len(cards_to_check) > 0
        elif cond.type == ConditionType.BATON:
            # Baton Pass: Check if current card replaced a specific unit/group member
            prev_cid = context.get("prev_cid", getattr(self, "prev_cid", -1))
            unit_filter = cond.params.get("unit", "")
            cost_filter = cond.params.get("filter", "")

            if prev_cid >= 0 and prev_cid in self.member_db:
                prev_card = self.member_db[prev_cid]

                # Check unit filter
                if unit_filter:
                    target_unit = Unit.from_japanese_name(unit_filter)
                    unit_match = target_unit in getattr(prev_card, "units", [])
                else:
                    unit_match = True

                # Check cost filter (e.g., COST_LT_SELF)
                if cost_filter == "COST_LT_SELF":
                    source_cid = context.get("card_id", -1)
                    if source_cid >= 0 and source_cid in self.member_db:
                        source_cost = self.member_db[source_cid].cost
                        cost_match = prev_card.cost < source_cost
                    else:
                        cost_match = False
                else:
                    cost_match = True

                met = unit_match and cost_match
            else:
                met = False
        else:
            met = True

        return met

    def _resolve_condition_opcode(self, opcode: Opcode, seg: Any, context: Dict[str, Any]) -> bool:
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
        """Execute a single quadruple from bytecode."""
        p = self.active_player
        opp_idx = 1 - p.player_id
        v = seg[1]
        a = seg[2]
        s_packed = seg[3]

        # Decode dynamic flag (Bit 6 of 'a')
        real_v = v
        if (a & 0x40) != 0:
            cond_type = ConditionType(v)
            if cond_type == ConditionType.COUNT_STAGE:
                raw_count = len([c for c in p.stage if c >= 0])
            elif cond_type == ConditionType.COUNT_HAND:
                raw_count = len(p.hand)
            elif cond_type == ConditionType.COUNT_DISCARD:
                raw_count = len(p.discard)
            elif cond_type == ConditionType.COUNT_ENERGY:
                raw_count = len(p.energy_zone)
            elif cond_type == ConditionType.COUNT_SUCCESS_LIVE:
                raw_count = len(p.success_lives)
            elif cond_type == ConditionType.COUNT_LIVE_ZONE:
                raw_count = len(p.live_zone)
            else:
                raw_count = 0

            # Decode scaling flag (Bit 5 of 'a')
            if (a & 0x20) != 0:
                # PER_X scaling: real_v = target_v * (raw_count // scaling_factor)
                scaling_factor = s_packed >> 4  # Top 4 bits of s_packed store scaling factor
                if scaling_factor > 0:
                    real_v = (s_packed & 0x0F) * (raw_count // scaling_factor)
                else:
                    real_v = 0
            else:
                real_v = raw_count

        # Decode slot/comparison
        s = s_packed & 0x0F

        # Condition Check Opcodes (Return/Jump logic usually handled in loop, but we need 'cond' state)
        # In this Python version, _resolve_pending_effect's loop needs to handle cond.
        # But for now, we only trigger effects.

        if self.verbose:
            print(f"DEBUG_OP: {opcode.name} v={v} a={a} s={s}")

        if opcode == Opcode.DRAW:
            self._draw_cards(p, real_v)
        elif opcode == Opcode.ADD_BLADES:
            p.continuous_effects.append(
                {
                    "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    "effect": Effect(EffectType.ADD_BLADES, real_v, TargetType.SELF),
                    "target_slot": s if s < 3 else -1,
                    "expiry": "TURN_END",
                }
            )
        elif opcode == Opcode.ADD_HEARTS:
            p.continuous_effects.append(
                {
                    "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    "effect": Effect(EffectType.ADD_HEARTS, real_v, TargetType.SELF, {"color": a & 0x3F}),
                    "expiry": "TURN_END",
                }
            )
        elif opcode == Opcode.GRANT_ABILITY:
            # Granting an ability (Rule 1.3.1)
            # a: attribute of granted ability (trigger type)
            # v: Index into member_db if external, or reference to current
            # For Sumire: It's usually a predefined ID or a special payload.
            # In V2 compiler, GRANT_ABILITY often carries a whole Ability object or pre-compiled bytecode.
            # But here we handle the "Legacy" or "Simple" case for Starters.

            # If it's "SELF" (s == 0), we apply to current member.
            source_id = context.get("source_card_id", -1)
            target_p = p

            # In Sumire's case, the pseudocode is:
            # EFFECT: GRANT_ABILITY(SELF, TRIGGER="CONSTANT", CONDITION="IS_ON_STAGE", EFFECT="BOOST_SCORE(1)")
            # This is compiled into Opcode 60.

            # For simplicity in this engine version, we convert it to a Continuous Effect
            # that mimics the granted ability.
            target_slot = context.get("area", -1)
            if target_slot == -1 and source_id != -1:
                # Find where source_id is on stage
                for i, cid in enumerate(p.stage):
                    if cid == source_id:
                        target_slot = i
                        break

            if target_slot != -1:
                # Create a pseudo-effect that matches the granted ability
                # Sumire grants BOOST_SCORE(1) while on stage.
                # In basic engine terms, this is just a Score Buff continuous effect.
                p.continuous_effects.append(
                    {
                        "source_card_id": source_id,
                        "effect": Effect(EffectType.BOOST_SCORE, real_v, TargetType.SELF),
                        "target_slot": target_slot,
                        "expiry": "TURN_END",  # Usually until end of turn or permanent?
                        # Starter Sumire is "This turn".
                    }
                )

        elif opcode == Opcode.LOOK_DECK:
            # Reveal top V cards (Target awareness)
            target_tp = self.players[opp_idx] if s == 2 else p  # s=2 is OPPONENT in TargetType
            if self.verbose:
                print(f"DEBUG: LOOK_DECK Target={target_tp.player_id} DeckLen={len(target_tp.main_deck)}")
            if not target_tp.main_deck:
                self._resolve_deck_refresh(target_tp)
            self.looked_cards = []
            for _ in range(v):
                if target_tp.main_deck:
                    self.looked_cards.append(target_tp.main_deck.pop(0))
            if self.verbose:
                print(f"DEBUG: LOOK_DECK Result={self.looked_cards}")
        elif opcode == Opcode.LOOK_AND_CHOOSE:
            # Trigger SLIST choice
            if self.looked_cards:
                dest = "discard" if (a & 0x0F) == 1 else "hand"
                target_pid = opp_idx if s == 2 else p.player_id
                self.pending_choices.append(
                    (
                        "SELECT_FROM_LIST",
                        {
                            "cards": self.looked_cards,
                            "count": real_v,
                            "reason": "look_and_choose",
                            "destination": dest,
                            "target_player_id": target_pid,
                            "player_id": p.player_id,
                            "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                        },
                    )
                )

        elif opcode == Opcode.TAP_OPPONENT:
            is_all = (a & 0x80) != 0
            requires_selection = (a & 0x20) != 0  # Bit 5 flag
            cost_max = v
            blades_max = a & 0x1F  # Mask out flags

            # Dynamic Resolution: If cost_max is 99, try to find context card cost
            if cost_max == 99:
                scid = context.get("source_card_id", context.get("card_id", -1))
                if scid != -1 and scid in self.member_db:
                    cost_max = self.member_db[scid].cost

            def passes_filter(slot_id):
                cid = opp.stage[slot_id]
                if cid < 0:
                    return False
                card = self.member_db[int(cid)]
                # Cost check
                if cost_max != 99 and card.cost > cost_max:
                    return False
                # Blades check
                if blades_max != 99 and card.total_blades > blades_max:
                    return False
                return True

            if is_all:
                for i in range(3):
                    if passes_filter(i):
                        opp.tapped_members[i] = True
                        opp.members_tapped_by_opponent_this_turn.add(opp.stage[i])
            else:
                # Check for interactive selection
                if requires_selection or (s == 2 and v == 1):  # s=2 is OPPONENT, v=1 count
                    choice = context.get("choice_index", -1)
                    if choice == -1:
                        # Pause for selection
                        # Create a pending choice
                        # Valid targets
                        valid_slots = [i for i in range(3) if passes_filter(i) and not opp.tapped_members[i]]

                        if valid_slots:
                            self.pending_choices.append(
                                (
                                    "TARGET_OPPONENT_MEMBER",
                                    {
                                        "player_id": self.current_player,
                                        "valid_slots": valid_slots,
                                        "effect": "tap_opponent",
                                        "pending_context": context,  # Store context to resume
                                        # "resume_opcode": opcode, ... (Python engine handles resume differently usually)
                                        # Using standard pending_choices format
                                    },
                                )
                            )
                            # In Python engine, pending_choices usually halts execution flow implicitly or explicitly?
                            # resolve_bytecode doesn't return status.
                            # We might need to ensure this halts.
                            # But standard python engine relies on pending_choices check in outer loop.
                            pass
                    else:
                        # Apply to chosen slot
                        if 0 <= choice < 3 and passes_filter(choice):
                            opp.tapped_members[choice] = True
                            opp.members_tapped_by_opponent_this_turn.add(opp.stage[choice])
                elif s < 3:  # Fallback for directed target (if s is actually a fixed slot index)
                    # Note: s=2 (Right Slot) vs s=2 (Opponent TargetType) is ambiguous without flags.
                    # This is why we added the flag.
                    # If flag is NOT set, and s < 3, assume fixed slot?
                    # But previously s=2 tapped right slot.
                    if passes_filter(s):
                        opp.tapped_members[s] = True
                        opp.members_tapped_by_opponent_this_turn.add(opp.stage[s])
        elif opcode == Opcode.ACTIVATE_MEMBER:
            if s < 3:
                p.tapped_members[s] = False
        elif opcode == Opcode.REVEAL_CARDS:
            # s=1 means reveal looking cards (usually for yel animation/trigger)
            pass
        elif opcode == Opcode.RECOVER_LIVE:
            # Trigger interactive selection instead of broken automatic recovery
            live_cards_in_discard = [cid for cid in p.discard if int(cid) in self.live_db]
            if live_cards_in_discard:
                self.pending_choices.append(
                    (
                        "SELECT_FROM_DISCARD",
                        {
                            "source_card_id": context.get("source_card_id", -1),
                            "cards": live_cards_in_discard,
                            "count": real_v,
                            "filter": "live",
                            "effect": "return_to_hand",
                            "effect_description": "回収するライブを選んでください",
                        },
                    )
                )
        elif opcode == Opcode.RECOVER_MEMBER:
            # Trigger interactive selection instead of broken automatic recovery
            member_cards_in_discard = [cid for cid in p.discard if int(cid) in self.member_db]
            if member_cards_in_discard:
                self.pending_choices.append(
                    (
                        "SELECT_FROM_DISCARD",
                        {
                            "source_card_id": context.get("source_card_id", -1),
                            "cards": member_cards_in_discard,
                            "count": real_v,
                            "filter": "member",
                            "effect": "return_to_hand",
                            "effect_description": "回収するメンバーを選んでください",
                        },
                    )
                )
        elif opcode == Opcode.SWAP_CARDS:
            # Discard v, then draw v
            for _ in range(v):
                if p.hand:
                    cid = p.hand.pop(0)
                    p.hand_added_turn.pop(0)
                    p.discard.append(cid)
            self._draw_cards(p, v)
        elif opcode == Opcode.REDUCE_COST:
            p.continuous_effects.append(
                {
                    "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    "effect": Effect(EffectType.REDUCE_COST, v, TargetType.SELF),
                    "target_slot": s if s < 3 else -1,
                    "expiry": "TURN_END",
                }
            )
        elif opcode == Opcode.REDUCE_HEART_REQ:
            p.continuous_effects.append(
                {
                    "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    "effect": Effect(EffectType.REDUCE_HEART_REQ, v, TargetType.SELF),
                    "expiry": "LIVE_END" if context.get("until") == "live_end" else "TURN_END",
                }
            )
        elif opcode == Opcode.BATON_TOUCH_MOD:
            p.continuous_effects.append(
                {
                    "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    "effect": Effect(EffectType.BATON_TOUCH_MOD, v, TargetType.SELF),
                    "expiry": "TURN_END",
                }
            )
        elif opcode == Opcode.META_RULE:
            # Handle specific meta rules that have engine impact (cheer_mod, etc)
            rule_type = context.get("type", "")
            if rule_type == "cheer_mod":
                p.continuous_effects.append(
                    {
                        "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                        "effect": Effect(EffectType.META_RULE, v, TargetType.SELF, {"type": "cheer_mod"}),
                        "expiry": "LIVE_END" if context.get("until") == "live_end" else "TURN_END",
                    }
                )
            elif rule_type == "fragment_cleanup":
                pass  # Already handled by parser filter
            else:
                p.meta_rules.add(str(rule_type))
        elif opcode == Opcode.TRANSFORM_COLOR:
            target = context.get("target", "base_hearts")
            p.continuous_effects.append(
                {
                    "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    "effect": Effect(EffectType.TRANSFORM_COLOR, v, TargetType.SELF, {"target": target, "color": a}),
                    "expiry": "LIVE_END" if context.get("until") == "live_end" else "TURN_END",
                }
            )
        elif opcode == Opcode.PLAY_MEMBER_FROM_HAND:
            # v = count, a = source_attr (e.g. Group)
            # From hand is standard, but if context says discard:
            source_zone = context.get("from", "hand")
            self.pending_choices.append(
                (
                    "TARGET_MEMBER_SLOT",
                    {
                        **context,
                        "player_id": p.player_id,
                        "effect": "place_member",
                        "source_zone": source_zone,
                        "count": v,
                        "filter_group": a if a != 0 else None,
                    },
                )
            )
        elif opcode == Opcode.FLAVOR_ACTION:
            # Trigger modal choice "What do you like?"
            self.pending_choices.append(
                (
                    "MODAL_CHOICE",
                    {
                        **context,
                        "player_id": opp_idx,
                        "title": "何が好き？",
                        "options": [
                            "チョコミント",
                            "ストロベリーフレイバー",
                            "クッキー＆クリーム",
                            "あなた",
                            "それ以外",
                        ],
                        "reason": "flavor_action",
                    },
                )
            )
        elif opcode == Opcode.ADD_TO_HAND:
            # v = count, a = source (0=looked, 1=discard, 2=deck)
            if a == 0 and self.looked_cards:
                for _ in range(v):
                    if self.looked_cards:
                        cid = self.looked_cards.pop(0)
                        p.hand.append(cid)
                        p.hand_added_turn.append(self.turn_number)
            elif a == 1:
                # Handled by RECOVER_LIVE/MEMBER usually, but for generic:
                for _ in range(v):
                    if p.discard:
                        cid = p.discard.pop()
                        p.hand.append(cid)
                        p.hand_added_turn.append(self.turn_number)
            elif a == 2:
                self._draw_cards(p, v)
        elif opcode == Opcode.BOOST_SCORE:
            p.live_score_bonus += v
        elif opcode == Opcode.ENERGY_CHARGE:
            count = v
            for _ in range(count):
                if p.main_deck:
                    cid = p.main_deck.pop(0)
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
                elif p.discard:
                    self._resolve_deck_refresh(p)
                    if p.main_deck:
                        cid = p.main_deck.pop(0)
                        p.energy_zone.append(cid)
                        p.tapped_energy[len(p.energy_zone) - 1] = False
        elif opcode == Opcode.MOVE_MEMBER:
            dest = context.get("target_slot", -1)
            if 0 <= s < 3 and 0 <= dest < 3:
                self._move_member(p, s, dest)
        elif opcode == Opcode.MOVE_TO_DISCARD:
            # v = count, a = source (1=deck_top, 2=hand, 3=energy), s = target_slot
            if a == 1:  # From Deck Top
                for _ in range(v):
                    if not p.main_deck:
                        self._resolve_deck_refresh(p)
                    if p.main_deck:
                        cid = p.main_deck.pop(0)
                        p.discard.append(cid)
            elif a == 2:  # From Hand
                for _ in range(v):
                    if p.hand:
                        cid = p.hand.pop()
                        p.hand_added_turn.pop()
                        p.discard.append(cid)
            elif a == 3:  # From Energy
                for _ in range(v):
                    if p.energy_zone:
                        cid = p.energy_zone.pop()
                        p.discard.append(cid)
            elif s == 0:  # Target SELF (Member on stage)
                scid = context.get("source_card_id", context.get("card_id", -1))
                for i in range(3):
                    if p.stage[i] == scid:
                        p.stage[i] = -1
                        p.tapped_members[i] = False
                        p.discard.append(scid)
                        break
        elif opcode == Opcode.JUMP_IF_FALSE:
            # This requires a more complex loop in _resolve_pending_effect
            # For now, standard step() might not use jumps heavily in Python mode
            pass

    def _can_pay_costs(self, player: Any, costs: List[Cost], source_area: int = -1, start_index: int = 0) -> bool:
        """Non-mutating check if a player can afford the costs."""
        total_reduction = sum(
            ce["effect"].value for ce in player.continuous_effects if ce["effect"].effect_type == EffectType.REDUCE_COST
        )

        for cost in costs[start_index:]:
            if cost.type == AbilityCostType.ENERGY:
                needed = max(0, cost.value - total_reduction)
                if player.count_untapped_energy() < needed:
                    return False
            elif cost.type == AbilityCostType.TAP_SELF:
                if source_area < 0 or player.tapped_members[source_area]:
                    return False
            elif cost.type in (AbilityCostType.SACRIFICE_SELF, AbilityCostType.RETURN_HAND):
                if source_area < 0 or player.stage[source_area] < 0:
                    return False
            elif cost.type == AbilityCostType.DISCARD_HAND:
                if len(player.hand) < cost.value:
                    return False
            elif cost.type == AbilityCostType.SACRIFICE_UNDER:
                if source_area < 0 or not player.stage_energy[source_area]:
                    return False
            elif cost.type == AbilityCostType.DISCARD_ENERGY:
                if player.count_untapped_energy() < 1:
                    return False
        return True

    def _pay_costs(self, p: "PlayerState", costs: List["Cost"], source_area: int = -1, start_index: int = 0) -> bool:
        """
        Pay costs. Returns True if paid, False if cancelled/deferred (optional).
        If optional cost is encountered, it queues a choice and returns False.
        """
        if not self._can_pay_costs(p, costs, source_area, start_index):
            return False

        total_reduction = sum(
            ce["effect"].value for ce in p.continuous_effects if ce["effect"].effect_type == EffectType.REDUCE_COST
        )

        # Default metadata for cost payment
        scid = getattr(self, "current_resolving_member_id", -1)
        choice_metadata = {"source_card_id": scid, "step_progress": "Cost"}

        for i, cost in enumerate(costs[start_index:]):
            cost_idx = start_index + i
            if cost.type == AbilityCostType.ENERGY:
                if cost.is_optional:
                    if self.verbose:
                        print(f"DEBUG: Queueing PAY_COST_OPTIONAL for player {p.player_id}")
                    # For optional energy costs, we must ask the player first
                    self.pending_choices.append(
                        (
                            "PAY_COST_OPTIONAL",
                            {
                                **choice_metadata,
                                "cost_index": cost_idx,
                                "amount": cost.value,
                                "cost_type": "energy",
                                "effect_description": f"エールを{cost.value}枚支払いますか？",
                            },
                        )
                    )
                    self.phase = Phase.RESPONSE
                    return False

                act = max(0, cost.value - total_reduction)
                tapped = 0
                for i in range(len(player.energy_zone) - 1, -1, -1):
                    if tapped >= act:
                        break
                    if not player.tapped_energy[i]:
                        player.tapped_energy[i] = True
                        tapped += 1
            elif cost.type == AbilityCostType.TAP_SELF:
                if source_area >= 0:
                    player.tapped_members[source_area] = True
            elif cost.type == AbilityCostType.SACRIFICE_SELF:
                if source_area >= 0 and player.stage[source_area] >= 0:
                    player.discard.append(player.stage[source_area])
                    player.stage[source_area] = -1
                    player.energy_deck.extend(player.stage_energy[source_area])
                    player.stage_energy[source_area] = []
                    player.tapped_members[source_area] = False
                    player.members_played_this_turn[source_area] = False
            elif cost.type == AbilityCostType.SACRIFICE_UNDER:
                if source_area >= 0:
                    player.energy_deck.extend(player.stage_energy[source_area])
                    player.stage_energy[source_area] = []
            elif cost.type == AbilityCostType.DISCARD_ENERGY:
                for i in range(len(player.energy_zone) - 1, -1, -1):
                    if not player.tapped_energy[i]:
                        player.tapped_energy[i] = True
                        break
            elif cost.type == AbilityCostType.RETURN_HAND:
                if source_area >= 0 and player.stage[source_area] >= 0:
                    player.hand.append(player.stage[source_area])
                    player.stage[source_area] = -1
                    player.energy_deck.extend(player.stage_energy[source_area])
                    player.stage_energy[source_area] = []
            elif cost.type == AbilityCostType.DISCARD_HAND:
                params = {
                    "reason": "cost",
                    "effect": "discard",
                    "is_optional": cost.is_optional,
                    "cost_index": cost_idx,
                    "count": cost.value,
                }
                if hasattr(cost, "params") and cost.params:
                    params.update(cost.params)
                self.pending_choices.append(("TARGET_HAND", {**choice_metadata, **params}))
                return False  # Stop and wait for choice
            # Add cost_index to other choices as well if implemented
            elif cost.type in (AbilityCostType.TAP_MEMBER, AbilityCostType.REST_MEMBER):
                # Pending implementation of choices for these types (if any)
                pass
        return True

    def _handle_choice(self, action: int) -> None:
        if not self.pending_choices:
            return
        choice_type, params = self.pending_choices.pop(0)
        # print(f"DEBUG: _handle_choice popped: {choice_type} Action: {action}")

        # Check if this choice was for a cost payment of a pending activation
        is_cost_payment = params.get("reason") == "cost" or (
            self.pending_activation
            and choice_type
            in (
                "TARGET_HAND",
                "DISCARD_SELECT",
                "TARGET_MEMBER_SLOT",
                "TARGET_MEMBER",
                "TARGET_LIVE",
                "TARGET_DISCARD",
                "TARGET_DECK",
                "TARGET_REMOVED",
                "TARGET_SUCCESS_LIVES",
                "TARGET_ENERGY_ZONE",
                "TARGET_ENERGY_DECK",
                "PAY_COST_OPTIONAL",
            )
        )
        if self.pending_activation:
            pass

        # Default metadata for choice chaining
        choice_metadata = params.copy()
        if "source_card_id" not in choice_metadata:
            choice_metadata["source_card_id"] = -1
        if "step_progress" not in choice_metadata:
            choice_metadata["step_progress"] = "?"

        p_idx = params.get("player_id", self.current_player)
        p = self.players[p_idx]
        opp_idx = 1 - p_idx
        opp = self.players[opp_idx]
        cost_paid = False

        # Store the choice answer for MODAL_ANSWER condition
        if 580 <= action < 586:  # COLOR_SELECT
            self.last_choice_answer = action - 580
        elif 800 <= action < 810:  # MODAL_CHOICE
            self.last_choice_answer = action - 800
        else:
            self.last_choice_answer = action  # Default fallback

        if choice_type == "TARGET_HAND":
            idx = action - 500
            if 0 <= idx < len(p.hand):
                cid = p.hand[idx]
                # Filter: Don't allow energy cards (ID>=2000) to be selected for non-energy-charge actions if needed
                # But here we just proceed.

                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True

                cid = p.hand.pop(idx)
                if idx < len(p.hand_added_turn):
                    p.hand_added_turn.pop(idx)

                eff = params.get("effect")
                if eff == "discard":
                    p.discard.append(cid)
                    if self.verbose:
                        print(f"DEBUG: TARGET_HAND discarded card {cid}. Discard size now {len(p.discard)}")
                elif eff == "energy_charge":
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
                elif eff == "place_under":
                    target = params.get("target_area", -1)
                    if target >= 0:
                        p.add_stage_energy(target, cid)
                elif eff == "place_member":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = cid
                    else:
                        p.discard.append(cid)  # Fallback
                elif eff == "place_live":
                    p.live_zone.append(cid)
                    p.live_zone_revealed.append(True)
                elif eff == "place_energy":
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
                elif eff == "place_energy_to_stage_energy":
                    target = params.get("target_area", 0)
                    p.add_stage_energy(target, cid)
                elif eff == "place_member_to_stage_energy":
                    target = params.get("target_area", 0)
                    p.add_stage_energy(target, cid)
                elif eff == "place_live_to_stage_energy":
                    target = params.get("target_area", 0)
                    p.add_stage_energy(target, cid)
                elif eff == "place_energy_to_discard":
                    p.discard.append(cid)
                elif eff == "place_member_to_discard":
                    p.discard.append(cid)
                elif eff == "place_live_to_discard":
                    p.discard.append(cid)
                elif eff == "place_energy_to_success":
                    p.success_lives.append(cid)
                elif eff == "place_member_to_success":
                    p.success_lives.append(cid)
                elif eff == "place_live_to_success":
                    p.success_lives.append(cid)
                elif eff == "place_energy_to_removed":
                    self.removed_cards.append(cid)
                elif eff == "place_member_to_removed":
                    self.removed_cards.append(cid)
                elif eff == "place_live_to_removed":
                    self.removed_cards.append(cid)

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_HAND", params))

        elif choice_type == "TARGET_LIVE":
            idx = action - 820
            if 0 <= idx < len(p.live_zone):
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True
                cid = p.live_zone.pop(idx)
                if idx < len(p.live_zone_revealed):
                    p.live_zone_revealed.pop(idx)

                eff = params.get("effect")
                if eff == "discard":
                    p.discard.append(cid)
                elif eff == "remove":
                    self.removed_cards.append(cid)
                elif eff == "return_to_hand":
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
                elif eff == "return_to_deck":
                    p.main_deck.append(cid)
                    random.shuffle(p.main_deck)
                elif eff == "return_to_success":
                    p.success_lives.append(cid)

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_LIVE", params))

        elif choice_type == "SELECT_FROM_DISCARD" or choice_type == "TARGET_DISCARD":
            idx = action - 660
            source_list = params.get("cards", p.discard)
            if 0 <= idx < len(source_list):
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True

                cid = source_list[idx]
                if cid in p.discard:
                    p.discard.remove(cid)  # Removed from discard responsibly
                else:
                    # Fallback for sync issues
                    if 0 <= idx < len(p.discard):
                        cid = p.discard.pop(idx)

                eff = params.get("effect")
                if eff == "place_member":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = cid
                    else:
                        p.discard.append(cid)
                elif eff == "place_live":
                    p.live_zone.append(cid)
                    p.live_zone_revealed.append(True)
                elif eff == "place_energy":
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
                elif eff == "return_to_deck":
                    p.main_deck.append(cid)
                    random.shuffle(p.main_deck)
                elif eff == "return_to_hand":
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
                elif eff == "return_to_success":
                    p.success_lives.append(cid)
                elif eff == "return_to_removed":
                    self.removed_cards.append(cid)

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_DISCARD", params))

        elif choice_type == "TARGET_DECK" or choice_type == "SELECT_FROM_LIST":
            idx = action - 600
            if 0 <= idx < len(p.main_deck) or choice_type == "SELECT_FROM_LIST":
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True

                # For SELECT_FROM_LIST, 'p.main_deck' isn't necessarily the source,
                # but we check the bounds of the provided cards list.
                source_list = params.get("cards", p.main_deck)
                if 0 <= idx < len(source_list):
                    cid = source_list.pop(idx) if choice_type != "SELECT_FROM_LIST" else source_list[idx]

                eff = params.get("effect")
                if eff == "place_member":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = cid
                    else:
                        p.discard.append(cid)
                elif eff == "place_live":
                    p.live_zone.append(cid)
                    p.live_zone_revealed.append(True)
                elif eff == "place_energy":
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
                elif eff == "return_to_hand":
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
                elif eff == "return_to_discard":
                    p.discard.append(cid)
                elif eff == "return_to_success":
                    p.success_lives.append(cid)
                elif eff == "return_to_removed":
                    self.removed_cards.append(cid)

                # Shuffle after deck manipulation
                random.shuffle(p.main_deck)

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_DECK", params))

        elif choice_type == "TARGET_REMOVED":
            idx = action - 850
            if 0 <= idx < len(self.removed_cards):
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True
                cid = self.removed_cards.pop(idx)

                eff = params.get("effect")
                if eff == "return_to_deck":
                    p.main_deck.append(cid)
                    random.shuffle(p.main_deck)
                elif eff == "return_to_hand":
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
                elif eff == "return_to_discard":
                    p.discard.append(cid)
                elif eff == "return_to_success":
                    p.success_lives.append(cid)
                elif eff == "place_member":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = cid
                    else:
                        p.discard.append(cid)
                elif eff == "place_live":
                    p.live_zone.append(cid)
                    p.live_zone_revealed.append(True)
                elif eff == "place_energy":
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_REMOVED", params))

        elif choice_type == "TARGET_SUCCESS_LIVES":
            idx = action - 760
            if 0 <= idx < len(p.success_lives):
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True
                cid = p.success_lives.pop(idx)

                eff = params.get("effect")
                if eff == "place_energy":
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
                elif eff == "discard":
                    p.discard.append(cid)
                elif eff == "remove":
                    self.removed_cards.append(cid)
                elif eff == "return_to_hand":
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
                elif eff == "return_to_deck":
                    p.main_deck.append(cid)
                    random.shuffle(p.main_deck)
                elif eff == "return_to_discard":
                    p.discard.append(cid)
                elif eff == "place_member":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = cid
                    else:
                        p.discard.append(cid)
                elif eff == "place_live":
                    p.live_zone.append(cid)
                    p.live_zone_revealed.append(True)

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_SUCCESS_LIVES", params))

        elif choice_type == "TARGET_ENERGY_ZONE":
            idx = action - 830
            if 0 <= idx < len(p.energy_zone):
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True
                cid = p.energy_zone.pop(idx)
                if idx < len(p.tapped_energy):
                    p.tapped_energy = np.delete(p.tapped_energy, idx)  # NumPy delete
                    # Re-pad to 64
                    p.tapped_energy = np.pad(p.tapped_energy, (0, 64 - len(p.tapped_energy)), "constant")

                eff = params.get("effect")
                if eff == "return_to_deck":
                    p.main_deck.append(cid)
                    random.shuffle(p.main_deck)
                elif eff == "return_to_hand":
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
                elif eff == "discard":
                    p.discard.append(cid)
                elif eff == "remove":
                    self.removed_cards.append(cid)
                elif eff == "return_to_success":
                    p.success_lives.append(cid)
                elif eff == "place_member":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = cid
                    else:
                        p.discard.append(cid)
                elif eff == "place_live":
                    p.live_zone.append(cid)
                    p.live_zone_revealed.append(True)

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_ENERGY_ZONE", params))

        elif choice_type == "TARGET_ENERGY_DECK":
            idx = action - 600  # Generic list range is fine for energy deck search
            if 0 <= idx < len(p.energy_deck):
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True
                cid = p.energy_deck.pop(idx)

                eff = params.get("effect")
                if eff == "return_to_hand":
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
                elif eff == "return_to_discard":
                    p.discard.append(cid)
                elif eff == "return_to_success":
                    p.success_lives.append(cid)
                elif eff == "return_to_removed":
                    self.removed_cards.append(cid)
                elif eff == "place_energy":
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
                elif eff == "place_member":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = cid
                    else:
                        p.discard.append(cid)
                elif eff == "place_live":
                    p.live_zone.append(cid)
                    p.live_zone_revealed.append(True)

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("TARGET_ENERGY_DECK", params))

        elif choice_type == "PAY_COST_OPTIONAL":
            # Action 570 for Yes, 0 for No
            if action == 570:
                amount = params.get("amount", 0)
                # Deduct energy
                tapped = 0
                for i in range(len(p.energy_zone) - 1, -1, -1):
                    if not p.tapped_energy[i]:
                        p.tapped_energy[i] = True
                        tapped += 1
                        if tapped >= amount:
                            break
                cost_paid = True
            else:
                # Declined optional cost
                cost_paid = False
                # The resumption logic at bottom of _handle_choice will see cost_paid=False
                # and clear pending_activation/effects.

        elif choice_type in ("TARGET_MEMBER", "TARGET_MEMBER_SLOT"):
            area = action - 560
            if 0 <= area < 3:
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True
                if params.get("effect") == "buff":
                    teff = params.get("target_effect")
                    if teff:
                        p.continuous_effects.append({"effect": teff, "target_slot": area, "expiry": "TURN_END"})
                elif params.get("effect") == "activate":
                    p.tapped_members[area] = False
                elif params.get("effect") == "tap":
                    p.tapped_members[area] = True
                elif params.get("effect") == "tap_self_chosen":
                    # Self-tap chosen by opponent ability (Nico/Tomari logic fallback if self-choice)
                    p.tapped_members[area] = True
                    p.members_tapped_by_opponent_this_turn.add(p.stage[area])
                elif params.get("effect") == "rest":
                    p.rested_members[area] = True
                elif params.get("reason") == "position_change":
                    step = params.get("step", "source")
                    if step == "source" and p.stage[area] >= 0:
                        self.pending_choices.insert(
                            0,
                            (
                                "TARGET_MEMBER_SLOT",
                                {**choice_metadata, "reason": "position_change", "step": "dest", "source": area},
                            ),
                        )
                    elif step == "dest":
                        src = params.get("source")
                        if src is not None and src != area:
                            self._move_member(p, src, area)
                # Handle return/discard/remove cost types targeting members
                elif params.get("effect") == "return_to_hand":
                    if p.stage[area] >= 0:
                        p.hand.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.stage_energy[area].clear()
                elif params.get("effect") == "discard_member":
                    if p.stage[area] >= 0:
                        p.discard.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.stage_energy[area].clear()
                elif params.get("effect") == "remove_member":
                    if p.stage[area] >= 0:
                        self.removed_cards.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.stage_energy[area].clear()
                elif params.get("effect") == "return_to_deck":
                    if p.stage[area] >= 0:
                        p.main_deck.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.stage_energy[area].clear()
                        random.shuffle(p.main_deck)
                elif params.get("effect") == "return_to_success":
                    if p.stage[area] >= 0:
                        p.success_lives.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.stage_energy[area].clear()
                elif params.get("effect") == "return_to_discard":
                    if p.stage[area] >= 0:
                        p.discard.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.stage_energy[area].clear()
                elif params.get("effect") == "return_to_removed":
                    if p.stage[area] >= 0:
                        self.removed_cards.append(p.stage[area])
                        p.stage[area] = -1
                        p.tapped_members[area] = False
                        p.stage_energy[area].clear()

        elif choice_type == "DISCARD_SELECT":
            idx = action - 500
            if 0 <= idx < len(p.hand):
                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True
                cid = p.hand.pop(idx)
                if idx < len(p.hand_added_turn):
                    p.hand_added_turn.pop(idx)
                p.discard.append(cid)

                if params.get("draw_on_discard") and params.get("count", 1) <= 1:
                    self._draw_cards(p, params.get("total_count", 1))

                if params.get("count", 1) > 1:
                    params["count"] -= 1
                    self.pending_choices.insert(0, ("DISCARD_SELECT", params))
        elif choice_type == "MODAL":
            opt = action - 570
            opts = params.get("options", [])
            if 0 <= opt < len(opts):
                choice = opts[opt]
                if choice == "チョコミント":
                    self.pending_choices.insert(
                        0, ("TARGET_HAND", {**choice_metadata, "effect": "discard", "player": "active"})
                    )
                elif choice == "あなた":
                    (self._draw_cards(p, 1), self._draw_cards(opp, 1))
                elif choice == "その他":
                    self.pending_choices.append(
                        (
                            "CHOOSE_FORMATION",
                            {
                                **choice_metadata,
                            },
                        )
                    )
        elif choice_type == "TARGET_OPPONENT_MEMBER":
            area = action - 600
            if 0 <= area < 3 and opp.stage[area] >= 0:
                if params.get("effect") == "tap":
                    opp.tapped_members[area] = True
                    opp.members_tapped_by_opponent_this_turn.add(opp.stage[area])
        elif choice_type == "SELECT_MODE":
            opt = action - 570

            # Handle Bytecode Options
            bytecodes = params.get("options_bytecode")
            if bytecodes and 0 <= opt < len(bytecodes):
                self.pending_effects.insert(0, bytecodes[opt])
                return

            opts = params.get("options", [])
            if 0 <= opt < len(opts):
                source_id = params.get("source_card_id", -1)
                opt_effects = opts[opt]
                total = len(opt_effects)
                for i, eff in enumerate(reversed(opt_effects)):
                    # Wrap in ResolvingEffect to preserve metadata
                    self.pending_effects.insert(0, ResolvingEffect(copy.copy(eff), source_id, total - i, total))
        elif choice_type == "SELECT_FROM_LIST":
            cards = params.get("cards", [])
            idx = action - 600
            target_player_id = params.get("target_player_id", p.player_id)
            tp = self.players[target_player_id]

            # Handle "pass" (action 0) for optional selections like "any number"
            if action == 0 and params.get("is_optional", False):
                reason = params.get("reason")
                if reason == "look_and_reorder":
                    # Selection finished via pass.
                    # 1. Discard remaining looked cards
                    if self.looked_cards:
                        for c in self.looked_cards:
                            p.discard.append(c)
                        self.looked_cards = []

                    # 2. Trigger reordering if enabled
                    if params.get("reorder") and hasattr(self, "_reorder_staged_cards") and self._reorder_staged_cards:
                        self.pending_choices.insert(
                            0,
                            (
                                "SELECT_ORDER",
                                {
                                    "cards": self._reorder_staged_cards.copy(),
                                    "ordered": [],
                                    "position": "top",
                                    "player_id": p.player_id,
                                },
                            ),
                        )
                        self._reorder_staged_cards = []
                    elif hasattr(self, "_reorder_staged_cards") and self._reorder_staged_cards:
                        # No reorder, just put back
                        for c in reversed(self._reorder_staged_cards):
                            p.main_deck.insert(0, c)
                        self._reorder_staged_cards = []
                    return

                elif reason == "look_and_choose":
                    if self.looked_cards:
                        if params.get("destination") == "discard":
                            # Put back on owner's deck
                            for c in reversed(self.looked_cards):
                                tp.main_deck.insert(0, c)
                        else:
                            # Standard: Discard rest
                            tp.discard.extend(self.looked_cards)
                        self.looked_cards = []

                return  # Exit early for other optional reasons

            if 0 <= idx < len(cards):
                sel = cards.pop(idx)

                if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                    cost_paid = True

                reason = params.get("reason")

                # Logic for adding to hand (Shioriko, Search, etc.)
                if reason in ("look_and_choose", "search_deck"):
                    dest = params.get("destination", params.get("to", "hand"))
                    if dest == "discard":
                        tp.discard.append(sel)
                    else:
                        p.hand.append(sel)
                        p.hand_added_turn.append(self.turn_number)

                # Logic for staging cards for deck top reordering
                elif reason == "look_and_reorder":
                    if not hasattr(self, "_reorder_staged_cards"):
                        self._reorder_staged_cards = []
                    self._reorder_staged_cards.append(sel)
                    # Remove from looked_cards to prevent double-discard
                    if sel in self.looked_cards:
                        self.looked_cards.remove(sel)

                    any_number = params.get("any_number", False)
                    reorder = params.get("reorder", False)

                    # Continue selection if cards remain and any_number is True
                    if any_number and cards:
                        self.pending_choices.insert(
                            0,
                            (
                                "SELECT_FROM_LIST",
                                {
                                    **params,
                                    "cards": cards,
                                },
                            ),
                        )
                        return  # Wait for next selection

                    # Selection done. Discard remaining looked_cards.
                    if self.looked_cards:
                        for c in self.looked_cards:
                            p.discard.append(c)
                        self.looked_cards = []

                    # Trigger reordering if enabled and we have staged cards
                    if reorder and self._reorder_staged_cards:
                        self.pending_choices.insert(
                            0,
                            (
                                "SELECT_ORDER",
                                {
                                    "cards": self._reorder_staged_cards.copy(),
                                    "ordered": [],
                                    "position": "top",
                                    "player_id": p.player_id,
                                },
                            ),
                        )
                        self._reorder_staged_cards = []
                    elif self._reorder_staged_cards:
                        # No reorder, just put them back on top in selection order
                        for c in reversed(self._reorder_staged_cards):
                            p.main_deck.insert(0, c)
                        self._reorder_staged_cards = []
                    return  # Exit early

                if self.looked_cards:
                    # Discard others ONLY if they were looked at (not search)
                    if reason == "look_and_choose":
                        if params.get("destination") == "discard":
                            # Return rest to owner's deck
                            for c in reversed(cards):
                                tp.main_deck.insert(0, c)
                        else:
                            # Discard rest
                            tp.discard.extend(cards)
                    self.looked_cards = []

                if reason == "search_deck":
                    if sel in p.main_deck:
                        p.main_deck.remove(sel)
                    if params.get("shuffle"):
                        random.shuffle(p.main_deck)
                elif reason == "activate_energy":
                    found_idx = -1
                    for i, ecid in enumerate(p.energy_zone):
                        if ecid == sel and p.tapped_energy[i]:
                            found_idx = i
                            break

                    if found_idx >= 0:
                        p.tapped_energy[found_idx] = False
                elif reason == "place_under_from_energy":
                    target = params.get("target_area", -1)
                    if target >= 0:
                        # Sync tapped state (sel was already popped from energy_zone via cards reference at idx)
                        if isinstance(p.tapped_energy, (list, np.ndarray)):
                            if isinstance(p.tapped_energy, np.ndarray):
                                p.tapped_energy[idx : len(p.energy_zone)] = p.tapped_energy[
                                    idx + 1 : len(p.energy_zone) + 1
                                ]
                            else:
                                p.tapped_energy.pop(idx)
                        p.add_stage_energy(target, sel)

                if params.get("count", 1) > 1 and reason == "activate_energy":
                    # Handle multi-select for energy activation
                    rem_cards = params.get("cards")
                    if sel in rem_cards:
                        rem_cards.remove(sel)
                    if rem_cards:
                        params["count"] -= 1
                        params["cards"] = rem_cards
                        self.pending_choices.insert(0, ("SELECT_FROM_LIST", params))
        elif choice_type == "SELECT_FROM_DISCARD":
            cards = params.get("cards", [])
            idx = action - 660
            if 0 <= idx < len(cards):
                sel = int(cards[idx])  # Cast to int to ensure match with discard list
                if sel in p.discard:
                    p.discard.remove(sel)
                    dest = params.get("destination", "hand")
                    if dest == "hand":
                        # Tuple unpacking was used but implies side effects in list construction??
                        # Logic: (p.hand.append(sel), p.hand_added_turn.append(self.turn_number))
                        # Better:
                        p.hand.append(sel)
                        p.hand_added_turn.append(self.turn_number)
                    elif dest == "stage":
                        area = next((i for i in range(3) if p.stage[i] < 0), -1)
                        if area >= 0:
                            p.stage[area] = sel
                        else:
                            p.hand.append(sel)
                            p.hand_added_turn.append(self.turn_number)
                    if params.get("count", 1) > 1:
                        rem = [c for c in cards if int(c) != sel and int(c) in p.discard]
                        if rem:
                            (
                                params.update({"cards": rem, "count": params["count"] - 1}),
                                self.pending_choices.insert(0, ("SELECT_FROM_DISCARD", params)),
                            )
        elif choice_type == "CHOOSE_FORMATION":
            mems = [(i, cid) for i, cid in enumerate(p.stage) if cid >= 0]
            if mems:
                self.pending_choices.append(
                    (
                        "SELECT_FORMATION_SLOT",
                        {**choice_metadata, "slot_index": 0, "available_members": mems, "new_stage": [-1, -1, -1]},
                    )
                )
        elif choice_type == "SELECT_FORMATION_SLOT":
            slot = params.get("slot_index", 0)
            avail = params.get("available_members", [])
            nstage = params.get("new_stage", [-1, -1, -1])
            idx = action - 700
            if 0 <= idx < len(avail):
                sel = avail.pop(idx)
                nstage[slot] = sel[1]
                if slot + 1 < 3 and avail:
                    self.pending_choices.insert(
                        0,
                        (
                            "SELECT_FORMATION_SLOT",
                            {
                                **choice_metadata,
                                "slot_index": slot + 1,
                                "available_members": avail,
                                "new_stage": nstage,
                            },
                        ),
                    )
                else:
                    for k in range(slot + 1, 3):
                        nstage[k] = -1
                    np.copyto(p.stage, nstage)
        elif choice_type == "COLOR_SELECT":
            color_idx = action - 580

            if 0 <= color_idx < 6:
                # Update pending ADD_HEARTS effects that depend on choice
                for i, pe in enumerate(self.pending_effects):
                    eff = pe.effect if hasattr(pe, "effect") else pe

                    if eff.effect_type == EffectType.ADD_HEARTS and eff.params.get("color") == "choice":
                        new_params = eff.params.copy()
                        new_params["color"] = color_idx
                        new_eff = Effect(EffectType.ADD_HEARTS, eff.value, eff.target, new_params)

                        if hasattr(pe, "effect"):
                            pe.effect = new_eff
                        else:
                            self.pending_effects[i] = new_eff
                        break
        elif choice_type == "SELECT_SWAP_SOURCE":
            idx = action - 600
            if 0 <= idx < len(params.get("cards", [])):
                self.pending_choices.insert(0, ("SELECT_SWAP_TARGET", {"card_to_hand": params["cards"][idx]}))
        elif choice_type == "SELECT_SWAP_TARGET":
            idx = action - 500
            if 0 <= idx < len(p.hand):
                clive = p.hand[idx]
                chand = params.get("card_to_hand")
                if chand in p.success_lives:
                    (p.success_lives.remove(chand), p.hand.append(chand), p.hand_added_turn.append(self.turn_number))
                if clive in p.hand:
                    hidx = p.hand.index(clive)
                    if hidx < len(p.hand_added_turn):
                        p.hand_added_turn.pop(hidx)
                    p.hand.remove(clive)
                    p.success_lives.append(clive)
        elif choice_type == "SELECT_SUCCESS_LIVE":
            print(f"DEBUG: SELECT_SUCCESS_LIVE resolution. Action: {action}")
            idx = action - 600
            cards = params.get("cards", [])
            print(f"DEBUG: cards in params: {cards}, calculated idx: {idx}")
            if 0 <= idx < len(cards):
                sel = cards[idx]
                tplayer = self.players[params.get("player_id", 0)]
                print(f"DEBUG: card selected: {sel}, player {tplayer.player_id}, passed_lives: {tplayer.passed_lives}")
                if sel in tplayer.passed_lives:
                    tplayer.success_lives.append(sel)
                    tplayer.passed_lives.remove(sel)
                    print(f"DEBUG: card moved. success_lives now: {tplayer.success_lives}")
                    # Discard others
                    if tplayer.passed_lives:
                        if hasattr(self, "log_rule"):
                            self.log_rule(
                                "Rule 8.4",
                                f"Player {tplayer.player_id} discarded other successful lives: {len(tplayer.passed_lives)} cards",
                            )
                        tplayer.discard.extend(tplayer.passed_lives)
                        tplayer.passed_lives = []
                    print(f"DEBUG: passed_lives cleared: {tplayer.passed_lives}")
                else:
                    print(f"DEBUG: card {sel} NOT found in passed_lives")
            else:
                print(f"DEBUG: idx {idx} out of range for cards")
        elif choice_type == "CONTINUE_LIVE_RESULT":
            if hasattr(self, "_finish_live_result"):
                self._finish_live_result()
            return  # Don't run re-entrancy hook after finishing phase
        elif choice_type == "CHOOSE_TRIGGER":
            tidx = action - 590
            ids = params.get("indices", [])
            if 0 <= tidx < len(ids):
                pid, ab, ctx = self.triggered_abilities.pop(ids[tidx])
                self._play_automatic_ability(pid, ab, ctx)
        elif choice_type == "SELECT_ORDER":
            idx = action - 700
            cards = params["cards"]
            if 0 <= idx < len(cards):
                params["ordered"].append(cards.pop(idx))
                if cards:
                    self.pending_choices.insert(0, ("SELECT_ORDER", params))
                else:
                    if params["position"] == "top":
                        for c in reversed(params["ordered"]):
                            p.main_deck.insert(0, c)
                    else:
                        p.main_deck.extend(params["ordered"])
        elif choice_type == "MODAL_CHOICE":
            # Modal choices usually just set last_choice_answer (handled at top of _handle_choice)
            pass

        # Resume pending activation if deferred (from cost payment)
        if is_cost_payment and self.pending_activation:
            if cost_paid:
                pa = self.pending_activation
                ability = pa["ability"]
                ctx = pa["context"]
                abi_key = pa["abi_key"]

                # Check if we need to pay MORE costs
                paid_index = params.get("cost_index", -1)

                # If we have a valid index, resume from next
                all_costs_paid = True
                if paid_index >= 0 and paid_index + 1 < len(ability.costs):
                    p = self.active_player
                    area = ctx.get("area", -1)
                    if not self._pay_costs(p, ability.costs, source_area=area, start_index=paid_index + 1):
                        all_costs_paid = False

                if all_costs_paid:
                    # Use ResolvingEffect to preserve source metadata (matching _play_automatic_ability)
                    cid = ctx.get("source_card_id", ctx.get("card_id", -1))
                    total = len(ability.effects)
                    for i, phase_effect in enumerate(reversed(ability.effects)):
                        step = total - i
                        eff_copy = copy.copy(phase_effect)
                        self.pending_effects.insert(0, ResolvingEffect(eff_copy, cid, step, total))

                    p = self.active_player
                    if ability.is_once_per_turn:
                        p.used_abilities.add(abi_key)

                    # Clear pending activation ONLY when fully paid and effects queued
                    self.pending_activation = None

                    while self.pending_effects and not self.pending_choices:
                        self._resolve_pending_effect(0, context=ctx)
                else:
                    # Still paying costs (waiting for next choice)
                    pass
            else:
                # Cost not yet fully paid - check if there are more cost choices pending
                # Only clear if there are no more cost choices (i.e., cost was declined)
                if not self.pending_choices or self.pending_choices[0][1].get("reason") != "cost":
                    self.pending_activation = None

        if self.pending_effects and not self.pending_choices:
            # Propagate the choice metadata back as context to preserve source_card_id for next effects
            self._resolve_pending_effect(0, context=params)

        # Phase 8 Re-entrancy: If we are in Live Result phase and just finished a selection,
        # we might need to add the "Continue" button or handle the next winner's selection.
        if not self.pending_choices and not self.pending_effects and self.phase == Phase.LIVE_RESULT:
            if hasattr(self, "_do_live_result"):
                self._do_live_result()

    def _move_member(self, player: Any, from_idx: int, to_idx: int) -> None:
        if from_idx == to_idx:
            return
        c1, c2 = player.stage[from_idx], player.stage[to_idx]
        if c1 >= 0:
            player.moved_members_this_turn.add(c1)
        if c2 >= 0:
            player.moved_members_this_turn.add(c2)
        player.stage[from_idx], player.stage[to_idx] = player.stage[to_idx], player.stage[from_idx]
        player.stage_energy[from_idx], player.stage_energy[to_idx] = (
            player.stage_energy[to_idx],
            player.stage_energy[from_idx],
        )
        player.tapped_members[from_idx], player.tapped_members[to_idx] = (
            player.tapped_members[to_idx],
            player.tapped_members[from_idx],
        )
