import os
import random
import time

import engine_rust


def run_benchmark(sim_counts=[10, 50, 100, 250], games_per_config=5):
    print("=== MCTS VS Random Benchmark ===")
    print(f"Games per configuration: {games_per_config}")
    print(f"Simulations to test: {sim_counts}")

    db_path = "data/cards_compiled.json"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)

    # Deck configuration
    member_pool = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    live_pool = [1000, 1001, 1002, 1003, 1004, 1005]

    # Fixed seeds for reproducibility across configs
    game_seeds = [1234 + i for i in range(games_per_config)]

    results = {}

    for sims in sim_counts:
        print(f"\n[CONFIG] Testing MCTS with {sims} simulations...")
        p1_wins = 0
        p0_wins = 0
        draws = 0
        total_time = 0
        total_steps = 0

        for g_idx, seed in enumerate(game_seeds):
            game = engine_rust.PyGameState(db)
            game.silent = True

            # Use separate random state for deck generation to be consistent across sim_counts
            rng = random.Random(seed)
            p0_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]
            p1_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]

            # Energy decks (standard energy card ID 200)
            p_energy = [200] * 12

            # 3 Lives to win (passing RAW IDs)
            p0_live_ids = [rng.choice(live_pool) for _ in range(3)]
            p1_live_ids = [rng.choice(live_pool) for _ in range(3)]

            # Initialize with seed to ensure same shuffle/start
            game.initialize_game_with_seed(p0_deck, p1_deck, p_energy, p_energy, p0_live_ids, p1_live_ids, seed)

            start_time = time.time()
            step_count = 0
            # Safety loop to prevent infinite games
            while not game.is_terminal() and step_count < 500:
                cp = game.current_player
                # In Mulligan phase, action 0 is confirm. Random might toggle cards (300-359).
                # To make it faster, we might want to skip mulligan toggles for random if it gets stuck.

                if cp == 0:
                    # Random Agent (Player 0)
                    legal_mask = game.get_legal_actions()
                    legal_indices = [idx for idx, val in enumerate(legal_mask) if val]
                    if not legal_indices:
                        game.step(0)
                    else:
                        # Optimization: Random shouldn't loop mulligan forever
                        if game.phase < 1:  # Mulligan
                            action = 0 if rng.random() < 0.2 else rng.choice(legal_indices)
                        else:
                            action = rng.choice(legal_indices)
                        game.step(int(action))
                else:
                    # MCTS Agent (Player 1)
                    game.step_opponent_mcts(sims)
                step_count += 1

            game_time = time.time() - start_time
            total_time += game_time
            total_steps += step_count

            winner = game.get_winner()
            if winner == 1:
                p1_wins += 1
            elif winner == 0:
                p0_wins += 1
            else:
                draws += 1

            print(
                f"  Game {g_idx + 1}: Winner = Player {winner if winner >= 0 else 'Draw'} ({step_count} steps, {game_time:.2f}s)"
            )

        results[sims] = {
            "p1_wins": p1_wins,
            "p0_wins": p0_wins,
            "draws": draws,
            "avg_time": total_time / games_per_config,
            "avg_steps": total_steps / games_per_config,
            "win_rate": p1_wins / games_per_config,
        }

    print("\n" + "=" * 70)
    print(f"{'MCTS Sims':<10} | {'Win Rate':<10} | {'P1/P0/Draw':<12} | {'Avg Time':<10} | {'Avg Steps':<10}")
    print("-" * 70)
    for sims in sim_counts:
        res = results[sims]
        win_rate = f"{res['win_rate'] * 100:>8.1f}%"
        counts = f"{res['p1_wins']}/{res['p0_wins']}/{res['draws']}"
        avg_t = f"{res['avg_time']:>8.2f}s"
        avg_s = f"{res['avg_steps']:>8.1f}"
        print(f"{sims:<10} | {win_rate} | {counts:<12} | {avg_t} | {avg_s}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark([10, 50, 100, 250], games_per_config=5)
