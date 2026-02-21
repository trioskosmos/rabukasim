import os
import sys

# Add project root to path for engine_rust
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

try:
    import engine_rust
except ImportError:
    engine_rust = None


def run_test():
    print("============================================================")
    print("TEST: Draw 2, Discard 2 (PL!N-PR-005-PR)")
    print("============================================================")

    if engine_rust is None:
        print("SKIPPING: engine_rust not found/compiled.")
        return

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 453 is Shizuku.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    # Hand: Shizuku + Dummy 10, 11
    # Deck: Dummy 100, 101
    gs.set_hand_cards(0, [453, 10, 11])
    gs.set_deck_cards(0, [100, 101])

    print(f"Initial State:")
    print(f"  Hand: {gs.get_player(0).hand}")
    print(f"  Deck: {gs.get_player(0).deck}")

    # 3. Play Shizuku
    print("\n--- Playing Shizuku ---")
    try:
        gs.process_action(0, 4, 0)  # Play from hand

        # 4. Handle Mandatory Discard (2 cards)
        if gs.get_player(0).pending_choice_type == "SELECT_HAND_DISCARD":
            print("Selecting 1st card to discard...")
            gs.process_action(0, 500, 0)
            print("Selecting 2nd card to discard...")
            gs.process_action(0, 500, 0)

    except Exception as e:
        print(f"Execution info: {e}")

    # 5. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    print(f"  Hand: {p0.hand} (Expected length 2)")
    print(f"  Discard: {p0.discard}")

    success = True
    if len(p0.hand) != 2:
        print(f"FAILURE: Expected hand size 2, found {len(p0.hand)}.")
        success = False

    if len(p0.discard) != 2:
        print(f"FAILURE: Expected discard size 2, found {len(p0.discard)}.")
        success = False

    if success:
        print("\nSUCCESS: Draw 2, Discard 2 ability works!")


if __name__ == "__main__":
    run_test()
