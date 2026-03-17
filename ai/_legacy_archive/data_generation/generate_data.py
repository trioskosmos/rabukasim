import os
import sys

# Critical Performance Tuning:
# Each Python process handles 1 game. If we don't pin Rayon threads to 1,
# every process will try to use ALL CPU cores for its MCTS simulations,
# causing massive thread contention and slowing down generation by 5-10x.
os.environ["RAYON_NUM_THREADS"] = "1"

import argparse
import concurrent.futures
import glob
import json
import multiprocessing
import random
import time

import numpy as np
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import engine_rust

from ai.models.training_config import POLICY_SIZE
from ai.utils.benchmark_decks import parse_deck

# Global database cache for workers
_WORKER_DB = None
_WORKER_DB_JSON = None


def worker_init(db_content):
    global _WORKER_DB, _WORKER_DB_JSON
    _WORKER_DB = engine_rust.PyCardDatabase(db_content)
    _WORKER_DB_JSON = json.loads(db_content)


def run_single_game(g_idx, sims, p0_deck_info, p1_deck_info):
    if _WORKER_DB is None:
        return None

    game = engine_rust.PyGameState(_WORKER_DB)
    game.silent = True
    p0_deck, p0_lives, p0_energy = p0_deck_info
    p1_deck, p1_lives, p1_energy = p1_deck_info

    game.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    game_states = []
    game_policies = []
    game_player_turn = []

    step = 0
    while not game.is_terminal() and step < 1500:  # Slightly reduced limit for safety
        cp = game.current_player
        phase = game.phase

        is_interactive = phase in [-1, 0, 4, 5]

        if is_interactive:
            encoded = game.encode_state(_WORKER_DB)
            suggestions = game.get_mcts_suggestions(sims, engine_rust.SearchHorizon.TurnEnd)

            policy = np.zeros(POLICY_SIZE, dtype=np.float32)
            total_visits = 0
            best_action = 0
            most_visits = -1

            for action, score, visits in suggestions:
                if action < POLICY_SIZE:
                    policy[int(action)] = visits
                total_visits += visits
                if visits > most_visits:
                    most_visits = visits
                    best_action = int(action)

            if total_visits > 0:
                policy /= total_visits

            game_states.append(encoded)
            game_policies.append(policy)
            game_player_turn.append(cp)

            try:
                game.step(best_action)
            except:
                break
        else:
            try:
                game.step(0)
            except:
                break
        step += 1

    if not game.is_terminal():
        return None

    winner = game.get_winner()
    s0 = game.get_player(0).score
    s1 = game.get_player(1).score

    game_winners = []
    for cp in game_player_turn:
        if winner == 2:  # Draw
            game_winners.append(0.0)
        elif cp == winner:
            game_winners.append(1.0)
        else:
            game_winners.append(-1.0)

    # Game end summary for logging
    outcome = {"winner": winner, "p0_score": s0, "p1_score": s1, "turns": game.turn}

    # tqdm will handle the progress bar, but a periodic print is helpful
    if g_idx % 100 == 0:
        win_str = "P0" if winner == 0 else "P1" if winner == 1 else "Tie"
        print(
            f" [Game {g_idx}] Winner: {win_str} | Final Score: {s0}-{s1} | Turns: {game.turn} | States: {len(game_states)}"
        )

    return {"states": game_states, "policies": game_policies, "winners": game_winners, "outcome": outcome}


