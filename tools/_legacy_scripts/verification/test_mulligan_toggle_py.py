import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from engine.game.game_state import GameState
from engine.game.player_state import PlayerState


def test_mulligan_toggle():
    print("Testing Mulligan Toggle (Python Engine)...")

    # Setup dummy state
    gs = GameState()
    # Mock player setup
    p0 = PlayerState(0)
    p0.hand = [1, 2, 3, 4, 5, 6]
    gs.players = [p0, PlayerState(1)]
    gs.current_player = 0

    # Phase needs to be Mulligan
    # Import Phase
    from engine.game.enums import Phase

    gs.phase = Phase.MULLIGAN_P1

    # Action 300 = Select index 0 (Card 1)
    print("Selecting card 0 (Action 300)...")
    gs._execute_action(300)

    assert hasattr(p0, "mulligan_selection")
    assert 0 in p0.mulligan_selection
    print("  -> Card 0 in selection: OK")

    # Toggle: Select index 0 again
    print("Deselecting card 0 (Action 300)...")
    gs._execute_action(300)

    assert 0 not in p0.mulligan_selection
    print("  -> Card 0 NOT in selection: OK")

    # Select index 1 (Action 301)
    print("Selecting card 1 (Action 301)...")
    gs._execute_action(301)
    assert 1 in p0.mulligan_selection
    print("  -> Card 1 in selection: OK")

    print("\nPython Mulligan Toggle Test PASSED")


if __name__ == "__main__":
    test_mulligan_toggle()
