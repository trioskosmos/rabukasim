import os
import sys
from types import SimpleNamespace

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.game.enums import Phase
from engine.game.game_state import GameState
from engine.models.ability import Effect, EffectType, TargetType


class _LiveCard:
    def __init__(self) -> None:
        self.name = "Test Live"
        self.img_path = "test.png"
        self.score = 1
        self.abilities = []


def _make_state() -> GameState:
    state = GameState()
    state.ui = SimpleNamespace(silent=True)
    state.member_db = {}
    state.live_db = {30000: _LiveCard()}
    state.performance_reveals_done = [True, True]
    state.phase = Phase.PERFORMANCE_P1
    state.first_player = 0
    state.current_player = 0
    state.players[0].cannot_live = True
    state.players[0].live_zone = [30000]
    state.players[0].live_zone_revealed = [False]
    state.players[0].discard = []
    return state


def test_cannot_live_skips_live_start_and_discards_live_zone():
    state = _make_state()

    def _unexpected_trigger(*args, **kwargs):
        raise AssertionError("ON_LIVE_START should not be triggered while cannot_live is active")

    state.trigger_event = _unexpected_trigger

    state._do_performance(0)

    player = state.players[0]
    assert player.live_zone == []
    assert player.discard == [30000]
    assert state.phase == Phase.PERFORMANCE_P2
    assert state.current_player == 1


def test_live_end_cleanup_recomputes_cannot_live_from_remaining_effects():
    state = _make_state()
    player = state.players[0]
    player.cannot_live = True
    player.continuous_effects = [
        {
            "effect": Effect(EffectType.RESTRICTION, 0, TargetType.SELF, {"type": "live"}),
            "expiry": "LIVE_END",
        }
    ]

    state._clear_expired_effects("LIVE_END")

    assert player.cannot_live is False
    assert player.continuous_effects == []
