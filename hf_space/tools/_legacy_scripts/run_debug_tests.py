import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from engine.game.mixins.effect_mixin import EffectMixin
from engine.models.ability import Effect, EffectType, TargetType
from engine.models.card import LiveCard, MemberCard
from engine.models.enums import Group


# Mock Classes for Standalone Testing
class MockGameState(EffectMixin):
    def __init__(self):
        self.pending_choices = []
        self.pending_effects = []
        self.players = [MockPlayer(0), MockPlayer(1)]
        self.turn_number = 1
        self.active_player_index = 0
        self.member_db = {}
        self.live_db = {}
        self.continuous_effects = []
        self.looked_cards = []
        # Add missing attributes found in GameState
        self.current_resolving_member = None
        self.current_resolving_ability = None
        self.rule_log = []
        self.removed_cards = []
        self.triggered_abilities = []

    @property
    def active_player(self):
        return self.players[self.active_player_index]

    @property
    def inactive_player(self):
        return self.players[1 - self.active_player_index]

    def _draw_cards(self, p, count):
        pass


class MockPlayer:
    def __init__(self, pid):
        self.player_id = pid
        self.hand = []
        self.discard = []
        self.stage = [-1, -1, -1]
        self.energy_zone = []
        self.restrictions = set()
        self.continuous_effects = []
        self.hand_added_turn = []
        self.success_lives = []
        self.energy_deck = []
        self.main_deck = []
        self.baton_touch_limit = 1
        self.negate_next_effect = False


def test_recover():
    print("Running test_recover...")
    gs = MockGameState()
    p = gs.active_player
    p.discard = [1182]

    # Mock Live DB
    c = LiveCard(1182, "L1", "Test Live", 1, [0] * 7, [], [Group.LIVE])
    gs.live_db[1182] = c

    effect = Effect(EffectType.RECOVER_LIVE, 1, TargetType.SELF, {})

    # Execute
    print(f"Before: Discard={p.discard}, LiveDB keys={list(gs.live_db.keys())}")
    gs.pending_effects.append(effect)
    gs._resolve_pending_effect(0, {})

    print(f"Pending Choices: {len(gs.pending_choices)}")
    if len(gs.pending_choices) > 0:
        print(f"Choice 0: {gs.pending_choices[0][0]}")

    assert len(gs.pending_choices) == 1
    print("test_recover PASSED")


def test_tap_opponent():
    print("Running test_tap_opponent...")
    gs = MockGameState()
    opp = gs.players[1]
    opp.stage[1] = 101

    # Mock Member DB
    c = MemberCard(101, "1", "M1", 1, [0] * 7, [0] * 7, 0, [Group.MUSE], [])
    gs.member_db[101] = c

    effect = Effect(EffectType.TAP_OPPONENT, 1, TargetType.OPPONENT_MEMBER, {})

    print(f"Before: Opp Stage={opp.stage}")
    gs.pending_effects.append(effect)
    gs._resolve_pending_effect(0, {})

    print(f"Pending Choices: {len(gs.pending_choices)}")
    if len(gs.pending_choices) > 0:
        print(f"Choice 0: {gs.pending_choices[0][0]}")

    assert len(gs.pending_choices) == 1
    print("test_tap_opponent PASSED")


if __name__ == "__main__":
    try:
        test_recover()
    except Exception as e:
        print(f"test_recover FAILED: {e}")
        import traceback

        traceback.print_exc()

    try:
        test_tap_opponent()
    except Exception as e:
        print(f"test_tap_opponent FAILED: {e}")
        import traceback

        traceback.print_exc()
