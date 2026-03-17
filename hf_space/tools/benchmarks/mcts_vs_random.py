import engine_rust
import numpy as np


def run_comparison(num_games=10):
    print(f"=== Running MCTS vs Random Comparison ({num_games} games) ===")

    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        json_str = f.read()
    db = engine_rust.PyCardDatabase(json_str)

    # We'll use PyVectorGameState to run games in parallel or just loop simple PyGameState
    # For a direct P0 (Random) vs P1 (MCTS) test, it's easier to use PyGameState in a loop.

    p1_wins = 0
    p0_wins = 0
    draws = 0

    # Card ID 115: Cost 4, Hearts: [Red:1, Yellow:1, Pink:1]
    # Card ID 1000: Live Req: [Red:1, Yellow:1, Pink:1]
    p_deck = [115] * 48
    p_energy = [115] * 48
    p_lives = [1000]  # Only 1 life to win!

    for i in range(num_games):
        game = engine_rust.PyGameState(db)
        game.initialize_game(p_deck, p_deck, p_energy, p_energy, p_lives, p_lives)

        # Game loop
        step_count = 0
        last_phase = -2
        last_player = -1
        stagnant_steps = 0

        while not game.is_terminal() and step_count < 500:
            cp = game.current_player
            ph = game.phase

            if ph == last_phase and cp == last_player:
                stagnant_steps += 1
            else:
                stagnant_steps = 0

            if step_count < 50 or stagnant_steps > 10:
                print(f"Step {step_count}: P{cp}, Phase {ph} (Stagnant: {stagnant_steps})")

            if stagnant_steps > 50:
                print(f"ERROR: Stagnant for 50 steps at Phase {ph}, Player {cp}. Breaking.")
                break

            last_phase = ph
            last_player = cp

            if cp == 0:
                # Player 0: Random
                legal_mask = game.get_legal_actions()
                legal_indices = [idx for idx, val in enumerate(legal_mask) if val]
                action = np.random.choice(legal_indices) if legal_indices else 0
                game.step(int(action))
            else:
                # Player 1: MCTS
                mcts_sims = 100
                game.step_opponent_mcts(mcts_sims)

            step_count += 1

        winner = game.get_winner()
        if winner == 1:
            p1_wins += 1
        elif winner == 0:
            p0_wins += 1
        else:
            draws += 1
            print(f"DEBUG: Game {i + 1} END: Phase {game.phase}, Winner {winner}, Steps {step_count}")

        print(f"Game {i + 1}: Winner = Player {winner if winner >= 0 else 'Draw'} (Steps: {step_count})")

    print("\nResults:")
    print(f"P0 (Random) Wins: {p0_wins}")
    print(f"P1 (MCTS) Wins: {p1_wins}")
    print(f"Draws: {draws}")
    print(f"MCTS Win Rate: {p1_wins / num_games * 100:.1f}%")


if __name__ == "__main__":
    run_comparison(5)
