import os
import sys

import numpy as np

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_env import VectorGameState


def test_start_order():
    print("TEST: Randomized Start Order (P1/P2)")

    env = VectorGameState(num_envs=100)
    env.reset()

    # Check Index 10 in global context
    is_second_flags = env.batch_global_ctx[:, 10]
    p1_count = np.sum(is_second_flags == 0)
    p2_count = np.sum(is_second_flags == 1)

    print("Total Envs: 100")
    print(f"P1 Starts: {p1_count}")
    print(f"P2 Starts: {p2_count}")

    # Assert reasonable distribution (e.g. within 30-70 range)
    assert 30 <= p1_count <= 70
    assert 30 <= p2_count <= 70

    # Verify Phase alignment
    # If P1 (0): Phase should be -1
    # If P2 (1): Phase should be 0 (Mulligan P2) because Opp (P1) already mulled.

    phases = env.batch_global_ctx[:, 8]

    for i in range(100):
        is_second = is_second_flags[i]
        ph = phases[i]

        if is_second == 0:  # Agent First
            if ph != -1:
                print(f"ERROR: Env {i} is P1 (0) but Phase is {ph} (Expected -1)")
                assert ph == -1
        else:  # Agent Second
            if ph != 0:
                print(f"ERROR: Env {i} is P2 (1) but Phase is {ph} (Expected 0)")
                assert ph == 0

    print("PASS: Start Order Randomization and Phase Initialization correct.")


if __name__ == "__main__":
    test_start_order()
