from __future__ import annotations

import random
from typing import Any, Dict, List

import numpy as np

from engine.game.effects.metadata import resolve_source_metadata
from engine.game.effects.zone_actions import move_stage_card
from engine.models.ability import Ability, AbilityCostType, ConditionType, Effect, EffectType, TargetType, TriggerType


def handle_cost(game: Any, player_id: int, ability: Ability, context: Dict[str, Any] = {}) -> bool:
    self = game
    """Handle ability costs (Rule 9.7.2). Returns True if cost paid/resolved."""
    p = self.players[player_id]
    cid = context.get("source_card_id")

    # Use new helper to ensure consistent metadata
    cost_metadata = resolve_source_metadata(self, cid, ability, reason="cost")
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
                            "effect_description": "繧ｿ繝・・縺吶ｋ繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ{cost.value}譫壽昏縺ｦ縺ｦ縺上□縺輔＞",
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
                        "effect_description": f"エネルギーを{cost.value}枚タップしてください",
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
                            "effect_description": "繝ｬ繧ｹ繝医☆繧九Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                            "is_optional": False,
                        },
                    )
                )
            return False
        elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_HAND:
            if cost.target == TargetType.MEMBER_SELF:
                area = context.get("area", -1)
                if area < 0 or not move_stage_card(self, p, area, "hand"):
                    return False
            else:
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **cost_metadata,
                            "effect": "return_to_hand",
                            "effect_description": "謇区惆縺ｫ謌ｻ縺吶Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                            "is_optional": False,
                        },
                    )
                )
            return False
        elif cost.cost_type == AbilityCostType.DISCARD_MEMBER:
            if cost.target == TargetType.MEMBER_SELF:
                area = context.get("area", -1)
                if area < 0 or not move_stage_card(self, p, area, "discard"):
                    return False
            else:
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **cost_metadata,
                            "effect": "discard_member",
                            "effect_description": "謐ｨ縺ｦ繧九Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
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
                            "effect_description": f"繝ｩ繧､繝悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽昏縺ｦ縺ｦ縺上□縺輔＞",
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
                            "effect_description": f"繝ｩ繧､繝悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫夐勁螟悶＠縺ｦ縺上□縺輔＞",
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
                if area < 0 or not move_stage_card(self, p, area, "removed"):
                    return False
            else:
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **cost_metadata,
                            "effect": "remove_member",
                            "effect_description": "髯､螟悶☆繧九Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
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
                            "effect_description": f"繝ｩ繧､繝悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝ｩ繧､繝悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壹ョ繝・く縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                if area < 0 or not move_stage_card(self, p, area, "deck"):
                    return False
            else:
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **cost_metadata,
                            "effect": "return_to_deck",
                            "effect_description": "繝・ャ繧ｭ縺ｫ謌ｻ縺吶Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ{cost.value}譫壹ョ繝・く縺ｫ謌ｻ縺励※縺上□縺輔＞",
                            "is_optional": False,
                            "count": cost.value,
                        },
                    )
                )
            if len(self.removed_cards) > 0:
                self.pending_choices.append(
                    (
                        "TARGET_REMOVED",
                        {
                            **cost_metadata,
                            "effect": "return_to_hand",
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨お繝ｼ繝ｫ繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫壽昏縺ｦ縺ｦ縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫夐勁螟悶＠縺ｦ縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫壹ョ繝・く縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Γ繝ｳ繝舌・繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Λ繧､繝悶ｒ{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ{cost.value}譫壹ョ繝・く縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽昏縺ｦ縺ｦ縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壹ョ繝・く縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壽昏縺ｦ縺ｦ縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫夐勁螟悶＠縺ｦ縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壹お繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨お繝ｼ繝ｫ繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Γ繝ｳ繝舌・繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Λ繧､繝悶ｒ{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                if area < 0 or not move_stage_card(self, p, area, "success"):
                    return False
            else:
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **cost_metadata,
                            "effect": "return_to_success",
                            "effect_description": "謌仙粥繝ｩ繧､繝悶↓謌ｻ縺吶Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                            "is_optional": False,
                        },
                    )
                )
            return False
        elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_DISCARD:
            if cost.target == TargetType.MEMBER_SELF:
                area = context.get("area", -1)
                if area < 0 or not move_stage_card(self, p, area, "discard"):
                    return False
            else:
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **cost_metadata,
                            "effect": "return_to_discard",
                            "effect_description": "謐ｨ縺ｦ譛ｭ縺ｫ謌ｻ縺吶Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                            "is_optional": False,
                        },
                    )
                )
            return False
        elif cost.cost_type == AbilityCostType.RETURN_MEMBER_TO_REMOVED:
            if cost.target == TargetType.MEMBER_SELF:
                area = context.get("area", -1)
                if area < 0 or not move_stage_card(self, p, area, "removed"):
                    return False
            else:
                self.pending_choices.append(
                    (
                        "TARGET_MEMBER",
                        {
                            **cost_metadata,
                            "effect": "return_to_removed",
                            "effect_description": "髯､螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺吶Γ繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
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
                            "effect_description": f"繝ｩ繧､繝悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝ｩ繧､繝悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝ｩ繧､繝悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧閲{cost.value}譫壹ョ繝・く縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壹ョ繝・く縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ謌ｻ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐・鄂ｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壹せ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺ｫ驟咲ｽｮ縺励※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繝・ャ繧ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謐ｨ縺ｦ譛ｭ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謇区惆縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨お繝ｼ繝ｫ繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Γ繝ｳ繝舌・繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Λ繧､繝悶ｒ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨お繝ｼ繝ｫ繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Γ繝ｳ繝舌・繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Λ繧､繝悶ｒ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨お繝ｼ繝ｫ繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Γ繝ｳ繝舌・繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"謌仙粥繝ｩ繧､繝悶°繧峨Λ繧､繝悶ｒ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"髯､螟悶だ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繧ｨ繝ｼ繝ｫ繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｨ繝ｼ繝ｫ繧ｾ繝ｼ繝ｳ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽焔譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽昏縺ｦ譛ｭ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫壽・蜉溘Λ繧､繝悶↓蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝｡繝ｳ繝舌・繧畜{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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
                            "effect_description": f"繧ｹ繝・・繧ｸ縺ｮ繧ｨ繝ｼ繝ｫ縺九ｉ繝ｩ繧､繝悶ｒ{cost.value}譫夐勁螟悶だ繝ｼ繝ｳ縺ｫ蜉縺医※縺上□縺輔＞",
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


__all__ = ["handle_cost"]
