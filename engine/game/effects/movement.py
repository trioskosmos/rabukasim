from typing import Any


def move_member(player: Any, from_idx: int, to_idx: int) -> None:
    """Swap two stage slots and keep the related state in sync."""
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

