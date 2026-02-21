import numpy as np
import pytest

def generate_test_file:
    with open('tests/test_ability_patterns_rigorous.py', 'w', encoding='utf-8') as f:
        f.write('import numpy as np\\nimport pytest\\n')
        f.write('from engine.game.game_state import GameState, Group, LiveCard, MemberCard, Phase\\n')
        f.write('from engine.models.ability import Ability, Effect, EffectType, TargetType, TriggerType\\n\\n')
        f.write('@pytest.fixture\\ndef game_state:\\n    \"\"\"Create a fresh game state for each test.\"\"\"\\n    state = GameState)\\n    # Reset class variables to avoid cross-test contamination\\n    GameState.member_db = {}\\n    GameState.live_db = {}\\n    return state\\n\\n')
        f.write('class TestRecoveryFromDiscardPatterns:\\n    \"\"\"Test the \\'Recovery from Discard\\' pattern group.\"\"\"\\n\\n')
        f.write('    @pytest.fixture)
