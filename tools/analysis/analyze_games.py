import os
import sys
import time

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from engine.game.game_state import initialize_game


def run_analysis(num_games=20):
    print(f"Starting analysis of {num_games} games...")
    results = []

    start_time = time.time()

    for g_idx in range(num_games):
        game = initialize_game(deck_type="random_verified")
        steps = 0
        illegal_moves = 0

        while not game.is_terminal() and steps < 1000:
            masks = game.get_legal_actions()
            indices = np.where(masks)[0]

            if len(indices) == 0:
                print(f"Game {g_idx}: No legal actions at step {steps} phase {game.phase}")
                break

            action = np.random.choice(indices)

            # Check for illegal handle
            game.take_action(action)

            # If the engine marks it as illegal (usually by ending the game with winner -2)
            if getattr(game, "winner", 0) == -2:
                illegal_moves += 1
                break

            steps += 1

        results.append(
            {
                "game": g_idx,
                "steps": steps,
                "winner": game.get_winner(),
                "final_phase": game.phase,
                "illegal": illegal_moves > 0,
                "stalled": steps >= 1000,
            }
        )

        if (g_idx + 1) % 5 == 0:
            print(f"Completed {g_idx + 1} games...")

    end_time = time.time()

    # Summary
    illegal_count = sum(1 for r in results if r["illegal"])
    stall_count = sum(1 for r in results if r["stalled"])
    win_0 = sum(1 for r in results if r["winner"] == 0)
    win_1 = sum(1 for r in results if r["winner"] == 1)

    print("\n--- Analysis Summary ---")
    print(f"Total Games: {num_games}")
    print(f"Average Steps: {np.mean([r['steps'] for r in results]):.1f}")
    print(f"Illegal Terminations: {illegal_count}")
    print(f"Stalled Games (1000+ steps): {stall_count}")
    print(f"Player 0 Wins: {win_0}")
    print(f"Player 1 Wins: {win_1}")
    print(f"Total Time: {end_time - start_time:.1f}s")
    print("------------------------\n")

    if illegal_count > 0 or stall_count > 0:
        print("!!! ISSUES DETECTED !!!")
        for r in results:
            if r["illegal"] or r["stalled"]:
                print(
                    f"Game {r['game']}: Illegal={r['illegal']}, Stalled={r['stalled']}, Phase={r['final_phase']}, Steps={r['steps']}"
                )


if __name__ == "__main__":
    run_analysis()
