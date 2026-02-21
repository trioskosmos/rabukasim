import sys
import os

# Add the project root to sys.path to allow imports from tools.reproduction
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

# Create an empty __init__.py in tools/reproduction if it doesn't exist to make it a package
init_path = os.path.join(project_root, "tools", "reproduction", "__init__.py")
if not os.path.exists(init_path):
    with open(init_path, "w") as f:
        pass

# Add the project root to sys.path to allow imports from engine_rust
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load utils using importlib to avoid package issues
import importlib.util

utils_path = os.path.join(project_root, "tools", "reproduction", "utils.py")
spec = importlib.util.spec_from_file_location("utils", utils_path)
utils = importlib.util.module_from_spec(spec)
sys.modules["utils"] = utils
spec.loader.exec_module(utils)

from utils import create_game_state, create_test_card_database, debug_print
from engine_rust import PyGameState, PyPlayerState
import engine_rust

print(f"DEBUG: engine_rust location: {engine_rust.__file__}")


def test_draw_2_discard_2():
    """
    Test Rank 9: PL!N-PR-005-PR (ID 453)
    Text: 登場カードを2枚引き手札を2枚控え室に置く
    Effect: DRAW(2) -> PLAYER; DISCARD_HAND(2) -> PLAYER
    """
    debug_print("Testing Rank 9: Draw 2, Discard 2")

    # 1. Setup
    db = create_test_card_database()

    # Use ID 453 for Rank 9
    card_id = 453

    # Create game state
    gs = create_game_state(db)

    # Setup player 0
    # Give player some cards in deck to draw
    # IDs 101, 102, 103, 104 in deck
    gs.set_deck_cards(0, [101, 102, 103, 104])

    # Set energy to pay for card (cost 13?)
    # ID 914=Red:2, ID 912=Blue:2, ID 915=Purple:2.
    # Total: Red=2, Blue=2, Purple=2. Matches Rank 9 requirements.
    gs.set_energy_cards(0, [914, 912, 915] * 5)

    # Give player some cards in hand to discard
    # ID 201, 202 in hand. Plus the card we play (453).
    gs.set_hand_cards(0, [201, 202, card_id])

    p0 = gs.get_player(0)
    print(f"Energy cards: {len(p0.energy_zone)}")
    print(f"Tapped energy: {list(p0.tapped_energy)}")
    print(f"Hand cards: {p0.hand}")

    print("\n--- Legal Actions ---")
    actions = gs.get_legal_action_ids()
    for aid in actions:
        # Check if it's a play action
        if 1 <= aid <= 180:
            hand_idx = (aid - 1) // 3
            slot_idx = (aid - 1) % 3
            print(f"  ID {aid}: Play Hand[{hand_idx}] to Slot {slot_idx}")
        else:
            print(f"  ID {aid}")

    # 2. Action: Play the card
    # We play card_id (453) from hand index 2 to center (0)
    # This should trigger ON_PLAY: DRAW(2), then DISCARD(2)

    debug_print(f"Playing card {card_id}...")
    utils.process_action(gs, 2, 0)  # Play card at index 2 to slot 0

    # 3. Verification - Step 1: Draw 2
    # After playing, we should have drawn 2 cards.
    # Logic:
    # Hand was [201, 202, 453]. Played 453. Hand becomes [201, 202].
    # Ability triggers: Draw 2. Hand becomes [201, 202, 101, 102].
    # Then Discard 2.

    # However, DISCARD(2) usually requires a choice if we have cards.
    # If the engine handles it interactively, pending_choice should be SELECT_HAND_DISCARD.

    choice_type = gs.pending_choice_type
    debug_print(f"Pending choice: {choice_type}")

    if choice_type == "SELECT_HAND_DISCARD":
        # Check that we have drawn the cards before discarding
        p0_check = gs.get_player(0)
        hand = p0_check.hand
        debug_print(f"Hand after draw, before discard: {hand}")

        # We expect 4 cards in hand (2 original + 2 drawn)
        # Note: Depending on implementation order, it might draw then ask to discard.
        if len(hand) != 4:
            print(f"FAIL: Expected 4 cards in hand, got {len(hand)}")
            return False

        # Select 2 cards to discard (indices 0 and 1)
        # Note: When we select index 0, the next card shifts to index 0?
        # Or does the engine handle indices based on original state?
        # Usually indices are stable until step is processed.
        # But here we make two choices sequentially? Or one multi-select?
        # SELECT_HAND_DISCARD usually takes one choice at a time if it loops.

        debug_print("Selecting 1st card to discard...")
        utils.process_action(gs, 0)  # Select index 0

        # Check if we need to select another
        choice_type = gs.pending_choice_type
        if choice_type == "SELECT_HAND_DISCARD":
            debug_print("Selecting 2nd card to discard...")
            utils.process_action(gs, 0)  # Select index 0 again (as first was removed?)

        # 4. Final Verification
        p0_final = gs.get_player(0)
        hand_final = p0_final.hand
        discard_final = p0_final.discard

        debug_print(f"Final hand: {hand_final}")
        debug_print(f"Final discard: {discard_final}")

        # Should have 2 cards left in hand
        if len(hand_final) != 2:
            print(f"FAIL: Expected 2 cards in hand, got {len(hand_final)}")
            return False

        # Discard should contain the 2 discarded cards
        if len(discard_final) < 2:
            print(f"FAIL: Expected at least 2 cards in discard, got {len(discard_final)}")
            return False

        return True
    else:
        print(f"FAIL: Expected SELECT_HAND_DISCARD choice, got {choice_type}")
        return False


if __name__ == "__main__":
    if test_draw_2_discard_2():
        print("PASS")
    else:
        print("FAIL")
