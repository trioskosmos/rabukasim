import json
import os
import sys
from types import SimpleNamespace

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.rust_serializer import FILTER_IS_OPTIONAL, RustGameStateSerializer
from engine.game.enums import Phase


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
        phase=Phase.RESPONSE,
        turn=1,
        db=SimpleNamespace(is_vanilla=False),
        get_legal_actions=lambda: [],
        get_effective_blades=lambda *_: 0,
        get_effective_hearts=lambda *_: [0, 0, 0, 0, 0, 0, 0],
        get_total_member_hearts=lambda *_: [0, 0, 0, 0, 0, 0, 0],
        get_total_hearts=lambda *_: [0, 0, 0, 0, 0, 0, 0],
        get_total_blades=lambda *_: 0,
        pending_choice_text="",
        pending_card_id=-1,
        pending_choices=[],
        rule_log=[],
        last_performance_results="{}",
        is_terminal=lambda: False,
        get_winner=lambda: -1,
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


def test_normalize_pending_choice_preserves_sparse_selection_indices():
    serializer = RustGameStateSerializer({}, {}, {})
    state = make_state()
    state.players = [make_player(0), make_player(1)]
    state.get_player = lambda idx: state.players[idx]
    state.players[0].looked_cards = [-1, 202, -1, 404]

    pending_choice = serializer._normalize_pending_choice(
        state,
        "select_from_list",
        {
            "choice_type": "LOOK_AND_CHOOSE",
            "source_card_id": 7,
            "source_player": 0,
        },
        lang="en",
    )

    assert [card["selection_idx"] for card in pending_choice["selection_cards"]] == [1, 3]
    assert [card["id"] for card in pending_choice["selection_cards"]] == [202, 404]


def test_serialize_state_maps_sparse_choice_action_to_original_selection_index():
    serializer = RustGameStateSerializer({}, {}, {})
    state = make_state()
    state.players = [make_player(0), make_player(1)]
    state.get_player = lambda idx: state.players[idx]
    state.pending_card_id = 7
    state.players[0].looked_cards = [-1, -1, 303]

    legal_mask = [False] * 11003
    legal_mask[11002] = True
    state.get_legal_actions = lambda: legal_mask
    state.pending_choices = [(
        "select_from_list",
        {
            "choice_type": "LOOK_AND_CHOOSE",
            "source_card_id": 7,
            "source_player": 0,
            "target_player": 0,
            "cards": [-1, -1, 303],
        },
    )]

    serialized = serializer.serialize_state(state, viewer_idx=0, lang="en")

    assert serialized["pending_choice"]["selection_cards"][0]["selection_idx"] == 2
    action = serialized["legal_actions"][0]
    assert action["selection_index"] == 2
    assert action["target_index"] == 2
    assert action["card_id"] == 303


def test_resolve_choice_name_handles_select_mode_and_optional_look_and_choose():
    serializer = RustGameStateSerializer({}, {}, {})

    pending_choice = {
        "options": [{}, {}],
        "options_text": ["Pay 2 Energy", "Discard 2 Hand"],
        "choice_type": "SELECT_MODE",
        "type": "SELECT_MODE",
    }

    assert serializer._resolve_choice_name(1, pending_choice, lang="en") == "Discard 2 Hand"

    state = make_state()
    state.players = [make_player(0), make_player(1)]
    state.get_player = lambda idx: state.players[idx]
    state.get_legal_actions = lambda: [True]
    state.pending_choices = [(
        "select_from_list",
        json.dumps(
            {
                "choice_type": "LOOK_AND_CHOOSE",
                "source_card_id": 500,
                "source_player": 0,
                "target_player": 0,
                "filter_attr": FILTER_IS_OPTIONAL,
            }
        ),
    )]

    serialized = serializer.serialize_state(state, viewer_idx=0, lang="en")

    assert serialized["pending_choice"]["filter_attr"] == FILTER_IS_OPTIONAL
    assert serialized["legal_actions"][0]["name"] == "No / Skip"
