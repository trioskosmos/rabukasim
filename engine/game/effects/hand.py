from __future__ import annotations

from typing import Any, Dict


def handle_discard_hand_cost(game: Any, player: Any, cost: Any, cost_metadata: Dict[str, Any]) -> bool:
    if len(player.hand) <= 0:
        return False

    game.pending_choices.append(
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


__all__ = ["handle_discard_hand_cost"]