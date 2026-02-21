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
    print("TEST: Tap & Condition (PL!-PR-007-PR)")
    print("============================================================")

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Nozomi = 10. Liella Live = 30204 (Tiny Stars). Dummy Member = 1.
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    gs.set_hand_cards(0, [10])
    gs.set_stage_card(0, 0, 1)  # Slot 0: Dummy Member
    gs.set_live_cards(0, [30204])  # Slot 0: Liella Live

    print(f"Initial State:")
    print(f"  Hand: {gs.get_player(0).hand}")
    print(f"  Stage Slot 0 (Target): {gs.get_player(0).stage[0]}")
    p0 = gs.get_player(0)

    print(f"  Live Slot 0: {p0.live_zone[0]}")
    # get_total_hearts returns [u32; 7]
    hearts_list = gs.get_total_hearts(0)
    total_hearts = sum(hearts_list)
    print(f"  Hearts: {total_hearts}")

    # 3. Play Nozomi
    print("\n--- Playing Nozomi ---")
    try:
        # Action ID 4: Play card from hand.
        gs.process_action(0, 4, 0)

        # 4. Handle Optional Cost: Tap Member
        if gs.pending_choice_type == "CONFIRM":
            print("Confirming optional tap cost...")
            gs.process_action(0, 506, 0)  # Confirm (Yes)

        if gs.pending_choice_type == "TAP_MEMBER":
            print("Selecting member to tap (Slot 0)...")
            gs.process_action(0, 500, 0)  # Select member in slot 0

    except Exception as e:
        print(f"Execution info: {e}")

    # 5. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)

    # tapped_members is [bool; 3]
    is_tapped = p0.tapped_members[0]
    print(f"  Member 0 Tapped: {is_tapped} (Expected: True)")

    hearts_list = gs.get_total_hearts(0)
    total_hearts = sum(hearts_list)
    print(f"  Hearts: {total_hearts} (Expected: 1)")

    success = True
    if not is_tapped:
        print("FAILURE: Member was not tapped.")
        success = False

    if total_hearts != 1:
        print(f"FAILURE: Expected 1 heart, found {total_hearts}.")
        success = False

    if success:
        print("\nSUCCESS: Tap & Condition ability works!")
    else:
        print("\nFAILURE: Tap & Condition ability failed.")


if __name__ == "__main__":
    run_test()
