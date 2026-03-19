from __future__ import annotations

from typing import Any, Dict


def discard_hand_card(player: Any, index: int = -1) -> int | None:
    """Remove one card from hand and keep the parallel hand timestamp list aligned."""
    if not player.hand:
        return None

    if index < 0:
        index += len(player.hand)

    if not 0 <= index < len(player.hand):
        return None

    cid = player.hand.pop(index)
    if index < len(player.hand_added_turn):
        player.hand_added_turn.pop(index)
    return cid


def move_hand_card_to_discard(player: Any, index: int = -1) -> int | None:
    cid = discard_hand_card(player, index)
    if cid is not None:
        player.discard.append(cid)
    return cid


def discard_hand_cards(player: Any, count: int) -> int:
    moved = 0
    for _ in range(count):
        cid = discard_hand_card(player)
        if cid is None:
            break
        player.discard.append(cid)
        moved += 1
    return moved


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


__all__ = [
    "discard_hand_card",
    "discard_hand_cards",
    "move_hand_card_to_discard",
    "handle_discard_hand_cost",
]
