"""Run 100 AI vs AI games to test for crashes."""

import time

import engine_rust as er


def run_stress_test(num_games: int = 100, mcts_sims: int = 50):
    print(f"Running {num_games} AI vs AI games at {mcts_sims} MCTS simulations...")

    # Load database once
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_json = f.read()
    db = er.PyCardDatabase(db_json)

    wins = [0, 0]
    crashes = 0

    start = time.time()

    for i in range(num_games):
        try:
            gs = er.PyGameState(db)
            gs.silent = True

            # Initialize with niji deck
            p0_deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 3
            p1_deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 3
            p0_lives = [1001, 1002, 1003]
            p1_lives = [1001, 1002, 1003]

            gs.initialize_game(p0_deck, p1_deck, [], [], p0_lives, p1_lives)

            result = gs.play_mirror_match(mcts_sims, mcts_sims, 0, 0)
            winner, turns = result

            if winner >= 0:
                wins[winner] += 1

            if (i + 1) % 10 == 0:
                elapsed = time.time() - start
                print(f"  Game {i + 1}/{num_games} - Winner: P{winner} ({turns} turns) - Elapsed: {elapsed:.1f}s")

        except Exception as e:
            crashes += 1
            print(f"  CRASH at game {i + 1}: {e}")

    elapsed = time.time() - start
    print("\n=== Results ===")
    print(f"Games: {num_games}")
    print(f"P0 Wins: {wins[0]}")
    print(f"P1 Wins: {wins[1]}")
    print(f"Crashes: {crashes}")
    print(f"Time: {elapsed:.1f}s ({elapsed / num_games:.2f}s per game)")

    return crashes == 0


if __name__ == "__main__":
    success = run_stress_test(100, 50)
    exit(0 if success else 1)
