import os
import sys
import json

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
    print("TEST: Rin Hoshizora Recovery (PL!-sd1-005-SD)")
    print("============================================================")

    # 1. Load Data
    cards_compiled_path = os.path.join(project_root, "data", "cards_compiled.json")
    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        compiled_data = f.read()

    # 2. Setup Game State
    # Card 251 is Rin. Card 30000 is a Live card (dummy for discard).
    db = engine_rust.PyCardDatabase(compiled_data)
    gs = engine_rust.PyGameState(db)

    # Prepare Player 0
    gs.set_stage_card(0, 0, 251)  # Slot 0: Rin
    gs.set_discard_cards(0, [30000])  # Discard: One Live card

    print(f"Initial State:")
    print(f"  Stage Slot 0: {gs.get_player(0).stage[0]}")
    print(f"  Discard Pile: {gs.get_player(0).discard}")
    print(f"  Hand: {gs.get_player(0).hand}")

    # 3. Trigger Rin's Ability (Index 0)
    print("\n--- Triggering Rin's Ability ---")
    try:
        # Activated ability (7), slot 0, ability 0
        res = gs.trigger_ability_on_card(0, 251, 0, 0)
        print(f"Result: {res}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 4. Check Results
    print("\nFinal State:")
    p0 = gs.get_player(0)
    stage_card = p0.stage[0]
    discard_pile = p0.discard
    hand = p0.hand

    print(f"  Stage Slot 0: {stage_card} (Expected: -1)")
    print(f"  Discard Pile: {discard_pile} (Expected to contain 251, but not 30000)")
    print(f"  Hand: {hand} (Expected to contain 30000)")

    success = True
    if stage_card != -1:
        print("FAILURE: Rin was not moved to discard.")
        success = False

    if 30000 not in hand:
        print("FAILURE: Live card was not recovered to hand.")
        success = False

    if success:
        print("\nSUCCESS: Rin's ability worked correctly!")
    else:
        print("\nFAILURE: Rin's ability failed.")


if __name__ == "__main__":
    run_test()
