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
    print("TEST: Draw & Discard (PL!N-bp1-019-PR)")
    print("============================================================")

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 566 is Setsuna.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    # Hand: Setsuna + Dummy 10
    # Deck: Dummy 100
    gs.set_hand_cards(0, [566, 10])
    gs.set_deck_cards(0, [100])

    print("Initial State:")
    print(f"  Hand: {gs.get_player(0).hand}")
    print(f"  Deck: {gs.get_player(0).deck}")

    # 3. Play Setsuna
    print("\n--- Playing Setsuna ---")
    try:
        gs.process_action(0, 4, 0)  # Play from hand

        # 4. Handle Mandatory Discard
        if gs.get_player(0).pending_choice_type == "SELECT_HAND_DISCARD":
            print("Selecting card to discard...")
            gs.process_action(0, 500, 0)  # Select 1st hand card (should be 10 or 100)

    except Exception as e:
        print(f"Execution info: {e}")

    # 5. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    hand = p0.hand
    discard = p0.discard

    print(f"  Hand: {hand}")
    print(f"  Discard: {discard}")

    # Success criteria:
    # 1. Card 100 was drawn.
    # 2. One card was discarded.
    # Total hand size should be 1 (Setsuna played, 1 drawn, 1 discarded).

    success = True
    if len(hand) != 1:
        print(f"FAILURE: Expected hand size 1, found {len(hand)}.")
        success = False

    if len(discard) != 1:
        print(f"FAILURE: Expected discard size 1, found {len(discard)}.")
        success = False

    if success:
        print("\nSUCCESS: Draw & Discard ability works!")
    else:
        print("\nFAILURE: Draw & Discard ability failed.")


if __name__ == "__main__":
    run_test()
