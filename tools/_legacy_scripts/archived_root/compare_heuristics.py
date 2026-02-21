import json
import random
import time

import engine_rust
import numpy as np


def load_db():
    with open("data/cards_compiled.json", "r") as f:
        return engine_rust.PyCardDatabase(f.read())


def get_test_deck():
    with open("data/cards_compiled.json", "r") as f:
        data = json.load(f)
    members = list(data["member_db"].keys())
    lives = list(data["live_db"].keys())
    members = [int(k) for k in members]
    lives = [int(k) for k in lives]

    # 50 random members, 3 lives, 10 energy (ID 20000)
    deck = random.choices(members, k=50)
    lives_deck = random.sample(lives, k=min(3, len(lives)))
    energy_deck = [20000] * 10
    return deck, energy_deck, lives_deck


def run_suite(num_games=50, mcts_sims=50):
    db = load_db()
    deck, energy, lives = get_test_deck()

    scenarios = [
        {"name": "Original(MCTS) vs Simple(MCTS)", "p0_h": 0, "p1_h": 1, "p0_s": mcts_sims, "p1_s": mcts_sims},
        {"name": "Original(Greedy) vs Simple(Greedy)", "p0_h": 0, "p1_h": 1, "p0_s": 0, "p1_s": 0},
        {"name": "Original(MCTS) vs Original(Greedy)", "p0_h": 0, "p1_h": 0, "p0_s": mcts_sims, "p1_s": 0},
        {"name": "Simple(MCTS) vs Simple(Greedy)", "p0_h": 1, "p1_h": 1, "p0_s": mcts_sims, "p1_s": 0},
    ]

    for sc in scenarios:
        print(f"\n=== Scenario: {sc['name']} ===")
        print(f"Configs: P0(H={sc['p0_h']}, Sims={sc['p0_s']}) vs P1(H={sc['p1_h']}, Sims={sc['p1_s']})")

        wins_p0 = 0
        wins_p1 = 0
        draws = 0
        turn_counts = []

        start_t = time.time()

        for i in range(num_games):
            game = engine_rust.PyGameState(db)
            seed = i * 777 + 123
            game.initialize_game_with_seed(
                list(deck), list(deck), list(energy), list(energy), list(lives), list(lives), seed
            )

            winner, turns = game.play_mirror_match(sc["p0_s"], sc["p1_s"], sc["p0_h"], sc["p1_h"])
            turn_counts.append(turns)

            if winner == 0:
                wins_p0 += 1
            elif winner == 1:
                wins_p1 += 1
            else:
                draws += 1

            if (i + 1) % 10 == 0:
                print(f"  Game {i + 1} done. (Avg Turns: {np.mean(turn_counts):.1f})")

        elapsed = time.time() - start_t
        print(f"--- Results ({num_games} games) ---")
        print(f"Time: {elapsed:.2f}s ({(elapsed / num_games):.2f}s/game)")
        print(f"P0 Wins: {wins_p0} ({wins_p0 / num_games * 100:.1f}%)")
        print(f"P1 Wins: {wins_p1} ({wins_p1 / num_games * 100:.1f}%)")
        print(f"Draws:   {draws}")
        print(f"Turns:   Avg={np.mean(turn_counts):.2f} Min={min(turn_counts)} Max={max(turn_counts)}")


if __name__ == "__main__":
    run_suite(num_games=50, mcts_sims=50)
