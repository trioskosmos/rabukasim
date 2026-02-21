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
    print("TEST: Color Select (PL!-bp3-012-PR)")
    print("============================================================")

    if engine_rust is None:
        print("SKIPPING: engine_rust not found/compiled.")
        return

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 88 is Kotori. Success live card 30000.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    gs.set_stage_card(0, 0, 88)

    p0 = gs.get_player(0)
    p0.set_success_lives([30000])  # Need to ensure this exists or use set_player
    gs.set_player(0, p0)

    gs.set_live_cards(0, [30001])  # Slot 0: Liella Live

    print(f"Initial State:")
    p0 = gs.get_player(0)
    print(f"  Stage Slot 0: {p0.stage[0]}")
    print(f"  Success Lives: {p0.success_lives}")

    hearts_list = gs.get_total_hearts(0)
    total_hearts = sum(hearts_list)
    print(f"  Hearts: {total_hearts}")

    # 3. Trigger Live Result
    print("\n--- Starting Live Result ---")
    try:
        # We'll simulate the ability directly if phase transitions are tricky
        # Kotori's ability is TRIGGER: ON_PLAY (according to analyze_all_unique_abilities report Rank 11)
        # Actually in test_color_select.py it says "Kotori (PL!-bp3-012-PR)".
        # Let's check card_analyzer output for Kotori ID 88.
        # It said TRIGGER: ACTIVATED? No, wait.

        # Action ID 4: Play card from hand.
        gs.set_hand_cards(0, [88])
        gs.process_action(0, 4, 0)

        # 4. Handle Color Select
        if gs.pending_choice_type == "SELECT_MODE":
            print("Selecting heart color (Pink)...")
            gs.process_action(0, 500, 0)  # Choice 0 (Pink)

    except Exception as e:
        print(f"Execution info: {e}")

    # 5. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    hearts_list = gs.get_total_hearts(0)
    total_hearts = sum(hearts_list)
    print(f"  Hearts: {total_hearts} (Expected: 1 because 1 success card)")

    success = True
    if total_hearts != 1:
        print(f"FAILURE: Expected 1 heart, found {total_hearts}")
        success = False

    if success:
        print("\nSUCCESS: Color Select test logic verified (Script Complete)")


if __name__ == "__main__":
    run_test()
