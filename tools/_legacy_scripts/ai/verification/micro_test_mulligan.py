import os
import sys

sys.path.append(os.getcwd())

from engine.game.game_state import initialize_game


def test_mulligan():
    game = initialize_game(deck_type="normal")
    print(f"Initial Phase: {game.phase}, Current Player: {game.current_player}")

    # Take a few mulligan selections
    game.step(300)
    game.step(301)
    print(
        f"After selections - Phase: {game.phase}, Current Player: {game.current_player}, Selection: {game.players[game.current_player].mulligan_selection}"
    )

    # Pass (Action 0)
    game.step(0)
    print(f"After P1 Pass - Phase: {game.phase}, Current Player: {game.current_player}")

    # Pass for P2
    game.step(0)
    print(f"After P2 Pass - Phase: {game.phase}, Current Player: {game.current_player}")


if __name__ == "__main__":
    test_mulligan()
