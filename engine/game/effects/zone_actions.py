from __future__ import annotations

import random
from typing import Any


def clear_stage_slot(player: Any, area: int) -> int:
    """Remove the staged card from a slot and clear its local state."""
    if area < 0 or area >= len(player.stage):
        return -1

    cid = player.stage[area]
    if cid < 0:
        return -1

    player.stage[area] = -1
    player.tapped_members[area] = False
    player.stage_energy[area].clear()
    return cid


def move_stage_card(game: Any, player: Any, area: int, destination: str) -> bool:
    """Move the card in a stage slot to another zone."""
    cid = clear_stage_slot(player, area)
    if cid < 0:
        return False

    dest = destination.lower()
    if dest == "hand":
        player.hand.append(cid)
        return True
    if dest == "discard":
        player.discard.append(cid)
        return True
    if dest == "removed":
        game.removed_cards.append(cid)
        return True
    if dest == "deck":
        player.main_deck.append(cid)
        random.shuffle(player.main_deck)
        return True
    if dest == "success":
        player.success_lives.append(cid)
        return True

    return False


__all__ = ["clear_stage_slot", "move_stage_card"]
