import os
import sys
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.mcts import MCTS, MCTSConfig

from engine.game.game_state import initialize_game


def benchmark_mcts():
    print("========================================================")
    print(" LovecaSim - MCTS SPEED BENCHMARK                       ")
    print("========================================================")

    sim_counts = [10, 25, 50, 100, 200]
    num_moves = 5

    print(f"Benchmarking over {num_moves} moves per config...\n")

    results = []

    for sims in sim_counts:
        print(f"--- Testing num_simulations = {sims} ---")
        config = MCTSConfig(num_simulations=sims)
        mcts = MCTS(config)

        # Initialize a fresh game for each test to be fair
        state = initialize_game()

        start_time = time.time()
        for _ in range(num_moves):
            # Select action (runs search)
            _ = mcts.search(state)
            mcts.reset()  # Reset tree to ensure full search each time

        total_time = time.time() - start_time
        avg_time = total_time / num_moves
        mps = 1.0 / avg_time

        print(f"  Avg Time/Move: {avg_time:.4f}s")
        print(f"  Moves/Sec:     {mps:.2f}")
        results.append((sims, mps))

    print("\n--- Summary ---")
    print(f"{'Simulations':<15} | {'Moves/Sec':<15} | {'Rel. Speed':<15}")
    base_mps = results[0][1]
    for sims, mps in results:
        rel = mps / base_mps
        print(f"{sims:<15} | {mps:<15.2f} | {rel:<15.2f}x")


if __name__ == "__main__":
    benchmark_mcts()
