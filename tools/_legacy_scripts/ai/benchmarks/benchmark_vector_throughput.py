import os
import sys
import time

import numpy as np

# Append root to path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter as VectorEnv


def benchmark_throughput():
    # Configuration
    NUM_ENVS = 1024
    STEPS = 1000
    TOTAL_STEPS = NUM_ENVS * STEPS

    print(f"Initializing VectorEnv (Adapter) with {NUM_ENVS} environments...")

    # Initialize Environment
    # Adapter takes num_envs as first arg
    try:
        env = VectorEnv(num_envs=NUM_ENVS)
    except TypeError as e:
        print(f"Error initializing: {e}")
        return

    print("Resetting environment...")
    obs = env.reset()

    print(f"Running {STEPS} steps per environment (Total: {TOTAL_STEPS:,.0f})...")

    start_time = time.perf_counter()

    # Pre-allocate random actions to minimize python loop overhead
    # But real training generates actions every step.
    # We'll generate random actions inside loop to be somewhat realistic (Numpy overhead)
    # Action space is ~1200.

    for i in range(STEPS):
        actions = np.random.randint(0, 1200, size=NUM_ENVS, dtype=np.int32)
        obs, rewards, dones, infos = env.step(actions)

        if (i + 1) % 100 == 0:
            print(f"Step {i + 1}/{STEPS}...", end="\r")

    end_time = time.perf_counter()
    duration = end_time - start_time

    sps = TOTAL_STEPS / duration

    print("\n" + "=" * 40)
    print("BENCHMARK RESULTS (VectorEnv)")
    print(f"Envs:        {NUM_ENVS}")
    print(f"Steps:       {STEPS}")
    print(f"Total Ops:   {TOTAL_STEPS:,.0f}")
    print(f"Duration:    {duration:.4f}s")
    print(f"Throughput:  {sps:,.0f} Steps/Second (op/s)")
    print("=" * 40)


if __name__ == "__main__":
    benchmark_throughput()
