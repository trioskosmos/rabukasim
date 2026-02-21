import os
import sys

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from engine.game.game_state import initialize_game


def test_single_game():
    print("Starting detailed game simulation under GPU training conditions...")
    game = initialize_game(deck_type="random_verified")
    game.verbose = True
    steps = 0

    while not game.is_terminal() and steps < 1000:
        masks = game.get_legal_actions()
        indices = np.where(masks)[0]

        if len(indices) == 0:
            print(f"No legal actions at step {steps} phase {game.phase}")
            break

        action = np.random.choice(indices)

        print(f"Step {steps}: Phase {game.phase.name}, Action {action}")
        game.take_action(action)

        if getattr(game, "game_over", False):
            print(f"Game Over! Winner: {game.winner}")
            break

        steps += 1

    print("\n--- Test Summary ---")
    print(f"Steps: {steps}")
    print(f"Winner: {game.get_winner()}")
    print(f"Final Phase: {game.phase.name}")
    print("---------------------\n")


if __name__ == "__main__":
    test_single_game()
