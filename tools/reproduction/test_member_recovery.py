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
    print("TEST: Member Recovery (PL!-sd1-002-SD)")
    print("============================================================")

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # PL!-sd1-002-SD is Card ID 248.
    # Target to recover: Card 1 (Honoka)
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    gs.set_stage_card(0, 0, 248)  # Slot 0: Source Card
    gs.set_discard_cards(0, [1])  # Discard: One Member card

    print(f"Initial State:")
    print(f"  Stage Slot 0: {gs.get_player(0).stage[0]}")
    print(f"  Discard Pile: {gs.get_player(0).discard}")
    print(f"  Hand: {gs.get_player(0).hand}")

    # 3. Trigger Ability (Index 0)
    print("\n--- Triggering Ability ---")
    # This should move card 248 to discard and 1 to hand.
    # If the engine is interactive (as recently refactored), this will PAUSE.
    # Since we aren't compiling, we check logic assuming it's interactive or automatic.
    try:
        res = gs.trigger_ability_on_card(0, 248, 0, 0)

        # Resumption logic (if needed for interactive)
        if gs.get_player(0).pending_choice_type == "SELECT_FROM_DISCARD":
            print("Pausing for interaction (Expected if engine is interactive)")
            gs.process_action(0, 500, 0)  # Choice index 0 (Honoka)

    except Exception as e:
        print(f"Note: Error during execution (expected if engine is in flux): {e}")

    # 4. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    stage_card = p0.stage[0]
    discard_pile = p0.discard
    hand = p0.hand

    print(f"  Stage Slot 0: {stage_card} (Expected: -1)")
    print(f"  Discard Pile: {discard_pile}")
    print(f"  Hand: {hand} (Expected to contain 1)")

    success = True
    if stage_card != -1:
        print("FAILURE: Card was not moved to discard.")
        success = False

    if 1 not in hand:
        print("FAILURE: Member was not recovered to hand.")
        success = False

    if success:
        print("\nSUCCESS: Member recovery ability works!")
    else:
        print("\nFAILURE: Member recovery ability failed.")


if __name__ == "__main__":
    run_test()
