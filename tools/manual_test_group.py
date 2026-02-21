import os
import sys
import traceback

import numpy as np

# Adjust path
sys.path.append(os.getcwd())

from game.game_state import Condition, ConditionType, GameState, MemberCard


def run_test():
    print("Starting manual test...")
    try:
        game = GameState()
        p0 = game.players[0]

        # Setup DB
        # Ensure dtype matches
        game.member_db[1] = MemberCard(
            card_id=1,
            card_no="L-001",
            name="Kanon",
            cost=1,
            hearts=np.zeros(6, dtype=np.int32),
            blade_hearts=np.zeros(7, dtype=np.int32),
            blades=1,
            group="ラブライブ！スーパースター!!",
        )

        print("Test 1: Zone Check Stage")
        p0.stage[0] = 1
        cond = Condition(ConditionType.GROUP_FILTER, {"group": "Liella!", "zone": "STAGE"})
        try:
            res = game._check_condition(p0, cond)
            print(f"Result: {res}")
            if not res:
                print("FAIL: Expected True")
        except:
            traceback.print_exc()

        print("Test: Clear Stage")
        p0.stage[0] = -1
        res = game._check_condition(p0, cond)
        print(f"Result (Empty): {res}")

        print("Test 2: Context Check Self")
        cond2 = Condition(ConditionType.GROUP_FILTER, {"group": "Liella!"})
        try:
            res2 = game._check_condition(p0, cond2, {"card_id": 1})
            print(f"Result: {res2}")
            if not res2:
                print("FAIL: Expected True")
        except:
            traceback.print_exc()

        print("Test 3: Alias Check (Liella! -> Series string)")
        cond3 = Condition(ConditionType.GROUP_FILTER, {"group": "Liella!"})
        # Card has full group string
        res3 = game._check_condition(p0, cond3, {"card_id": 1})
        print(f"Result: {res3}")

        print("DONE")

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    run_test()
