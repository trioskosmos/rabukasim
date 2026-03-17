import gc
import os
import sys

# Add project root directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from engine.game.game_state import GameState
from engine.models.card import MemberCard


def count_objects_in_state():
    # Initialize basic state
    GameState.member_db = {
        1: MemberCard(
            card_id=1,
            card_no="M1",
            name="Cheap",
            cost=1,
            blades=1,
            hearts=[1, 0, 0, 0, 0, 0, 0],
            blade_hearts=[1, 0, 0, 0, 0, 0, 0],
        ),
    }

    state = GameState()
    # Populate with some typical data
    p0 = state.players[0]
    p0.hand = [1] * 5
    p0.deck = [1] * 20
    p0.stage = [1, -1, -1]
    p0.energy_zone = [100] * 5

    # Force garbage collection
    gc.collect()

    print("Counting objects in a typical GameState...")

    # fast but rough recursion
    def recursive_len(o, seen):
        if id(o) in seen:
            return 0
        seen.add(id(o))

        count = 1

        if isinstance(o, dict):
            for k, v in o.items():
                count += recursive_len(k, seen)
                count += recursive_len(v, seen)
        elif isinstance(o, list):
            for i in o:
                count += recursive_len(i, seen)
        elif hasattr(o, "__dict__"):
            count += recursive_len(o.__dict__, seen)

        return count

    seen = set()
    total = recursive_len(state, seen)
    print(f"Approximate distinct python objects in GameState: {total}")

    import timeit

    t = timeit.timeit(lambda: state.copy(), number=1000)
    print(f"Time per copy: {t / 1000 * 1000:.3f} ms")


if __name__ == "__main__":
    count_objects_in_state()
