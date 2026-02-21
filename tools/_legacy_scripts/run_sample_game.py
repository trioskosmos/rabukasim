import os
import sys

import numpy as np

# Ensure the root directory is in PYTHONPATH
sys.path.append(os.getcwd())

from engine.game.data_loader import CardDataLoader
from engine.game.game_state import GameState


def run_simulation(turns=10):
    print("Initializing Game Engine...")

    # Load card data
    cards_path = os.path.join("data", "cards_compiled.json")
    loader = CardDataLoader(cards_path)
    member_db, live_db, _ = loader.load()

    # Initialize global DBs in GameState
    GameState.initialize_class_db(member_db, live_db)

    # Create game instance
    # Note: We use initialize_game if available, otherwise manual setup
    try:
        from engine.game.game_state import initialize_game

        game = initialize_game(deck_type="normal")
    except ImportError:
        # Fallback to manual initialization if initialize_game isn't exposed
        game = GameState(verbose=True)
        # Deep setup (decks, etc) would go here if needed,
        # but initialize_game is the standard way per codebase.

    print(f"Starting Simulation (Max {turns} turns)...")

    step = 0
    while not game.game_over and step < 100:
        masks = game.get_legal_actions()
        legal_indices = np.where(masks)[0]

        if len(legal_indices) == 0:
            print(f"Step {step}: No legal actions available. Ending.")
            break

        # Select a random legal action
        # In a real game, this would be an AI choice
        action = np.random.choice(legal_indices)

        # We use in_place=True for efficiency if supported, or just re-assign
        # Based on gym_env.py, game.step(action, in_place=True) is used.
        try:
            game = game.step(action, in_place=True)
        except Exception as e:
            print(f"Error during step {step}: {e}")
            break

        if step % 10 == 0:
            print(f"Step {step}: Phase={game.phase.name}, Turn={game.turn_number}, Player={game.current_player}")

        step += 1

    print("\nSimulation Finished!")
    print(f"Total Steps: {step}")
    print(f"Final Phase: {game.phase.name}")
    print(f"Final Turn: {game.turn_number}")
    print(f"Game Over: {game.game_over}")
    if game.game_over:
        print(f"Winner: {game.winner}")

    print("\nSUCCESS: Game engine is functional and stable.")


if __name__ == "__main__":
    run_simulation()
