import random

import engine_rust


def analyze_game(seed=1236, sims=1000):
    print(f"=== Analyzing Game Loss: Seed={seed}, Sims={sims} ===")

    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    db = engine_rust.PyCardDatabase(db_json)

    member_pool = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    live_pool = [1000, 1001, 1002, 1003, 1004, 1005]

    game = engine_rust.PyGameState(db)
    rng = random.Random(seed)
    # Re-generate exact same decks
    p0_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]
    p1_deck = [rng.choice(member_pool) for _ in range(40)] + [rng.choice(live_pool) for _ in range(10)]
    p_energy = [200] * 12
    p0_live_ids = [rng.choice(live_pool) for _ in range(3)]
    p1_live_ids = [rng.choice(live_pool) for _ in range(3)]

    game.initialize_game_with_seed(p0_deck, p1_deck, p_energy, p_energy, p0_live_ids, p1_live_ids, seed)

    print(f"P0 Initial Hand: {game.get_player(0).hand}")
    print(f"P0 Initial Lives: {p0_live_ids}")
    step_count = 0
    while not game.is_terminal() and step_count < 100:
        cp = game.current_player
        ph = game.phase

        if cp == 0:
            hand = game.get_player(0).hand
            legal_mask = game.get_legal_actions()
            legal_indices = [idx for idx, val in enumerate(legal_mask) if val]
            if ph < 1:
                print(f"  [Step {step_count}] P0 Mulligan Legal: {legal_indices}")
            action = rng.choice(legal_indices) if legal_indices else 0

            # Log significant actions for P0
            if 1 <= action <= 180:
                idx = (action - 1) // 3
                slot = (action - 1) % 3
                cid = hand[idx]
                print(f"  [Step {step_count}] P0 PLAYED Card {cid} to Slot {slot}")
            elif 400 <= action <= 459:
                idx = action - 400
                cid = hand[idx]
                print(f"  [Step {step_count}] P0 SET LIVE Card {cid} (Hand: {hand})")
            elif action == 0 and ph == 4:
                print(f"  [Step {step_count}] P0 ENDED Main Phase")

            game.step(int(action))
        else:
            game.step_opponent_mcts(sims)

        # Log Score progression and success details
        p0 = game.get_player(0)
        s0 = p0.score
        if s0 > 0 and step_count % 1 == 0:  # Check every step if they scored
            # Check if score increased
            pass

        if ph == 8:  # Live Result phase - check successes
            if p0.score > 0:
                print(f"  [Step {step_count}] P0 Stats: Score={p0.score}")

        step_count += 1

    winner = game.get_winner()
    s0 = game.get_player(0).score
    s1 = game.get_player(1).score
    print(f"Winner: {winner} in {step_count} steps. Final Score: {s0} - {s1}")


if __name__ == "__main__":
    # Test Seed 1236 (Game 3) where it lost at 1000 and 4000 sims
    analyze_game(seed=1236, sims=4000)
