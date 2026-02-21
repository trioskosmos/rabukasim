import os
import sys

import numpy as np

# Ensure path
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def test_minimal_wrapper():
    print("--- Minimal VectorGameState Test ---")

    # 1. Setup
    num_envs = 1
    env = VectorGameState(num_envs)
    env.reset()

    # 2. Mock State
    # Force hand to have 586
    env.batch_hand[0, :].fill(0)
    env.batch_hand[0, 0] = 586
    env.batch_global_ctx[0, 3] = 1  # HD

    print(f"Hand Before: {env.batch_hand[0, :5]}")

    # 3. Predict/Action
    actions = np.array([586], dtype=np.int32)
    print(f"Executing Action: {actions[0]}")

    # 4. Step
    env.step(actions)

    print(f"Hand After: {env.batch_hand[0, :5]}")

    if env.batch_hand[0, 0] == 0:
        print("SUCCESS: Card removed from hand.")
    else:
        print("FAILURE: Card still in hand.")


if __name__ == "__main__":
    test_minimal_wrapper()
