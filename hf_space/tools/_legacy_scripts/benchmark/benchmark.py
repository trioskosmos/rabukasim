import time

import numpy as np

from engine.game.game_state import initialize_game


def run_benchmark_mode(fast_mode: bool, steps: int = 5000):
    mode_name = "Fast Mode" if fast_mode else "Normal Mode"
    print(f"Initializing {mode_name}...")
    gs = initialize_game(deck_type="vanilla")
    gs.fast_mode = fast_mode

    print(f"Running {steps} steps ({mode_name})...")
    start_time = time.perf_counter()

    step_func = gs.step
    get_legal = gs.get_legal_actions
    np.random.seed(42)  # Reset seed for fair comparison

    for i in range(steps):
        legal = get_legal()
        if np.any(legal):
            valid_indices = np.where(legal)[0]
            action = np.random.choice(valid_indices)
            step_func(action)

            if gs.game_over:
                gs = initialize_game(deck_type="vanilla")
                gs.fast_mode = fast_mode
                step_func = gs.step
                get_legal = gs.get_legal_actions

    end_time = time.perf_counter()
    duration = end_time - start_time
    sps = steps / duration

    print(f"{mode_name}: {steps} steps in {duration:.4f} seconds")
    print(f"{mode_name} Speed: {sps:.2f} steps/second")
    return sps


def run_benchmark():
    # Warmup
    print("Warming up...")
    run_benchmark_mode(True, 1000)
    print("-" * 40)

    normal_sps = run_benchmark_mode(False, 5000)
    print("-" * 40)
    fast_sps = run_benchmark_mode(True, 5000)

    improvement = (fast_sps - normal_sps) / normal_sps * 100
    print(f"\nImprovement: {improvement:.2f}%")


if __name__ == "__main__":
    run_benchmark()
