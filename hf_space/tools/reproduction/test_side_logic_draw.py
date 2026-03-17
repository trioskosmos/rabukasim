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
    print("TEST: Side Logic Draw (PL!SP-bp1-002-R＋)")
    print("============================================================")

    if engine_rust is None:
        print("SKIPPING: engine_rust not found/compiled.")
        return

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 1163 is Keke (R+).
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    # Keke in Hand. 2 Energy in hand. 2 Cards in Deck.
    gs.set_hand_cards(0, [1163])
    gs.set_energy_cards(0, [1000, 1001])
    gs.set_deck_cards(0, [200, 201])

    print("Initial State:")
    p0 = gs.get_player(0)
    print(f"  Hand: {p0.hand}")
    print(f"  Deck: {p0.deck}")

    # 3. Play Keke to Left Side (Slot 0)
    print("\n--- Playing Keke to Left Side ---")
    try:
        # Action ID 4: Play card from hand.
        # Slot 0 is usually left side.
        gs.process_action(0, 4, 0)

        # 4. Handle Optional Energy Cost
        if gs.pending_choice_type == "CONFIRM":
            print("Confirming optional energy payment...")
            gs.process_action(0, 506, 0)  # Confirm (Yes)

        if gs.pending_choice_type == "TAP_ENERGY":
            print("Selecting 2 energy to pay...")
            gs.process_action(0, 500, 0)  # 1st
            gs.process_action(0, 500, 0)  # 2nd

    except Exception as e:
        print(f"Execution info: {e}")

    # 5. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)

    tapped_count = sum(1 for t in p0.tapped_energy if t)

    print(f"  Hand: {p0.hand} (Expected to contain 2 cards from deck)")
    print(f"  Tapped Energy: {tapped_count} (Expected: 2)")

    success = True
    if len(p0.hand) != 2:
        print(f"FAILURE: Expected 2 cards in hand, found {len(p0.hand)}. Hand: {p0.hand}")
        success = False

    if tapped_count != 2:
        print(f"FAILURE: Expected 2 tapped energy, found {tapped_count}")
        success = False

    if success:
        print("\nSUCCESS: Side Logic Draw test logic verified (Script Complete)")


if __name__ == "__main__":
    run_test()
