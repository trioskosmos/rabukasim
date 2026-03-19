from __future__ import annotations

from typing import Any, Dict


def handle_tap_energy_cost(game: Any, player: Any, cost: Any, cost_metadata: Dict[str, Any]) -> bool:
    tapped_indices = [i for i, tapped in enumerate(player.tapped_energy) if not tapped and i < len(player.energy_zone)]
    untapped_cards = [player.energy_zone[i] for i in tapped_indices]

    if len(untapped_cards) < cost.value:
        return False

    game.pending_choices.append(
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


__all__ = ["handle_tap_energy_cost"]