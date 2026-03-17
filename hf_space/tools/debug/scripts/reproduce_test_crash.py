# Standalone reproduction of test logic
import sys

# Add current dir to path
sys.path.append(".")

from engine.tests.framework.ability_test_generator import get_cards_with_condition

from engine.game.data_loader import CardDataLoader
from engine.game.enums import Phase
from engine.game.game_state import GameState


def reproduce():
    print("Loading data...")
    loader = CardDataLoader("engine/data/cards.json")
    member_db, live_db, _ = loader.load()
    GameState.member_db = member_db
    GameState.live_db = live_db

    print("Generating cases...")
    test_cases = get_cards_with_condition("GROUP_FILTER")
    print(f"Found {len(test_cases)} cases")

    if not test_cases:
        print("No cases found!")
        return

    print(f"Found {len(test_cases)} cases")

    for i, test_case in enumerate(test_cases):
        print(f"Running case {i}: {test_case.get('card_name')} ({test_case.get('card_id')})")

        # Setup state manually (mimic validated_game_state fixture)
        gs = GameState()
        # Initializing without reset_game

        cid = test_case["card_id"]
        trigger_name = test_case["trigger"]

        p = gs.players[0]
        # Reset player state for clean run
        p.hand = [cid] + [999] * 5
        p.hand_added_turn = [0] * 6
        p.stage = [None] * 3
        p.energy_zone = [2000] * 10
        p.tapped_energy = [False] * 10  # approximate

        if trigger_name == "ON_PLAY":
            gs.phase = Phase.MAIN
        elif trigger_name == "LIVE_START":
            p.stage[0] = cid
            p.live_zone = [1000]
            gs.phase = Phase.PERFORMANCE_P1
        elif trigger_name == "ACTIVATED":
            p.stage[0] = cid
            p.tapped_members = [False, False, False]
            gs.phase = Phase.MAIN

        action = 1 if trigger_name == "ON_PLAY" else 0
        if trigger_name == "ACTIVATED":
            action = 200

        try:
            gs.step(action)
        except Exception as e:
            print(f"CRASH ON CASE {i} (CID {cid}): {e}")
            import traceback

            traceback.print_exc()
            return  # Stop on first crash

    print("All cases completed.")


if __name__ == "__main__":
    try:
        reproduce()
    except Exception:
        import traceback

        traceback.print_exc()
