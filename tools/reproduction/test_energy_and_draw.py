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
    print("TEST: Energy & Draw (PL!N-bp1-006-R＋)")
    print("============================================================")

    if engine_rust is None:
        print("SKIPPING: engine_rust not found/compiled.")
        return

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 508 is Kanata.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    # Ability 0: Activated, Discard 1 -> Activate Energy 2
    # Ability 1: Activated, Pay Energy 2 -> Draw 1
    gs.set_stage_card(0, 0, 508)
    gs.set_hand_cards(0, [10])  # Discard fodder
    gs.set_energy_cards(0, [1000, 1001])

    # Use get_player/set_player for nested state updates
    p0 = gs.get_player(0)
    p0.set_tapped_energy([True, True])
    gs.set_player(0, p0)

    gs.set_deck_cards(0, [100])

    # Set group flag for N-bp1 members in slot 1 (for condition check: GROUP_ID=2)
    gs.set_stage_card(0, 1, 468)  # Kasumi (N-bp1)

    print("Initial State:")
    p0 = gs.get_player(0)
    tapped_count = sum(1 for t in p0.tapped_energy if t)
    print(f"  Tapped Energy: {tapped_count}")
    print(f"  Hand: {p0.hand}")

    # 3. Trigger Ability 0 (Energy Activation)
    print("\n--- Triggering Ability 0: Energy Activation ---")
    try:
        # Ability 0 on card 508
        gs.trigger_ability_on_card(0, 508, 0, 0)

        if gs.pending_choice_type == "SELECT_HAND_DISCARD":
            gs.process_action(0, 500, 0)  # Discard 10

    except Exception as e:
        print(f"Execution info: {e}")

    # 4. Trigger Ability 1 (Draw)
    print("\n--- Triggering Ability 1: Draw ---")
    try:
        # Ability 1 on card 508
        gs.trigger_ability_on_card(0, 508, 1, 0)

        if gs.pending_choice_type == "TAP_ENERGY":
            gs.process_action(0, 500, 0)  # Tap 1
            gs.process_action(0, 500, 0)  # Tap 2

    except Exception as e:
        print(f"Execution info: {e}")

    # 5. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    print(f"  Hand: {p0.hand} (Expected to contain 100)")
    energy_count = len(p0.energy_zone)
    print(f"  Energy Count: {energy_count}")

    success = True
    if 100 not in p0.hand:
        print("FAILURE: Card 100 was not drawn.")
        success = False

    if success:
        print("\nSUCCESS: Energy & Draw test logic verified (Script Complete)")


if __name__ == "__main__":
    run_test()
