import argparse
import concurrent.futures
import json
import multiprocessing
import os
import random
import sys
import time

import numpy as np
from tqdm import tqdm

# Pin threads for performance
os.environ["RAYON_NUM_THREADS"] = "1"

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.utils.benchmark_decks import parse_deck

# Global cache for workers (optional, for NN mode)
_WORKER_MODEL_PATH = None


def worker_init(db_content, model_path=None):
    global _WORKER_DB, _WORKER_MODEL_PATH
    _WORKER_DB = engine_rust.PyCardDatabase(db_content)
    _WORKER_MODEL_PATH = model_path


def run_self_play_game(g_idx, sims, p0_deck_info, p1_deck_info):
    if _WORKER_DB is None:
        return None

    game = engine_rust.PyGameState(_WORKER_DB)
    game.silent = True
    p0_deck, p0_lives, p0_energy = p0_deck_info
    p1_deck, p1_lives, p1_energy = p1_deck_info

    game.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    game_states = []
    game_policies = []
    game_turns_remaining = []
    game_player_turn = []
    game_score_diffs = []

    # Target values will be backfilled after game ends

    step = 0
    max_turns = 150  # Estimated max turns for normalization
    while not game.is_terminal() and step < 1000:
        cp = game.current_player
        phase = game.phase

        # Interactive Phases: Mulligan (-1, 0), Main (4), LiveSet (5)
        is_interactive = phase in [-1, 0, 4, 5]

        if is_interactive:
            # Observation (now 1200)
            encoded = game.get_observation()
            if len(encoded) != 1200:
                # Pad to 1200 if engine mismatch
                if len(encoded) < 1200:
                    encoded = encoded + [0.0] * (1200 - len(encoded))
                else:
                    encoded = encoded[:1200]

            # Use MCTS with Original Heuristic (Teacher Mode)
            # If _WORKER_MODEL_PATH is None, we use pure MCTS
            h_type = "original" if _WORKER_MODEL_PATH is None else "hybrid"
            suggestions = game.search_mcts(
                num_sims=sims, seconds=0.0, heuristic_type=h_type, model_path=_WORKER_MODEL_PATH
            )

            # Build policy
            policy = np.zeros(2000, dtype=np.float32)
            action_ids = []
            visit_counts = []
            total_visits = 0
            for action, _, visits in suggestions:
                if action < 2000:
                    action_ids.append(int(action))
                    visit_counts.append(visits)
                    total_visits += visits

            if total_visits == 0:
                legal = list(game.get_legal_action_ids())
                action_ids = [int(a) for a in legal if a < 2000]
                visit_counts = [1.0] * len(action_ids)
                total_visits = len(action_ids)

            probs = np.array(visit_counts, dtype=np.float32) / total_visits

            # Add Noise (Dirichlet) for exploration
            if len(probs) > 1:
                noise = np.random.dirichlet([0.3] * len(probs))
                probs = 0.75 * probs + 0.25 * noise
                # CRITICAL: Re-normalize for np.random.choice float precision
                probs = probs / np.sum(probs)

            for i, aid in enumerate(action_ids):
                policy[aid] = probs[i]

            game_states.append(encoded)
            game_policies.append(policy)
            game_player_turn.append(cp)
            game_turns_remaining.append(float(game.turn))  # Store current turn, normalize later

            # Action Selection
            if step < 40:  # Explore in early game
                action = np.random.choice(action_ids, p=probs)
            else:  # Exploit
                action = action_ids[np.argmax(probs)]

            try:
                game.step(int(action))
            except:
                break
        else:
            # Auto-step
            try:
                game.step(0)
            except:
                break
        step += 1

    if not game.is_terminal():
        return None

    winner = game.get_winner()
    s0 = float(game.get_player(0).score)
    s1 = float(game.get_player(1).score)
    final_turn = float(game.turn)

    # Process rewards and normalized turns
    winners = []
    scores = []
    turns_normalized = []

    for i in range(len(game_player_turn)):
        p_idx = game_player_turn[i]

        # Win Signal (1, 0, -1)
        if winner == 2:
            winners.append(0.0)
        elif p_idx == winner:
            winners.append(1.0)
        else:
            winners.append(-1.0)

        # Score Diff (Normalized)
        diff = (s0 - s1) if p_idx == 0 else (s1 - s0)
        score_norm = np.tanh(diff / 50.0)  # Scale roughly to [-1, 1]
        scores.append(score_norm)

        # Turns Remaining (Normalized 0..1)
        # 1.0 at start, 0.0 at end
        rem = (final_turn - game_turns_remaining[i]) / max_turns
        turns_normalized.append(np.clip(rem, 0.0, 1.0))

    return {
        "states": np.array(game_states, dtype=np.float32),
        "policies": np.array(game_policies, dtype=np.float32),
        "winners": np.array(winners, dtype=np.float32),
        "scores": np.array(scores, dtype=np.float32),
        "turns_left": np.array(turns_normalized, dtype=np.float32),
        "outcome": {"winner": winner, "score": (s0, s1), "turns": game.turn},
    }


