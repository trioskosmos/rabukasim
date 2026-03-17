import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def hybrid_step_simulated(vec_env, actions, fallback_ratio=0.0):
    """
    Simulates a step where:
    1. We run the Numba Batch (Always overhead of full batch usually)
    2. We identify envs needing Python
    3. We run Python logic for them
    """

    # Run Numba for everyone (Assuming batch is efficient enough we just run it)
    vec_env.step(actions)

    # If ratio > 0, some percentage need Python "fixup"
    if fallback_ratio > 0.0:
        num_envs = len(actions)
        num_python = int(num_envs * fallback_ratio)

        # Simulate Python Sequential Work
        # Average engine step ~0.5ms to 1.0ms depending on logic
        # We'll be generous and say 0.2ms (200us) for a simple logic fix
        # But for full game logic fallback it's 1-2ms.
        # Let's say 0.5ms (500us) average.

        work_time = 0.0005 * num_python

        # Busy wait to simulate CPU load (sleep is inaccurate for small times)
        deadline = time.perf_counter() + work_time
        while time.perf_counter() < deadline:
            pass


def benchmark_hybrid():
    batch_size = 4096  # Realistic large batch
    num_steps = 100

    print(f"--- Hybrid Architecture Benchmark (Batch={batch_size}) ---")
    print("Baseline: Pure Numba (~700k SPS)")
    print("Python Cost Model: 0.5ms per environment fallback")

    vec_env = VectorGameState(batch_size)
    vec_env.reset()
    actions = np.ones(batch_size, dtype=np.int32)

    # WARMUP JIT
    vec_env.step(actions)
    print("Warmup complete.")

    ratios = [0.0, 0.001, 0.01, 0.05, 0.1, 1.0]  # 0%, 0.1%, 1%, 5%, 10%, 100%

    for r in ratios:
        print(f"\nTesting {r * 100:.1f}% Python Fallback ({int(batch_size * r)} envs)...")

        start = time.perf_counter()
        for _ in range(num_steps):
            hybrid_step_simulated(vec_env, actions, fallback_ratio=r)
        dur = time.perf_counter() - start

        total_steps = num_steps * batch_size
        sps = total_steps / dur

        print(f"-> Speed: {sps:,.0f} steps/sec")
        if r == 0.0:
            base_sps = sps
        else:
            print(f"   (Slowdown: {base_sps / sps:.1f}x)")


if __name__ == "__main__":
    benchmark_hybrid()
