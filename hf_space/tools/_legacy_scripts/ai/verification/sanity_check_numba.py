import os
import sys

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def sanity_check():
    print("--- Numba Scoring Sanity Check ---")
    env = VectorGameState(num_envs=1)
    env.reset()

    # 1. Play a Member with Blades
    # ID 586 (usually a member with stats)
    mem_id = 586
    env.batch_hand[0, 0] = mem_id
    env.step(np.array([mem_id], dtype=np.int32))
    print(f"Stage After Member: {env.batch_stage[0]}")

    # 2. Play a Live (ID 999 is vanilla live usually)
    live_id = 999
    # Ensure it's in hand
    env.batch_hand[0, 0] = live_id
    print(f"Score Before Live: {env.batch_scores[0]}")
    env.step(np.array([live_id], dtype=np.int32))
    print(f"Score After Live: {env.batch_scores[0]}")

    if env.batch_scores[0] > 0:
        print("SUCCESS: Engine Scored!")
    else:
        # Check why it failed
        # reqs = env.card_stats[live_id, 12:18]
        # hearts = ...
        print("FAILURE: Engine did not score.")
        print(f"Live Stats: {env.card_stats[live_id, 12:18]}")
        print(f"Member Stats: {env.card_stats[mem_id, 0:5]}")


if __name__ == "__main__":
    sanity_check()
