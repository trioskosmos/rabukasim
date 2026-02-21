import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def benchmark_oo_steps():
    print("Benchmarking OO Engine (LoveLiveCardGameEnv)...")
    env = LoveLiveCardGameEnv()
    env.reset()

    num_steps = 1000

    start = time.time()
    for _ in range(num_steps):
        # Sample legal action
        masks = env.action_masks()
        legal_indices = np.where(masks)[0]
        if len(legal_indices) == 0:
            env.reset()
            continue

        action = np.random.choice(legal_indices)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            env.reset()

    end = time.time()

    duration = end - start
    throughput = num_steps / duration

    print(f"Throughput: {throughput:.2f} steps/sec")


if __name__ == "__main__":
    benchmark_oo_steps()
