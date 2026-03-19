import os
import sys
from types import SimpleNamespace

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.game.game_state import GameState
from engine.models.ability import Condition
from engine.models.generated_enums import ConditionType


def test_count_success_live_respects_opponent_target():
    state = GameState()
    state.ui = SimpleNamespace(silent=True)

    state.players[0].success_lives = []
    state.players[1].success_lives = [30000]

    self_condition = Condition(ConditionType.COUNT_SUCCESS_LIVE, {"target": "self", "min": 0})
    opponent_condition = Condition(ConditionType.COUNT_SUCCESS_LIVE, {"target": "opponent", "min": 1})

    assert state._check_condition(state.players[0], self_condition, {})
    assert state._check_condition(state.players[0], opponent_condition, {})