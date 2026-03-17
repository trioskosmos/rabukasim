import os
import sys
import time

import numpy as np
import torch.multiprocessing as mp

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.train_gpu_workers import DistributedVectorEnv
from ai.vec_env_adapter import VectorEnvAdapter


def benchmark_distributed():
    print("========================================================")
    print(" LovecaSim - DISTRIBUTED vs SINGLE PROCESS BENCHMARK    ")
    print("========================================================")

    TOTAL_ENVS = 4096
    STEPS = 100

    # 1. Single Process (Multi-Threaded Numba)
    print("\n[1] Single Process (VectorEnvAdapter)")
    print(f"    Envs: {TOTAL_ENVS}, Numba Threads: Auto")

    env_single = VectorEnvAdapter(num_envs=TOTAL_ENVS)
    env_single.reset()
    actions = np.random.randint(0, 2, size=TOTAL_ENVS).astype(np.int32)

    # Warmup
    env_single.step(actions)

    start = time.time()
    for _ in range(STEPS):
        env_single.step(actions)
    end = time.time()

    single_throughput = (TOTAL_ENVS * STEPS) / (end - start)
    print(f"    Throughput: {single_throughput:,.2f} steps/sec")
    env_single.close()

    # 2. Distributed (Multi-Process)
    NUM_WORKERS = 4
    ENVS_PER_WORKER = TOTAL_ENVS // NUM_WORKERS

    print("\n[2] Distributed (DistributedVectorEnv)")
    print(f"    Workers: {NUM_WORKERS}, Envs/Worker: {ENVS_PER_WORKER}")

    # Set start method for MP
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        pass

    env_dist = DistributedVectorEnv(num_workers=NUM_WORKERS, envs_per_worker=ENVS_PER_WORKER)
    env_dist.reset()

    # Warmup
    env_dist.step_async(actions)
    env_dist.step_wait()

    start = time.time()
    for _ in range(STEPS):
        env_dist.step_async(actions)
        _ = env_dist.step_wait()
    end = time.time()

    dist_throughput = (TOTAL_ENVS * STEPS) / (end - start)
    print(f"    Throughput: {dist_throughput:,.2f} steps/sec")

    print("\n--- Comparison ---")
    print(f"Single Process: {single_throughput:,.2f} SPS")
    print(f"Distributed:    {dist_throughput:,.2f} SPS")
    if dist_throughput > single_throughput:
        print(f"Result: Distributed is {dist_throughput / single_throughput:.2f}x FASTER")
    else:
        print(f"Result: Distributed is {single_throughput / dist_throughput:.2f}x SLOWER (Overhead dominates)")

    env_dist.close()


if __name__ == "__main__":
    benchmark_distributed()