def generate_self_play(
    num_games=100,
    model_path="ai/models/alphanet.onnx",
    output_file="ai/data/self_play_0.npz",
    sims=100,
    weight=0.3,
    skip_rollout=False,
    workers=0,
):
    db_path = "engine/data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    # Load Decks (Standard Pool)
    deck_paths = [
        "ai/decks/aqours_cup.txt",
        "ai/decks/hasunosora_cup.txt",
        "ai/decks/liella_cup.txt",
        "ai/decks/muse_cup.txt",
        "ai/decks/nijigaku_cup.txt",
    ]
    decks = []
    for dp in deck_paths:
        if os.path.exists(dp):
            decks.append(parse_deck(dp, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})))

    all_states, all_policies, all_winners = [], [], []
    all_scores, all_turns = [], []
    total_completed = 0
    total_samples = 0
    chunk_size = 100  # Save every 100 games

    stats = {"wins": 0, "losses": 0, "draws": 0}

    if model_path == "None":
        model_path = None

    max_workers = workers if workers > 0 else min(multiprocessing.cpu_count(), 12)
    mode_str = "Teacher (Heuristic MCTS)" if model_path is None else "Student (Hybrid MCTS)"
    print(f"Starting Self-Play: {num_games} games using {max_workers} workers... Mode: {mode_str}")

    def save_chunk():
        nonlocal all_states, all_policies, all_winners, all_scores, all_turns
        if not all_states:
            return
        ts = int(time.time())
        path = output_file.replace(".npz", f"_chunk_{total_completed // chunk_size}_{ts}.npz")
        print(f"\n[Disk] Saving {len(all_states)} samples to {path}...")
        np.savez(
            path,
            states=np.array(all_states, dtype=np.float32),
            policies=np.array(all_policies, dtype=np.float32),
            winners=np.array(all_winners, dtype=np.float32),
            scores=np.array(all_scores, dtype=np.float32),
            turns_left=np.array(all_turns, dtype=np.float32),
        )
        all_states, all_policies, all_winners = [], [], []
        all_scores, all_turns = [], []

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=max_workers, initializer=worker_init, initargs=(db_content, model_path)
    ) as executor:
        pending = {}
        batch_cap = max_workers * 2
        games_submitted = 0

        pbar = tqdm(total=num_games)

        while total_completed < num_games or pending:
            while len(pending) < batch_cap and games_submitted < num_games:
                p0, p1 = random.randint(0, len(decks) - 1), random.randint(0, len(decks) - 1)
                f = executor.submit(run_self_play_game, games_submitted, sims, decks[p0], decks[p1])
                pending[f] = games_submitted
                games_submitted += 1

            if not pending:
                break

            done, _ = concurrent.futures.wait(pending.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
            for f in done:
                pending.pop(f)
                try:
                    res = f.result()
                    if res:
                        all_states.extend(res["states"])
                        all_policies.extend(res["policies"])
                        all_winners.extend(res["winners"])
                        all_scores.extend(res["scores"])
                        all_turns.extend(res["turns_left"])

                        total_completed += 1
                        total_samples += len(res["states"])

                        # Update stats
                        outcome = res["outcome"]
                        w_idx = outcome["winner"]
                        turns = outcome["turns"]

                        win_str = "DRAW" if w_idx == 2 else f"P{w_idx} WIN"

                        if w_idx == 2:
                            stats["draws"] += 1
                        elif w_idx == 0:
                            stats["wins"] += 1
                        else:
                            stats["losses"] += 1

                        # Reduce log spam for large runs
                        if total_completed % 10 == 0 or total_completed < 10:
                            print(
                                f" [Game {total_completed}] {win_str} in {turns} turns | Samples: {len(res['states'])} | Total W/L/D: {stats['wins']}/{stats['losses']}/{stats['draws']}"
                            )

                        pbar.update(1)
                        if total_completed % chunk_size == 0:
                            save_chunk()
                except Exception as e:
                    print(f"Game failed: {e}")

        pbar.close()

    if all_states:
        save_chunk()
    print(f"Self-play generation complete. Total samples: {total_samples}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--sims", type=int, default=100)
    parser.add_argument("--model", type=str, default="ai/models/alphanet_best.onnx")
    parser.add_argument("--weight", type=float, default=0.3)
    parser.add_argument("--workers", type=int, default=0, help="Number of workers (0 = auto)")
    parser.add_argument("--fast", action="store_true", help="Skip rollouts, use pure NN value (faster)")
    args = parser.parse_args()

    generate_self_play(
        num_games=args.games,
        model_path=args.model,
        sims=args.sims,
        weight=args.weight,
        skip_rollout=args.fast,
        workers=args.workers,
    )
