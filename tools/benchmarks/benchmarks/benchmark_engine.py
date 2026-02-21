import os
import sys
import time

# Add local directory to path
sys.path.append(os.getcwd())

from engine.game.game_state import initialize_game


def benchmark_observation(n_iterations=10000):
    print("Initializing game for benchmark...")
    game = initialize_game(use_real_data=True)

    # Warmup JIT
    print("Warming up JIT...")
    for _ in range(100):
        _ = game.get_observation()

    print(f"Running {n_iterations} iterations of get_observation()...")
    start_time = time.time()

    for _ in range(n_iterations):
        _ = game.get_observation()

    end_time = time.time()
    total_time = end_time - start_time
    ops_per_sec = n_iterations / total_time

    print(f"Total time: {total_time:.4f}s")
    print(f"Throughput: {ops_per_sec:.2f} obs/sec")

    return ops_per_sec


if __name__ == "__main__":
    try:
        benchmark_observation()
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback

        traceback.print_exc()
