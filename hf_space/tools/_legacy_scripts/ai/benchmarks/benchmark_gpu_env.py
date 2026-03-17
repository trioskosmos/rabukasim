"""
Benchmark Script: CPU VectorEnv vs GPU VectorEnvGPU
===================================================

Compares the throughput (Steps Per Second) of the existing CPU-based
Numba VectorEnv against the new GPU-resident VectorEnvGPU (mock or real).
"""

import os
import sys
import time

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState
from ai.vector_env_gpu import HAS_CUDA, VectorEnvGPU


def benchmark_cpu(num_envs=4096, steps=100):
    print(f"\n--- Benchmarking CPU VectorEnv ({num_envs} envs) ---")
    try:
        env = VectorGameState(num_envs)
        actions = np.zeros(num_envs, dtype=np.int32)

        # Warmup
        env.step(actions)

        start = time.time()
        for _ in range(steps):
            env.step(actions)
            # Simulate obs copy to "GPU" (conceptually)
            obs = env.get_observations()
        end = time.time()

        total_steps = num_envs * steps
        duration = end - start
        sps = total_steps / duration
        print(f"CPU Throughput: {sps:,.0f} SPS")
        return sps
    except Exception as e:
        print(f"CPU Benchmark Failed: {e}")
        return 0


def benchmark_gpu(num_envs=4096, steps=100):
    print(f"\n--- Benchmarking GPU VectorEnvGPU ({num_envs} envs) ---")
    if not HAS_CUDA:
        print(" [WARN] Running in MOCK mode (No CUDA). Results are invalid for performance.")

    try:
        env = VectorEnvGPU(num_envs)

        # Actions on Host (will be transferred) or Device
        actions = np.zeros(num_envs, dtype=np.int32)

        # Warmup
        env.step(actions)

        start = time.time()
        for _ in range(steps):
            # Step + Encode Obs
            obs, _, _, _ = env.step(actions)
            # In real scenario, obs is already on GPU, ready for PyTorch

        if HAS_CUDA:
            from numba import cuda

            cuda.synchronize()

        end = time.time()

        total_steps = num_envs * steps
        duration = end - start
        sps = total_steps / duration
        print(f"GPU Throughput: {sps:,.0f} SPS")
        return sps
    except Exception as e:
        print(f"GPU Benchmark Failed: {e}")
        return 0


if __name__ == "__main__":
    print("Starting Benchmark Comparison...")

    # 1. CPU Benchmark
    # Using smaller batch for CPU to be realistic about typical usage
    cpu_sps = benchmark_cpu(num_envs=128, steps=100)

    # 2. GPU Benchmark
    # GPU benefits from massive parallelism
    gpu_sps = benchmark_gpu(num_envs=4096, steps=100)

    print("\n--- Summary ---")
    print(f"CPU (128 envs): {cpu_sps:,.0f} SPS")
    print(f"GPU (4k envs):  {gpu_sps:,.0f} SPS")

    if not HAS_CUDA:
        print("\nNote: GPU results are based on Mock execution (Numpy fallbacks).")
        print("Real CUDA hardware required for accurate profiling.")
