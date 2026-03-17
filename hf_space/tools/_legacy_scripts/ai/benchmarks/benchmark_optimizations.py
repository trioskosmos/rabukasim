import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def benchmark():
    print("Starting optimization benchmark (Hot Run)...")
    num_envs = 1024
    vgs = VectorGameState(num_envs)

    # Warmup
    vgs.reset()
    vgs.get_observations()
    vgs.get_action_masks()
    vgs.step(np.zeros(num_envs, dtype=np.int32))

    # 1. Benchmark Reset
    start = time.time()
    vgs.reset()
    reset_time = time.time() - start
    print(f" [Reset] {num_envs} envs reset in {reset_time:.4f}s")

    # 2. Benchmark Observations (Parallel)
    start = time.time()
    obs = vgs.get_observations()
    obs_time = time.time() - start
    print(f" [Obs] {num_envs} envs encoded in {obs_time:.4f}s")

    # 3. Benchmark Action Masks (Parallel)
    start = time.time()
    masks = vgs.get_action_masks()
    mask_time = time.time() - start
    print(f" [Mask] {num_envs} envs masked in {mask_time:.4f}s")

    # 4. Benchmark Step (Parallel)
    actions = np.zeros(num_envs, dtype=np.int32)
    start = time.time()
    vgs.step(actions)
    step_time = time.time() - start
    print(f" [Step] {num_envs} envs stepped in {step_time:.4f}s")

    print("\nBenchmark Complete.")


if __name__ == "__main__":
    benchmark()
