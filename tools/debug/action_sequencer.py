import os
import sys
import traceback
from typing import Callable

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from game.game_state import GameState, Phase


class StateVerifier:
    """Helper class to verify game state properties."""

    def __init__(self, state: GameState):
        self.state = state

    def assert_phase(self, expected_phase: Phase):
        if self.state.phase != expected_phase:
            raise AssertionError(f"Expected phase {expected_phase}, but got {self.state.phase}")

    def assert_player_turn(self, expected_player: int):
        if self.state.current_player != expected_player:
            raise AssertionError(f"Expected player {expected_player}'s turn, but got {self.state.current_player}")

    def assert_hand_contains(self, player_id: int, card_id: int):
        if card_id not in self.state.players[player_id].hand:
            raise AssertionError(
                f"Player {player_id} hand does not contain card {card_id}. Hand: {self.state.players[player_id].hand}"
            )

    def assert_hand_does_not_contain(self, player_id: int, card_id: int):
        if card_id in self.state.players[player_id].hand:
            raise AssertionError(f"Player {player_id} hand contains card {card_id} but shouldn't.")

    def assert_stage_card(self, player_id: int, position: int, card_id: int):
        actual = self.state.players[player_id].stage[position]
        if actual != card_id:
            raise AssertionError(f"Player {player_id} stage[{position}] expected {card_id}, got {actual}")

    def assert_life_at(self, player_id: int, valid_hp: int):
        # This is a bit complex as HP is derived from live zone, but for now we check length of lives
        lives = len(self.state.players[player_id].live_zone)
        if lives != valid_hp:
            raise AssertionError(f"Player {player_id} expected {valid_hp} lives, got {lives}")


class ActionSequence:
    """Defines and executes a sequence of actions."""

    def __init__(self, state: GameState = None):
        self.state = state if state else GameState()
        self.verifier = StateVerifier(self.state)
        self.history = []

    def setup_inject(self, player_id: int, card_id: int, zone: str, position: int = -1):
        """Inject a card before the sequence starts properly."""
        print(f"[SETUP] Inject P{player_id} {card_id} -> {zone}@{position}")
        self.state.inject_card(player_id, card_id, zone, position)

    def action_step(self, action_id: int, comment: str = ""):
        """Execute a single game action."""
        print(f"[ACTION] {comment} (ID: {action_id})")
        # Validate legality
        legal_actions = self.state.get_legal_actions()
        if not legal_actions[action_id]:
            raise AssertionError(f"Action {action_id} is improperly illegal in phase {self.state.phase}")

        self.state = self.state.step(action_id)
        self.verifier.state = self.state  # Update verifier ref
        self.history.append((action_id, comment))

    def action_auto(self, max_steps: int = 10):
        """Advance through automatic phases."""
        print(f"[AUTO] Advancing up to {max_steps} steps...")
        steps = 0
        from game.game_state import Phase  # Local import to avoid circular dependency issues if any

        while steps < max_steps and not self.state.is_terminal():
            if self.state.phase in (Phase.ACTIVE, Phase.ENERGY, Phase.DRAW, Phase.PERFORMANCE_P1, Phase.PERFORMANCE_P2):
                self.state = self.state.step(0)
                self.verifier.state = self.state
                steps += 1
                continue
            break
        print(f"[AUTO] Done after {steps} steps. Phase: {self.state.phase}")

    def verify(self, check_func: Callable[[StateVerifier], None]):
        """Run a custom verification function."""
        print("[VERIFY] Running checks...")
        check_func(self.verifier)
        print("[VERIFY] Passed.")

    def run_wrapper(self, func):
        """Run a function and handle errors nicely."""
        try:
            func()
            print("\n✅ Sequence Completed Successfully")
        except AssertionError as e:
            print(f"\n❌ Verification Failed: {e}")
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            print(f"\n💥 Runtime Error: {e}")
            traceback.print_exc()
            sys.exit(1)
