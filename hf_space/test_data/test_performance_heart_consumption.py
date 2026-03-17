from types import SimpleNamespace

import numpy as np

from engine.game.player_state import PlayerState
from engine.game.serializer import serialize_player
from engine.models.card import LiveCard, MemberCard


def _member(card_id: int, hearts: list[int]) -> MemberCard:
    return MemberCard(
        card_id=card_id,
        card_no=f"M-{card_id}",
        name=f"Member {card_id}",
        cost=1,
        hearts=np.array(hearts, dtype=np.int32),
        blade_hearts=np.zeros(7, dtype=np.int32),
        blades=0,
    )


def _live(card_id: int, required: list[int]) -> LiveCard:
    return LiveCard(
        card_id=card_id,
        card_no=f"L-{card_id}",
        name=f"Live {card_id}",
        score=1,
        required_hearts=np.array(required, dtype=np.int32),
    )


def test_performance_guide_consumes_colored_hearts_used_for_any_requirements():
    player = PlayerState(0)
    player.stage[0] = 101
    player.live_zone = [201, 202]

    member_db = {101: _member(101, [1, 0, 0, 0, 0, 0, 0])}
    live_db = {
        201: _live(201, [0, 0, 0, 0, 0, 0, 1]),
        202: _live(202, [1, 0, 0, 0, 0, 0, 0]),
    }

    guide = player.get_performance_guide(live_db, member_db)

    assert guide["lives"][0]["passed"] is True
    assert guide["lives"][1]["passed"] is False


def test_serializer_marks_later_live_uncleared_after_any_consumes_pool():
    player = PlayerState(0)
    player.stage[0] = 101
    player.live_zone = [201, 202]
    player.live_zone_revealed = [True, True]

    member_db = {101: _member(101, [1, 0, 0, 0, 0, 0, 0])}
    live_db = {
        201: _live(201, [0, 0, 0, 0, 0, 0, 1]),
        202: _live(202, [1, 0, 0, 0, 0, 0, 0]),
    }
    game_state = SimpleNamespace(
        member_db=member_db,
        live_db=live_db,
        energy_db={},
        turn_number=1,
        current_player=0,
        get_legal_actions=lambda _player_idx: [False] * 900,
    )

    serialized = serialize_player(player, game_state, 0, viewer_idx=0)

    assert serialized["live_zone"][0]["is_cleared"] is True
    assert serialized["live_zone"][1]["is_cleared"] is False
