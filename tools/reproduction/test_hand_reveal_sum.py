import sys
import os

sys.path.insert(0, os.getcwd())
import engine_rust

print(f"DEBUG: engine_rust loaded from {engine_rust.__file__}")
import traceback
import json

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

from tools.reproduction import utils


def test_hand_reveal_sum():
    print("============================================================")
    print("TEST: Rank 19: Hand Reveal Sum (PL!SP-bp1-003-P)")
    print("============================================================")

    # 1. Load Data
    db = utils.create_test_card_database()
    gs = utils.create_game_state(db)

    # 嵐 千砂都 (Sum Cost reveal)
    card_id = 1179

    # Needs cost 60 energy? Let's give plenty.
    gs.set_energy_cards(0, [901] * 60)

    # We need specific cards in hand to sum up to 10, 20, 30...
    # ID 0 is LL-bp1-001 (cost 20).
    # Sum = 20. Should trigger.
    gs.set_hand_cards(0, [card_id, 0])

    gs.set_player(0, gs.get_player(0))
    gs.phase = 4  # Main

    print(f"Playing card {card_id}...")
    try:
        # Play hand index 0 to slot 0
        # Formula: 1 + 0*3 + 0 = 1
        gs.step(1)

        # After playing, does it ask for choice?
        # Text: 10, 20, 30... sum -> BOOST_SCORE
        # Usually it's automatic if it only has one choice or is a sum check.

        # After playing, activate the ability
        print("Activating Ability 0...")
        # 200 + slot 0 * 10 + ab 0 = 200
        gs.step(200)

        print(f"Pending choice after activate: {gs.pending_choice_type}")

        # If it asks for cards to reveal:
        if gs.pending_choice_type == "SELECT_HAND":
            print("Revealing card ID 0 for sum cost...")
            # Select hand index 1 (which is ID 0 now)
            # Logic: Hand was [1178, 0]. Played 1178. Hand is [0].
            # Index of ID 0 is 0.
            gs.step(500)  # Select hand index 0

        print(f"Post-activation phase: {gs.phase}")

        # TRANSITION TO LIVE PHASE TO CHECK SCORE
        print("Transitioning to Live Phase...")
        gs.phase = 5  # LiveSet
        # Set a live card
        gs.set_live_cards(0, [1])  # Some live card
        gs.set_live_cards(1, [1])  # Opponent

        # Step through performance
        print("Stepping through performance...")
        # LiveSet -> Performance
        gs.step(0)
        gs.step(0)  # Need P2 to pass as well

        # Performance loop
        max_steps = 20
        while gs.phase in [6, 7] and max_steps > 0:
            gs.step(0)
            max_steps -= 1

        if gs.phase == 8:
            print("Triggering LiveResult calculation...")
            gs.step(0)

        print(f"Phase after performance: {gs.phase}")

        # Check performance results
        res_json = gs.performance_results
        last_res_json = gs.last_performance_results

        import json

        res = json.loads(res_json)
        last_res = json.loads(last_res_json)

        # Use last_res if res is empty or default
        if not res.get("0", {}).get("total_score"):
            print("Using Last Performance Results")
            res = last_res

        # Get Player 0 score
        p0_res = res.get("0", {})
        total_score = p0_res.get("total_score", 0)

        print(f"Player 0 Performance Score: {total_score}")

        # We have 0 hearts on board, but 1 bonus.
        # So expected score is 1.
        if total_score != 2:
            print(f"FAIL: Expected performance score 2, got {total_score}")
            return False

        print("PASS: Rank 19 logic verified.")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if test_hand_reveal_sum():
        print("\nRANK 19 PASS")
    else:
        print("\nRANK 19 FAIL")
        sys.exit(1)
