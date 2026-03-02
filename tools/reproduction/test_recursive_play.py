import os
import sys

# Add project root to path for engine_rust (though it may not be importable during refactor)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

try:
    import engine_rust
except ImportError:
    engine_rust = None


def run_test():
    print("============================================================")
    print("TEST: Recursive Play (PL!N-bp1-002-R＋)")
    print("============================================================")

    if engine_rust is None:
        print("SKIPPING: engine_rust not found/compiled.")
        return

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 468 is Kasumi.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    # Kasumi in Discard. Card 10 in hand for cost. 2 Energy for cost.
    gs.set_discard_cards(0, [468])
    gs.set_hand_cards(0, [10])
    gs.set_energy_cards(0, [1000, 1001])

    print("Initial State:")
    p0 = gs.get_player(0)
    print(f"  Discard: {p0.discard}")
    print(f"  Hand: {p0.hand}")
    print(f"  Energy: {len(p0.energy_zone)}")

    # 3. Trigger Ability from Discard
    print("\n--- Triggering Ability from Discard ---")
    try:
        # Ability 1 on card 468 (Index 1)
        gs.trigger_ability_on_card(0, 468, 1, 0)

        # 4. Handle Optional Discard Cost
        if gs.pending_choice_type == "SELECT_HAND_DISCARD":
            print("Selecting card to discard...")
            gs.process_action(0, 500, 0)  # Select Card 10

        # 5. Handle Energy Payment
        if gs.pending_choice_type == "TAP_ENERGY":
            print("Selecting 2 energy to pay...")
            gs.process_action(0, 500, 0)  # Select 1st energy
            gs.process_action(0, 500, 0)  # Select 2nd energy

        # 6. Handle Target Slot for PLAY
        if gs.pending_choice_type == "MOVE_MEMBER":
            print("Selecting slot 0 for play...")
            gs.process_action(0, 500, 0)  # Slot 0

    except Exception as e:
        print(f"Execution info: {e}")

    # 7. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)

    tapped_count = sum(1 for t in p0.tapped_energy if t)

    print(f"  Stage Slot 0: {p0.stage[0]} (Expected: 468)")
    print(f"  Discard: {p0.discard} (Expected: [10])")
    print(f"  Tapped Energy: {tapped_count} (Expected: 2)")

    success = True
    if p0.stage[0] != 468:
        print(f"FAILURE: Card 468 not on stage. Slot 0 = {p0.stage[0]}")
        success = False

    if 10 not in p0.discard:
        print(f"FAILURE: Card 10 not in discard. Discard = {p0.discard}")
        success = False

    if success:
        print("\nSUCCESS: Recursive Play test logic verified (Script Complete)")


if __name__ == "__main__":
    run_test()
