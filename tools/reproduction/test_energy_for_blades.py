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
    print("TEST: Energy for Blades (PL!HS-PR-018-PR)")
    print("============================================================")

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 277 is Rurino. Live card 30000.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    gs.set_stage_card(0, 0, 277)  # Slot 0: Rurino
    gs.set_energy_cards(0, [1000])  # Energy: One card
    gs.set_live_cards(0, [30000])  # Live: One card at index 0

    print(f"Initial State:")
    p0 = gs.get_player(0)
    print(f"  Stage Slot 0: {p0.stage[0]}")
    print(f"  Energy Zone: {p0.energy_zone}")
    print(f"  Blades: {gs.get_total_blades(0)}")

    # 3. Enter Live Result Phase
    print("\n--- Starting Live Result ---")
    try:
        # Action ID 7: Start Live Result (index 0)
        gs.process_action(0, 7, 0)

        # 4. Handle Optional Cost: Pay Energy
        if gs.pending_choice_type == "CONFIRM":
            print("Confirming optional energy payment...")
            gs.process_action(0, 506, 0)  # Confirm (Yes)

        # 5. Handle Energy Selection
        if gs.pending_choice_type == "TAP_ENERGY":
            print("Selecting energy card to pay...")
            gs.process_action(0, 500, 0)  # Select 1st energy card

    except Exception as e:
        print(f"Execution info: {e}")

    # 6. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)

    tapped_count = sum(1 for t in p0.tapped_energy if t)
    total_blades = gs.get_total_blades(0)

    print(f"  Tapped Energy: {tapped_count}")
    print(f"  Current Blades: {total_blades}")

    success = True
    if tapped_count != 1:
        print("FAILURE: Energy was not tapped.")
        success = False

    if total_blades < 2:
        print(f"FAILURE: Expected at least 2 blades, found {total_blades}.")
        success = False

    if success:
        print("\nSUCCESS: Energy for Blades ability works!")
    else:
        print("\nFAILURE: Energy for Blades ability failed.")


if __name__ == "__main__":
    run_test()
