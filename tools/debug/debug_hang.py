import random
import time

import engine_rust


def debug_game(seed=1238, sims=1000):
    print(f"=== Debugging Matching Game 5: Seed={seed}, Sims={sims} ===")

    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)

    member_pool = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    live_pool = [1000, 1001, 1002, 1003, 1004, 1005]

    game = engine_rust.PyGameState(db)
    rng = random.Random(seed)
    p0_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]
    p1_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]
    p_energy = [200] * 12
    p0_live_ids = [rng.choice(live_pool) for _ in range(3)]
    p1_live_ids = [rng.choice(live_pool) for _ in range(3)]

    game.initialize_game_with_seed(p0_deck, p1_deck, p_energy, p_energy, p0_live_ids, p1_live_ids, seed)

    step_count = 0
    while not game.is_terminal() and step_count < 500:
        cp = game.current_player
        ph = game.phase

        start = time.time()
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
            dur = time.time() - start
            if step_count % 50 == 0:
                print(f"Step {step_count}: P0 Random took {dur:.4f}s")
        else:
            game.step_opponent_mcts(sims)
            dur = time.time() - start
            if dur > 1.0 or step_count % 10 == 0:
                print(f"Step {step_count}: P1 MCTS ({sims}) took {dur:.2f}s (Phase {ph})")

        step_count += 1

    print(f"Winner: {game.get_winner()} in {step_count} steps")


if __name__ == "__main__":
    debug_game()
