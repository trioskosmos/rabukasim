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
    print("TEST: Energy Charge (PL!SP-PR-004-PR)")
    print("============================================================")

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 1148 is Keke.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    # Hand: Keke + Card 10
    # Deck: Card 100
    gs.set_hand_cards(0, [1148, 10])
    gs.set_deck_cards(0, [100])

    print("Initial State:")
    p0 = gs.get_player(0)
    print(f"  Hand: {p0.hand}")
    print(f"  Deck: {p0.deck}")
    print(f"  Energy Count: {len(p0.energy_zone)}")

    # 3. Play Keke
    print("\n--- Playing Keke ---")
    try:
        gs.process_action(0, 4, 0)  # Play from hand

        # 4. Handle Optional Cost: Discard
        if gs.pending_choice_type == "CONFIRM":
            print("Confirming optional discard cost...")
            gs.process_action(0, 506, 0)  # Confirm (Yes)

        if gs.pending_choice_type == "SELECT_HAND_DISCARD":
            print("Selecting card to discard...")
            gs.process_action(0, 500, 0)  # Select Card 10

    except Exception as e:
        print(f"Execution info: {e}")

    # 5. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)

    energy_count = len(p0.energy_zone)
    tapped_count = sum(1 for t in p0.tapped_energy if t)

    print(f"  Energy Count: {energy_count}")
    print(f"  Tapped Energy Count: {tapped_count} (Expected: 1 for WAIT mode charge)")
    print(f"  Discard: {p0.discard}")

    success = True
    if energy_count != 1:
        print(f"FAILURE: Expected 1 energy card, found {energy_count}.")
        success = False

    if tapped_count != 1:
        print(f"FAILURE: Expected 1 tapped energy (WAIT mode), found {tapped_count}.")
        success = False

    if success:
        print("\nSUCCESS: Energy Charge ability works!")
    else:
        print("\nFAILURE: Energy Charge ability failed.")


if __name__ == "__main__":
    run_test()
