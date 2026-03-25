import os
import sys
from types import SimpleNamespace

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.rust_serializer import RustGameStateSerializer


def make_player(player_id):
    return SimpleNamespace(
        player_id=player_id,
        score=0,
        hand=[],
        hand_added_turn=[],
        stage=[-1, -1, -1],
        tapped_members=[False, False, False],
        stage_energy_count=[0, 0, 0],
        live_zone=[-1, -1, -1],
        live_zone_revealed=[False, False, False],
        energy_zone=[],
        tapped_energy=[],
        mulligan_selection=0,
        deck_count=2,
        energy_deck_count=1,
        initial_deck=[101, 102],
        deck=[201, 202],
        energy_deck=[301],
        discard=[],
        success_lives=[],
        looked_cards=[],
    )


def make_state():
    return SimpleNamespace(
        current_player=0,
        turn=1,
        db=SimpleNamespace(is_vanilla=False),
        get_legal_actions=lambda: [],
        get_effective_blades=lambda *_: 0,
        get_effective_hearts=lambda *_: [0, 0, 0, 0, 0, 0, 0],
        get_total_hearts=lambda *_: [0, 0, 0, 0, 0, 0, 0],
        get_total_blades=lambda *_: 0,
    )


def test_serialize_player_hides_private_deck_lists_from_opponent_view():
    serializer = RustGameStateSerializer({}, {}, {})
    state = make_state()
    player = make_player(1)

    visible = serializer.serialize_player(player, state, p_idx=1, viewer_idx=1, legal_mask=[], lang="en")
    hidden = serializer.serialize_player(player, state, p_idx=1, viewer_idx=0, legal_mask=[], lang="en")

    assert [card["id"] for card in visible["initial_deck"]] == [101, 102]
    assert [card["id"] for card in visible["full_deck"]] == [201, 202]
    assert [card["id"] for card in visible["energy_deck"]] == [301]

    assert hidden["initial_deck"] == []
    assert hidden["full_deck"] == []
    assert hidden["energy_deck"] == []
    assert hidden["deck_count"] == 2
    assert hidden["energy_deck_count"] == 1
