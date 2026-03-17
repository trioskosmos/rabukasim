import os
import sys
import time

import numpy as np

# Add local directory to path
sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def benchmark_gym_step(n_steps=5000):
    print("Initializing Env...")
    env = LoveLiveCardGameEnv()
    env.reset()

    print(f"Benchmarking Gym.step() with Vectorized Encoding ({n_steps} steps)...")

    start_time = time.time()
    steps_done = 0

    while steps_done < n_steps:
        # Generate random action (legality doesn't matter for obs speed check)
        # But to avoid instant game over, we try to pick legal ones if possible,
        # or just random.
        # Actually random interactions are fine.
        action = np.random.randint(0, 1000)

        obs, reward, terminated, truncated, info = env.step(action)
        steps_done += 1

        if terminated or truncated:
            env.reset()

    end_time = time.time()
    total_time = end_time - start_time
    fps = n_steps / total_time

    print(f"Completed {n_steps} steps in {total_time:.4f} seconds.")
    print(f"Gym FPS: {fps:.2f}")


if __name__ == "__main__":
    benchmark_gym_step()
