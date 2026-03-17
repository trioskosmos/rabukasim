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
    print("TEST: Recover Live & Color (PL!N-bp1-003-R＋)")
    print("============================================================")

    if engine_rust is None:
        print("SKIPPING: engine_rust not found/compiled.")
        return

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 484 is Shizuku (R+). Live card 30000 in discard.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    gs.set_hand_cards(0, [484, 10])  # Shizuku and cost card
    gs.set_discard_cards(0, [30000])  # Live card to recover

    print("Initial State:")
    p0 = gs.get_player(0)
    print(f"  Hand: {p0.hand}")
    print(f"  Discard: {p0.discard}")

    # 3. Play Shizuku (Trigger ON_PLAY)
    print("\n--- Playing Shizuku ---")
    try:
        gs.process_action(0, 4, 0)  # Play from hand

        # 4. Handle Optional Discard Cost
        if gs.pending_choice_type == "CONFIRM":
            print("Confirming optional discard cost...")
            gs.process_action(0, 506, 0)  # Confirm (Yes)

        if gs.pending_choice_type == "SELECT_HAND_DISCARD":
            print("Selecting card to discard...")
            gs.process_action(0, 500, 0)  # Select Card 10

        # 5. Handle Live Recovery
        if gs.pending_choice_type == "SELECT_FROM_DISCARD":
            print("Selecting live card to recover...")
            gs.process_action(0, 500, 0)  # Select Card 30000

        # 6. Trigger Live Result (Trigger ON_LIVE_START)
        print("\n--- Starting Live Result ---")
        gs.set_live_cards(0, [30001])  # Set a live to result
        gs.process_action(0, 7, 0)  # Start live result Phase

        # 7. Handle Optional Color Select
        if gs.pending_choice_type == "CONFIRM":
            print("Confirming optional color select cost...")
            gs.process_action(0, 506, 0)  # Confirm (Yes)

        if gs.pending_choice_type == "COLOR_SELECT":
            print("Selecting color (Red)...")
            gs.process_action(0, 500, 1)  # Choice 1 (Red)

    except Exception as e:
        print(f"Execution info: {e}")

    # 8. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    print(f"  Hand: {p0.hand} (Expected to contain 30000)")

    hearts_list = gs.get_total_hearts(0)
    total_hearts = sum(hearts_list)
    print(f"  Hearts: {total_hearts} (Expected: 1 from color select)")

    success = True
    if 30000 not in p0.hand:
        print("FAILURE: Live card not recovered.")
        success = False

    if total_hearts != 1:
        print(f"FAILURE: Expected 1 heart, found {total_hearts}")
        success = False

    if success:
        print("\nSUCCESS: Recover Live & Color test logic verified (Script Complete)")


if __name__ == "__main__":
    run_test()
