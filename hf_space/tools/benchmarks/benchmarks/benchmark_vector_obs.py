import os
import sys
import time

# Add local directory to path
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def benchmark_obs_encoding(num_envs=1024, n_iterations=1000):
    env = VectorGameState(num_envs)

    # Warmup
    _ = env.get_observations()

    print(f"Benchmarking Observation Encoding (Batch size: {num_envs}, {n_iterations} iterations)...")
    start_time = time.time()
    for _ in range(n_iterations):
        _ = env.get_observations()
    end_time = time.time()

    total_time = end_time - start_time
    throughput = (num_envs * n_iterations) / total_time

    print(f"Calculated {num_envs * n_iterations} observations in {total_time:.4f} seconds.")
    print(f"Throughput: {throughput:.2f} obs/sec")
    print(f"Latency: {total_time * 1000 / n_iterations:.4f} ms per batch")


if __name__ == "__main__":
    benchmark_obs_encoding()
