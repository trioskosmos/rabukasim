import unittest
from types import SimpleNamespace
import sys
import json

sys.modules.setdefault('engine_rust', SimpleNamespace())

from backend.rust_serializer import RustGameStateSerializer
from engine.game.enums import Phase


class FakePlayer:
    def __init__(self, hand=None, stage=None, discard=None, live_zone=None, player_id=0):
        self.player_id = player_id
        self.hand = hand or []
        self.stage = stage or [-1, -1, -1]
        self.discard = discard or []
        self.live_zone = live_zone or [-1, -1, -1]
        self.success_lives = []
        self.mulligan_selection = 0


class FakeGameState:
    def __init__(self, legal_mask, pending_choices, players, phase=Phase.RESPONSE, current_player=0):
        self._legal_mask = legal_mask
        self.pending_choices = pending_choices
        self.current_player = current_player
        self.phase = phase
        self.turn = 1
        self.rule_log = []
        self.last_performance_results = '{}'
        self.performance_history = '[]'
        self.pending_choice_text = ''
        self.pending_choice_type = ''
        self.pending_ab_idx = 0
        self.pending_area_idx = 0
        self.pending_card_id = -1
        self.db = SimpleNamespace(is_vanilla=False)
        self._players = players

    def get_legal_actions(self):
        return self._legal_mask

    def get_player(self, idx):
        return self._players[idx]

    def is_terminal(self):
        return False

    def get_winner(self):
        return -1


class RustSerializerActionMetadataTests(unittest.TestCase):
    def setUp(self):
        source_card = SimpleNamespace(
            card_no='SRC-001',
            name='Source Idol',
            cost=2,
            blades=1,
            img_path='source.png',
            hearts=[1, 0, 0, 0, 0, 0],
            blade_hearts=[0, 0, 0, 0, 0, 0],
            original_text='Source ability text',
            original_text_en='Source ability text',
            ability_text='Source ability text',
            abilities=[],
        )
        target_card = SimpleNamespace(
            card_no='TGT-002',
            name='Target Idol',
            cost=1,
            blades=0,
            img_path='target.png',
            hearts=[0, 1, 0, 0, 0, 0],
            blade_hearts=[0, 0, 0, 0, 0, 0],
            original_text='Target card text',
            original_text_en='Target card text',
            ability_text='Target card text',
            abilities=[],
        )
        self.serializer = RustGameStateSerializer({1: source_card, 2: target_card}, {}, {})
        self.serializer.serialize_player = lambda *args, **kwargs: {}

    def test_select_from_list_keeps_effect_source_separate_from_selected_card(self):
        legal_mask = [False] * 1000
        legal_mask[550] = True
        gs = FakeGameState(
            legal_mask=legal_mask,
            pending_choices=[('SELECT_FROM_LIST', json.dumps({'cards': [2], 'source_card_id': 1}))],
            players=[FakePlayer(), FakePlayer()],
        )

        state = self.serializer.serialize_state(gs, viewer_idx=0)
        action = state['legal_actions'][0]

        self.assertEqual(action['id'], 550)
        self.assertEqual(action['source_card_id'], 1)
        self.assertEqual(action['card_id'], 2)
        self.assertEqual(action['name'], 'Target Idol')
        self.assertNotEqual(action.get('text', ''), 'Target card text')

    def test_target_opponent_keeps_source_card_on_action_metadata(self):
        legal_mask = [False] * 1000
        legal_mask[600] = True
        gs = FakeGameState(
            legal_mask=legal_mask,
            pending_choices=[('TARGET_OPPONENT_MEMBER', json.dumps({'source_card_id': 1}))],
            players=[FakePlayer(), FakePlayer(stage=[2, -1, -1])],
        )

        state = self.serializer.serialize_state(gs, viewer_idx=0)
        action = state['legal_actions'][0]

        self.assertEqual(action['id'], 600)
        self.assertEqual(action['source_card_id'], 1)
        self.assertEqual(action['card_id'], 2)
        self.assertEqual(action['target_player'], 1)
        self.assertEqual(action['slot_idx'], 0)


if __name__ == '__main__':
    unittest.main()