def generate_dataset(num_games=100, output_file="ai/data/data_batch_0.npz", sims=200, resume=False, chunk_size=5000):
    db_path = "data/cards_compiled.json"
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    deck_config = [
        ("Aqours", "ai/decks/aqours_cup.txt"),
        ("Hasunosora", "ai/decks/hasunosora_cup.txt"),
        ("Liella", "ai/decks/liella_cup.txt"),
        ("Muse", "ai/decks/muse_cup.txt"),
        ("Nijigasaki", "ai/decks/nijigaku_cup.txt"),
    ]
    decks = []
    deck_names = []
    print("Loading curriculum decks...")
    for name, dp in deck_config:
        if os.path.exists(dp):
            decks.append(parse_deck(dp, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})))
            deck_names.append(name)

    if not decks:
        p_deck = [124, 127, 130, 132] * 12
        p_lives = [1024, 1025, 1027]
        p_energy = [20000] * 10
        decks = [(p_deck, p_lives, p_energy)]
        deck_names = ["Starter-SD1"]

    total_completed = 0
    total_samples = 0
    stats = {}
    for i in range(len(decks)):
        for j in range(len(decks)):
            stats[(i, j)] = {"games": 0, "p0_wins": 0, "p0_total": 0, "p1_total": 0, "turns_total": 0}

    all_states, all_policies, all_winners = [], [], []

    def print_stats_table():
        n = len(deck_names)
        print("\n" + "=" * 95)
        print(f" DECK VS DECK STATISTICS (Progress: {total_completed}/{num_games} | Samples: {total_samples})")
        print("=" * 95)
        header = f"{'P0 \\ P1':<12} | " + " | ".join([f"{name[:10]:^14}" for name in deck_names])
        print(header)
        print("-" * len(header))
        for i in range(n):
            row = f"{deck_names[i]:<12} | "
            cols = []
            for j in range(n):
                s = stats[(i, j)]
                if s["games"] > 0:
                    wr = (s["p0_wins"] / s["games"]) * 100
                    avg0 = s["p0_total"] / s["games"]
                    avg1 = s["p1_total"] / s["games"]
                    avg_t = s["turns_total"] / s["games"]
                    cols.append(f"{wr:>3.0f}%/{avg0:^3.1f}/T{avg_t:<2.1f}")
                else:
                    cols.append(f"{'-':^14}")
            print(row + " | ".join(cols))
        print("=" * 95 + "\n")

    def save_current_chunk(is_final=False):
        nonlocal all_states, all_policies, all_winners
        if not all_states:
            return

        # Unique timestamped or indexed chunks to prevent overwriting during write
        chunk_idx = total_completed // chunk_size
        path = output_file.replace(".npz", f"_chunk_{chunk_idx}_{int(time.time())}.npz")

        print(f"\n[Disk] Attempting to save {len(all_states)} samples to {path}...")

        try:
            # Step 1: Save UNCOMPRESSED (Fast, less likely to fail mid-write)
            np.savez(
                path,
                states=np.array(all_states, dtype=np.float32),
                policies=np.array(all_policies, dtype=np.float32),
                winners=np.array(all_winners, dtype=np.float32),
            )

            # Step 2: VERIFY immediately
            with np.load(path) as data:
                if "states" in data.keys() and len(data["states"]) == len(all_states):
                    print(f" -> VERIFIED: {path} is healthy.")
                else:
                    raise IOError("Verification failed: File is truncated or keys missing.")

            # Reset buffers only after successful verification
            if not is_final:
                all_states, all_policies, all_winners = [], [], []

        except Exception as e:
            print(f" !!! CRITICAL SAVE ERROR: {e}")
            print(" !!! Data is still in memory, will retry next chunk.")

    if resume:
        existing = sorted(glob.glob(output_file.replace(".npz", "_chunk_*.npz")))
        if existing:
            total_completed = len(existing) * chunk_size
            print(f"Resuming from game {total_completed} ({len(existing)} chunks found)")

    max_workers = min(multiprocessing.cpu_count(), 16)
    print(f"Starting generation using {max_workers} workers...")

    try:
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers, initializer=worker_init, initargs=(db_content,)
        ) as executor:
            pending = {}
            batch_cap = max_workers * 2
            games_submitted = total_completed

            pbar = tqdm(total=num_games, initial=total_completed)
            last_save_time = time.time()

            while games_submitted < num_games or pending:
                current_time = time.time()
                # Autosave every 30 minutes
                if current_time - last_save_time > 1800:
                    print("\n[Timer] 30 minutes passed. Autosaving...")
                    save_current_chunk()
                    last_save_time = current_time

                while len(pending) < batch_cap and games_submitted < num_games:
                    p0, p1 = random.randint(0, len(decks) - 1), random.randint(0, len(decks) - 1)
                    f = executor.submit(run_single_game, games_submitted, sims, decks[p0], decks[p1])
                    pending[f] = (p0, p1)
                    games_submitted += 1

                done, _ = concurrent.futures.wait(pending.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
                for f in done:
                    p0, p1 = pending.pop(f)
                    try:
                        res = f.result()
                        if res:
                            all_states.extend(res["states"])
                            all_policies.extend(res["policies"])
                            all_winners.extend(res["winners"])
                            total_completed += 1
                            total_samples += len(res["states"])
                            pbar.update(1)

                            o = res["outcome"]
                            s = stats[(p0, p1)]
                            s["games"] += 1
                            if o["winner"] == 0:
                                s["p0_wins"] += 1
                            s["p0_total"] += o["p0_score"]
                            s["p1_total"] += o["p1_score"]
                            s["turns_total"] += o["turns"]

                            if total_completed % chunk_size == 0:
                                save_current_chunk()
                                print_stats_table()
                            # REMOVED: dangerous 100-game re-compression checkpoints
                    except Exception:
                        pass
            pbar.close()
    except KeyboardInterrupt:
        print("\nStopping...")

    save_current_chunk(is_final=True)
    print_stats_table()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-games", type=int, default=100)
    parser.add_argument("--output-file", type=str, default="ai/data/data_batch_0.npz")
    parser.add_argument("--sims", type=int, default=400)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=1000)
    args = parser.parse_args()
    generate_dataset(
        num_games=args.num_games,
        output_file=args.output_file,
        sims=args.sims,
        resume=args.resume,
        chunk_size=args.chunk_size,
    )
