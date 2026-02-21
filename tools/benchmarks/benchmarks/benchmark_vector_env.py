import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def benchmark_vector_env():
    print("Benchmarking Vectorized Environments...")

    batch_sizes = [1, 32, 128, 512, 1024]
    num_steps = 1000

    for batch_size in batch_sizes:
        venv = VectorGameState(batch_size)
        venv.reset()

        # Random actions
        actions = np.random.randint(0, 2, size=batch_size).astype(np.int32)

        # Warmup
        venv.step(actions)

        start = time.time()
        for _ in range(num_steps):
            # Regenerate random actions each step (minor overhead)
            actions = np.random.randint(0, 2, size=batch_size).astype(np.int32)
            venv.step(actions)
        end = time.time()

        total_steps = batch_size * num_steps
        duration = end - start
        throughput = total_steps / duration

        print(f"Batch Size: {batch_size:4d} | Throughput: {throughput:12.2f} steps/sec")


if __name__ == "__main__":
    benchmark_vector_env()
