import random
import time

import engine_rust


def run_scaling_benchmark(start_sims=1000, games_per_config=3):
    print("=== MCTS Scaling Benchmark (Step Optimization) ===", flush=True)

    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)

    member_pool = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    live_pool = [1000, 1001, 1002, 1003, 1004, 1005]
    game_seeds = [1234 + i for i in range(games_per_config)]

    current_sims = start_sims
    results = []

    while True:
        print(f"\n>> CONFIG: {current_sims} sims/turn", flush=True)
        p1_wins = 0
        total_time = 0
        total_steps = 0

        for g_idx, seed in enumerate(game_seeds):
            game = engine_rust.PyGameState(db)
            rng = random.Random(seed)
            p0_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]
            p1_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]
            p_energy = [200] * 12
            p0_live_ids = [rng.choice(live_pool) for _ in range(3)]
            p1_live_ids = [rng.choice(live_pool) for _ in range(3)]

            game.initialize_game_with_seed(p0_deck, p1_deck, p_energy, p_energy, p0_live_ids, p1_live_ids, seed)

            start_time = time.time()
            step_count = 0
            while not game.is_terminal() and step_count < 500:
                cp = game.current_player
                if cp == 0:
                    legal_mask = game.get_legal_actions()
                    legal_indices = [idx for idx, val in enumerate(legal_mask) if val]
                    if not legal_indices:
                        game.step(0)
                    else:
                        if game.phase < 1:
                            action = 0 if rng.random() < 0.2 else rng.choice(legal_indices)
                        else:
                            action = rng.choice(legal_indices)
                        game.step(int(action))
                else:
                    game.step_opponent_mcts(current_sims)
                step_count += 1
                if step_count % 100 == 0:
                    print(
                        f"      .. g{g_idx + 1} at step {step_count} (time={time.time() - start_time:.1f}s)", flush=True
                    )

            game_time = time.time() - start_time
            total_time += game_time
            total_steps += step_count
            if game.get_winner() == 1:
                p1_wins += 1

            print(
                f"   Game {g_idx + 1}: Win={game.get_winner() == 1}, Steps={step_count}, Time={game_time:.2f}s",
                flush=True,
            )

        avg_time = total_time / games_per_config
        avg_steps = total_steps / games_per_config

        results.append(
            {"sims": current_sims, "win_rate": p1_wins / games_per_config, "avg_time": avg_time, "avg_steps": avg_steps}
        )

        if avg_time > 20.0:
            break
        current_sims *= 2
        if current_sims > 32000:
            break

    print("\n" + "=" * 75, flush=True)
    print(f"{'MCTS Sims':<10} | {'Win Rate':<10} | {'Avg Time':<12} | {'Avg Steps':<10}", flush=True)
    print("-" * 75, flush=True)
    for res in results:
        print(
            f"{res['sims']:<10} | {res['win_rate'] * 100:>8.1f}% | {res['avg_time']:>10.2f}s | {res['avg_steps']:>10.1f}",
            flush=True,
        )
    print("=" * 75, flush=True)


if __name__ == "__main__":
    run_scaling_benchmark(start_sims=1000, games_per_config=3)
