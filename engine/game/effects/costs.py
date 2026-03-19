from typing import Any, Dict, List

from engine.game.enums import Phase
from engine.models.ability import AbilityCostType, Cost, EffectType


def can_pay_costs(player: Any, costs: List[Cost], source_area: int = -1, start_index: int = 0) -> bool:
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


def pay_costs(game: Any, p: Any, costs: List[Cost], source_area: int = -1, start_index: int = 0) -> bool:
    """
    Pay costs. Returns True if paid, False if cancelled/deferred (optional).
    If optional cost is encountered, it queues a choice and returns False.
    """
    if not can_pay_costs(p, costs, source_area, start_index):
        return False

    total_reduction = sum(
        ce["effect"].value for ce in p.continuous_effects if ce["effect"].effect_type == EffectType.REDUCE_COST
    )

    # Default metadata for cost payment
    scid = getattr(game, "current_resolving_member_id", -1)
    choice_metadata: Dict[str, Any] = {"source_card_id": scid, "step_progress": "Cost"}

    for i, cost in enumerate(costs[start_index:]):
        cost_idx = start_index + i
        if cost.type == AbilityCostType.ENERGY:
            if cost.is_optional:
                if game.verbose:
                    print(f"DEBUG: Queueing PAY_COST_OPTIONAL for player {p.player_id}")
                game.pending_choices.append(
                    (
                        "PAY_COST_OPTIONAL",
                        {
                            **choice_metadata,
                            "cost_index": cost_idx,
                            "amount": cost.value,
                            "cost_type": "energy",
                            "effect_description": f"Pay optional energy cost ({cost.value})",
                        },
                    )
                )
                game.phase = Phase.RESPONSE
                return False

            act = max(0, cost.value - total_reduction)
            tapped = 0
            for i in range(len(p.energy_zone) - 1, -1, -1):
                if tapped >= act:
                    break
                if not p.tapped_energy[i]:
                    p.tapped_energy[i] = True
                    tapped += 1
        elif cost.type == AbilityCostType.TAP_SELF:
            if source_area >= 0:
                p.tapped_members[source_area] = True
        elif cost.type == AbilityCostType.SACRIFICE_SELF:
            if source_area >= 0 and p.stage[source_area] >= 0:
                p.discard.append(p.stage[source_area])
                p.stage[source_area] = -1
                p.energy_deck.extend(p.stage_energy[source_area])
                p.stage_energy[source_area] = []
                p.tapped_members[source_area] = False
                p.members_played_this_turn[source_area] = False
        elif cost.type == AbilityCostType.SACRIFICE_UNDER:
            if source_area >= 0:
                p.energy_deck.extend(p.stage_energy[source_area])
                p.stage_energy[source_area] = []
        elif cost.type == AbilityCostType.DISCARD_ENERGY:
            for i in range(len(p.energy_zone) - 1, -1, -1):
                if not p.tapped_energy[i]:
                    p.tapped_energy[i] = True
                    break
        elif cost.type == AbilityCostType.RETURN_HAND:
            if source_area >= 0 and p.stage[source_area] >= 0:
                p.hand.append(p.stage[source_area])
                p.stage[source_area] = -1
                p.energy_deck.extend(p.stage_energy[source_area])
                p.stage_energy[source_area] = []
        elif cost.type == AbilityCostType.DISCARD_HAND:
            if cost.is_optional:
                game.pending_choices.append(
                    (
                        "PAY_COST_OPTIONAL",
                        {
                            **choice_metadata,
                            "cost_index": cost_idx,
                            "amount": cost.value,
                            "cost_type": "discard",
                            "effect_description": f"Discard cards for optional cost ({cost.value})",
                        },
                    )
                )
                game.phase = Phase.RESPONSE
                return False

            params = {
                "reason": "cost",
                "effect": "discard",
                "is_optional": cost.is_optional,
                "cost_index": cost_idx,
                "count": cost.value,
            }
            if hasattr(cost, "params") and cost.params:
                params.update(cost.params)
            game.pending_choices.append(("TARGET_HAND", {**choice_metadata, **params}))
            return False
        elif cost.type in (AbilityCostType.TAP_MEMBER, AbilityCostType.REST_MEMBER):
            # Pending implementation of choices for these types (if any)
            pass
    return True

