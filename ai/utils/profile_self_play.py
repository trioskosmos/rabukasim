"""Profile a single self-play game to identify bottlenecks."""

import json
import os
import sys
import time

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.models.training_config import POLICY_SIZE
from ai.utils.benchmark_decks import parse_deck


def profile_game(sims=100, neural_weight=0.3):
    db_path = "engine/data/cards_compiled.json"
    model_path = "ai/models/alphanet_best.onnx"

    with open(db_path, "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    db = engine_rust.PyCardDatabase(db_content)
    mcts = engine_rust.PyHybridMCTS(model_path, neural_weight)

    deck_file = "ai/decks/liella_cup.txt"
    main_deck, lives_deck, energy_deck = parse_deck(
        deck_file, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})
    )
    test_deck = (main_deck * 10)[:48]
    test_lives = (lives_deck * 10)[:12]
    test_energy = (energy_deck * 10)[:12]

    game = engine_rust.PyGameState(db)
    game.silent = True
    game.initialize_game(test_deck, test_deck, test_energy, test_energy, test_lives, test_lives)

    # Timing accumulators
    times = {
        "encode_state": 0.0,
        "mcts_suggestions": 0.0,
        "policy_build": 0.0,
        "dirichlet_noise": 0.0,
        "action_selection": 0.0,
        "game_step": 0.0,
        "other": 0.0,
    }
    counts = {"interactive": 0, "non_interactive": 0}

    step = 0
    t_game_start = time.perf_counter()

    while not game.is_terminal() and step < 500:
        phase = game.phase
        is_interactive = phase in [-1, 0, 4, 5]

        if is_interactive:
            counts["interactive"] += 1

            # 1. Encode State
            t0 = time.perf_counter()
            encoded = game.encode_state(db)
            times["encode_state"] += time.perf_counter() - t0

            # 2. MCTS Suggestions
            t0 = time.perf_counter()
            suggestions = mcts.get_suggestions(game, sims)
            times["mcts_suggestions"] += time.perf_counter() - t0

            # 3. Build Policy
            t0 = time.perf_counter()
            action_ids = []
            visit_counts = []
            total_visits = 0
            for action, score, visits in suggestions:
                if action < POLICY_SIZE:
                    action_ids.append(int(action))
                    visit_counts.append(visits)
                    total_visits += visits
            if total_visits == 0:
                legal = list(game.get_legal_action_ids())
                action_ids = [int(a) for a in legal if a < POLICY_SIZE]
                visit_counts = [1.0] * len(action_ids)
                total_visits = len(action_ids)
            probs = np.array(visit_counts, dtype=np.float32) / total_visits
            times["policy_build"] += time.perf_counter() - t0

            # 4. Dirichlet Noise
            t0 = time.perf_counter()
            noise = np.random.dirichlet([1.0] * len(probs))
            probs = 0.5 * probs + 0.5 * noise
            probs /= probs.sum()
            times["dirichlet_noise"] += time.perf_counter() - t0

            # 5. Action Selection
            t0 = time.perf_counter()
            if step < 60:
                action = np.random.choice(action_ids, p=probs)
            else:
                action = action_ids[np.argmax(probs)]
            times["action_selection"] += time.perf_counter() - t0

            # 6. Game Step
            t0 = time.perf_counter()
            game.step(int(action))
            times["game_step"] += time.perf_counter() - t0
        else:
            counts["non_interactive"] += 1
            t0 = time.perf_counter()
            game.step(0)
            times["game_step"] += time.perf_counter() - t0

        step += 1

    t_game_total = time.perf_counter() - t_game_start

    print(f"\n{'=' * 50}")
    print(f"PROFILE RESULTS ({sims} sims, weight={neural_weight})")
    print(f"{'=' * 50}")
    print(f"Total Game Time: {t_game_total:.3f}s")
    print(f"Steps: {step} ({counts['interactive']} interactive, {counts['non_interactive']} auto)")
    print(f"\n{'Operation':<25} {'Time (s)':<10} {'% Total':<10} {'Per Call (ms)':<15}")
    print("-" * 60)

    for op, t in sorted(times.items(), key=lambda x: -x[1]):
        pct = 100 * t / t_game_total if t_game_total > 0 else 0
        calls = counts["interactive"] if op != "game_step" else step
        per_call_ms = 1000 * t / calls if calls > 0 else 0
        print(f"{op:<25} {t:<10.4f} {pct:<10.1f} {per_call_ms:<15.3f}")

    print(f"\nTerminal: {game.is_terminal()}, Winner: {game.get_winner()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=100)
    parser.add_argument("--weight", type=float, default=0.3)
    args = parser.parse_args()
    profile_game(sims=args.sims, neural_weight=args.weight)
