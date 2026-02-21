import os
import sys

# Add project root to path for engine_rust
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

try:
    import engine_rust
except ImportError:
    print("Error: engine_rust not found. Did you run build_engine.bat?")
    sys.exit(1)


def run_test():
    print("============================================================")
    print("TEST: Look & Choose (PL!-sd1-011-SD)")
    print("============================================================")

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 257 is Eli.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    gs.set_hand_cards(0, [257, 10])  # Eli and a card to discard (10)
    gs.set_deck_cards(0, [101, 102, 103, 104])  # Deck entries

    print(f"Initial State:")
    print(f"  Hand: {gs.get_player(0).hand}")
    print(f"  Deck: {gs.get_player(0).deck}")

    # 3. Trigger Ability (Index 0)
    print("\n--- Playing Eli ---")
    # Eli is in hand, we play it to trigger ON_PLAY.
    try:
        # Playing to slot 0
        gs.process_action(0, 4, 0)  # Play Eli from hand

        # 4. Handle Optional Cost: Discard Card 10
        if gs.get_player(0).pending_choice_type == "CONFIRM":
            print("Confirming optional cost...")
            gs.process_action(0, 506, 0)  # Confirm (Yes)

        if gs.get_player(0).pending_choice_type == "SELECT_HAND_DISCARD":
            print("Selecting card to discard...")
            gs.process_action(0, 500, 0)  # Select 1st hand card (which should be 10 now)

        # 5. Handle Look & Choose
        if gs.get_player(0).pending_choice_type == "SELECT_FROM_LIST":
            print(f"Looked cards: {gs.get_player(0).looked_cards}")
            print("Selecting card 103 to hand...")
            # Assuming 103 is at index 0 of looked_cards (popped 104, 103, 102)
            # Wait, pop order usually pops end. [101, 102, 103, 104] -> pops 104, 103, 102.
            # They are in looked_cards. We pick one.
            gs.process_action(0, 500, 0)

    except Exception as e:
        print(f"Execution info: {e}")

    # 6. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    hand = p0.hand
    discard = p0.discard

    print(f"  Hand: {hand}")
    print(f"  Discard: {discard}")

    # Success criteria:
    # 1. Card 10 is in discard (if cost paid).
    # 2. One card from deck is in hand.
    # 3. Two cards from deck are in discard.

    deck_cards_in_hand = [c for c in hand if c in [101, 102, 103, 104]]
    deck_cards_in_discard = [c for c in discard if c in [101, 102, 103, 104]]

    success = True
    if 10 not in discard:
        print("FAILURE: Cost card 10 not in discard.")
    if len(deck_cards_in_hand) != 1:
        print(f"FAILURE: Expected 1 deck card in hand, found {len(deck_cards_in_hand)}.")
        success = False
    if len(deck_cards_in_discard) != 2:
        print(f"FAILURE: Expected 2 deck cards in discard, found {len(deck_cards_in_discard)}.")
        success = False

    if success:
        print("\nSUCCESS: Look & Choose ability works!")
    else:
        print("\nFAILURE: Look & Choose ability failed.")


if __name__ == "__main__":
    run_test()
