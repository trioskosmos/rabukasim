import os
import sys
import time

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.fast_mcts import HeuristicMCTS, HeuristicMCTSConfig

from engine.game.game_state import initialize_game


def demonstrate():
    print("========================================================")
    print(" LovecaSim - MCTS WITHOUT TRAINING DEMO                 ")
    print("========================================================")
    print(" This script demonstrates how MCTS can select intelligent")
    print(" moves using only game rules and simulation, with NO")
    print(" neural network or pre-training.")
    print("========================================================\n")

    # Initialize Game
    state = initialize_game()
    print(" [Init] Game initialized.")

    # Configure MCTS
    # 500 simulations should provide decent play without being too slow
    config = HeuristicMCTSConfig(num_simulations=500, c_puct=1.4)
    ai = HeuristicMCTS(config)

    print(f" [Config] Simulations: {config.num_simulations}")
    print(" [Config] Evaluation:  Heuristic (Lives + Blades)")

    # Run for a few turns
    for turn in range(1, 4):
        print(f"\n--- Turn {turn} (Player {state.current_player}) ---")

        # AI Thinks
        start = time.time()
        print(" [Thinking] AI is running simulations...")
        action = ai.search(state)
        duration = time.time() - start

        # Analysis
        root = ai.root
        total_visits = root.visit_count
        best_child = root.children[action]
        win_rate = best_child.value  # Average value [-1, 1]

        print(f" [Result] Selected Action: {action}")
        print(f" [Stats]  Time Taken:      {duration:.2f}s")
        print(f" [Stats]  Simulations:     {total_visits}")
        print(f" [Stats]  Est. Advantage:  {win_rate:.2f} (Interval: -1.0 to 1.0)")

        # Apply Move
        state = state.step(action)
        if state.is_terminal():
            print(f" [Game Over] Winner: {state.get_winner()}")
            break

    print("\n========================================================")
    print(" DEMO COMPLETE")
    print("========================================================")


if __name__ == "__main__":
    demonstrate()
