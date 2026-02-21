"""
Unified Agent Tournament Benchmark
Compares three methods:
1. Original: Full GameState + SmartHeuristicAgent (Std copy)
2. Fast: FastGameState + FastSmartAgent (Mutable)
3. Hybrid: Full GameState + SmartHeuristicAgent (Fast Pool + Optimized copy)
"""

import argparse
import os
import random
import sys
import time
from multiprocessing import Pool, cpu_count
from typing import Dict

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import RandomAgent, SmartHeuristicAgent, TrueRandomAgent

from tools.agent_tournament_fast import FastGameState, FastRandomAgent, FastSmartAgent, FastTrueRandomAgent

# ============================================================================
# STANDARDIZED TASK GENERATION
# ============================================================================


def generate_fixed_tasks(num_games: int, seed: int, member_db: Dict, live_db: Dict):
    """Generates consistent tasks and decks for all benchmarks."""
    random.seed(seed)
    np.random.seed(seed)

    tasks = []
    agent_pairs = [("Smart", "Random"), ("Smart", "Smart"), ("Random", "Random")]

    m_ids = list(member_db.keys())
    l_ids = list(live_db.keys())

    for i in range(num_games):
        a1, a2 = random.choice(agent_pairs)
        game_seed = seed + i

        # Pre-generate decks for both players
        # Standard: 40 members, 10 lives
        decks = []
        for _ in range(2):
            deck = [random.choice(m_ids) for _ in range(40)] + [random.choice(l_ids) for _ in range(10)]
            random.shuffle(deck)
            decks.append(deck)

        tasks.append({"agent_a": a1, "agent_b": a2, "seed": game_seed, "decks": decks})
    return tasks


# ============================================================================
# RUNNERS
# ============================================================================

# GLOBAL STORAGE FOR WORKERS
G_TASKS = []
G_MEMBER_DB = {}
G_LIVE_DB = {}


def init_worker(tasks, member_db, live_db):
    global G_TASKS, G_MEMBER_DB, G_LIVE_DB
    G_TASKS = tasks
    G_MEMBER_DB = member_db
    G_LIVE_DB = live_db

    # Force GameState initialization in worker
    GameState.member_db = G_MEMBER_DB
    GameState.live_db = G_LIVE_DB

    # Initialize JIT arrays locally in worker
    GameState._init_jit_arrays()

    # Debug: Check key types
    first_key = next(iter(G_MEMBER_DB.keys())) if G_MEMBER_DB else None
    # print(f"Worker initialized. DB size: {len(G_MEMBER_DB)}. First key type: {type(first_key)}")


# --- TRUE ORIGINAL RUNNER (Slow Deepcopy) ---
def run_true_original(task_idx):
    import copy

    task = G_TASKS[task_idx]
    random.seed(task["seed"])
    np.random.seed(task["seed"])

    # GameState.member_db already set in init_worker

    state = GameState()
    agent_map = {"Smart": SmartHeuristicAgent(), "Random": RandomAgent(), "TrueRandom": TrueRandomAgent()}
    agent_a, agent_b = agent_map[task["agent_a"]], agent_map[task["agent_b"]]

    for i, p in enumerate(state.players):
        p.main_deck = task["decks"][i][:]
        p.energy_deck = [2000] * 12
        for _ in range(5):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    first_player = random.randint(0, 1)
    state.first_player, state.current_player = first_player, first_player
    state.phase = Phase.MULLIGAN_P1

    for _ in range(2000):
        if state.game_over:
            break
        mask = state.get_legal_actions()
        if not np.any(mask):
            break
        pid = state.current_player
        active = agent_a if (first_player == 0 and pid == 0) or (first_player == 1 and pid == 1) else agent_b
        action = active.choose_action(state, pid)

        # SLOW DEEPCOPY (Explicitly replicate the OLD behavior)
        # We manually deepcopy since we already optimized GameState.copy()
        state = copy.deepcopy(state)
        state = state.step(action)

    return 1.0 if state.winner == 0 else (0.5 if state.winner == 2 else 0.0)


# --- OPTIMIZED RUNNER (Full Rules + Fast Copy) ---
def run_optimized(task_idx):
    task = G_TASKS[task_idx]
    random.seed(task["seed"])
    np.random.seed(task["seed"])

    GameState.member_db = G_MEMBER_DB
    GameState.live_db = G_LIVE_DB

    state = GameState()
    agent_map = {"Smart": SmartHeuristicAgent(), "Random": RandomAgent(), "TrueRandom": TrueRandomAgent()}
    agent_a, agent_b = agent_map[task["agent_a"]], agent_map[task["agent_b"]]

    for i, p in enumerate(state.players):
        p.main_deck = task["decks"][i][:]
        p.energy_deck = [2000] * 12
        for _ in range(5):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    first_player = random.randint(0, 1)
    state.first_player, state.current_player = first_player, first_player
    state.phase = Phase.MULLIGAN_P1

    for _ in range(2000):
        if state.game_over:
            break
        mask = state.get_legal_actions()
        if not np.any(mask):
            break
        pid = state.current_player
        active = agent_a if (first_player == 0 and pid == 0) or (first_player == 1 and pid == 1) else agent_b
        action = active.choose_action(state, pid)
        state = state.step(action)  # Uses the new optimized copy()

    return 1.0 if state.winner == 0 else (0.5 if state.winner == 2 else 0.0)


# --- HYBRID RUNNER (Full Rules + In-place) ---
def run_hybrid(task_idx):
    task = G_TASKS[task_idx]
    random.seed(task["seed"])
    np.random.seed(task["seed"])

    GameState.member_db = G_MEMBER_DB
    GameState.live_db = G_LIVE_DB

    state = GameState()
    agent_map = {"Smart": SmartHeuristicAgent(), "Random": RandomAgent(), "TrueRandom": TrueRandomAgent()}
    agent_a, agent_b = agent_map[task["agent_a"]], agent_map[task["agent_b"]]

    for i, p in enumerate(state.players):
        p.main_deck = task["decks"][i][:]
        p.energy_deck = [2000] * 12
        for _ in range(5):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    first_player = random.randint(0, 1)
    state.first_player, state.current_player = first_player, first_player
    state.phase = Phase.MULLIGAN_P1

    for _ in range(2000):
        if state.game_over:
            break
        mask = state.get_legal_actions()
        if not np.any(mask):
            break
        pid = state.current_player
        active = agent_a if (first_player == 0 and pid == 0) or (first_player == 1 and pid == 1) else agent_b
        action = active.choose_action(state, pid)

        # IN-PLACE
        state._process_rule_checks()
        if state.pending_choices:
            state._handle_choice(action)
        elif state.pending_effects:
            state._resolve_pending_effect(0)
        else:
            state._execute_action(action)
        while state.pending_effects and not state.pending_choices:
            state._resolve_pending_effect(0)
        state._process_rule_checks()

    return 1.0 if state.winner == 0 else (0.5 if state.winner == 2 else 0.0)


# --- FAST RUNNER (Simplified Rules) ---
def run_fast(task_idx):
    from tools.agent_tournament_fast import Phase as FastPhase

    task = G_TASKS[task_idx]
    random.seed(task["seed"])
    np.random.seed(task["seed"])
    state = FastGameState(G_MEMBER_DB, G_LIVE_DB)
    agent_map = {"Smart": FastSmartAgent(), "Random": FastRandomAgent(), "TrueRandom": FastTrueRandomAgent()}
    agent_a, agent_b = agent_map[task["agent_a"]], agent_map[task["agent_b"]]
    for i, p in enumerate(state.players):
        p.main_deck = task["decks"][i][:]
        p.energy_deck = [2000] * 12
        for _ in range(5):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))
    first_player = random.randint(0, 1)
    state.first_player, state.current_player = first_player, first_player
    state.phase = FastPhase.MULLIGAN_P1
    for _ in range(2000):
        if state.game_over:
            break
        mask = state.get_legal_actions()
        if not np.any(mask):
            break
        pid = state.current_player
        active = agent_a if (first_player == 0 and pid == 0) or (first_player == 1 and pid == 1) else agent_b
        action = active.choose_action(state, pid)
        state.step_inplace(action)
    return 1.0 if state.winner == 0 else (0.5 if state.winner == 2 else 0.0)


# ============================================================================
# MAIN BENCHMARK
# ============================================================================


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()
    global G_TASKS
    G_TASKS = generate_fixed_tasks(args.games, args.seed, m, l)
    workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    results_summary = []

    print(f"Benchmarking {args.games} games using {workers} workers...\n")

    methods = [
        ("TRUE ORIGINAL (Deepcopy)", run_true_original),
        ("OPTIMIZED (Fast Copy)", run_optimized),
        ("HYBRID (In-place)", run_hybrid),
        ("FAST (Simple Rules)", run_fast),
    ]

    for name, runner in methods:
        print(f"Running {name}...")
        start = time.time()
        with Pool(processes=workers, initializer=init_worker, initargs=(G_TASKS, m, l)) as pool:
            task_indices = list(range(len(G_TASKS)))
            results = pool.map(runner, task_indices)

        elapsed = time.time() - start
        ms_per_game = (elapsed / args.games) * 1000
        throughput = args.games / elapsed

        print(f"  Total Time: {elapsed:.2f}s")
        print(f"  Avg Rate:   {ms_per_game:.1f} ms/game")
        print(f"  Throughput: {throughput:.1f} games/sec")
        print(f"  Winrate:    {sum(results) / len(results) * 100:.1f}%\n")

        results_summary.append(
            {"name": name, "elapsed": elapsed, "ms_per_game": ms_per_game, "throughput": throughput, "results": results}
        )

    # Final Comparison
    print("=" * 70)
    print(f"{'Method':<30} | {'ms/game':<10} | {'Throughput':<10} | {'Consistency'}")
    print("-" * 70)
    # Optimized is our new "Gold Standard" for accuracy
    baseline_results = results_summary[1]["results"]
    for entry in results_summary:
        consistency = (
            "100%"
            if entry["results"] == baseline_results
            else ("DIFFERENT" if entry["name"] != "FAST (Simple Rules)" else "N/A (Simple)")
        )
        print(f"{entry['name']:<30} | {entry['ms_per_game']:<10.1f} | {entry['throughput']:<10.1f} | {consistency}")
    print("=" * 70)


if __name__ == "__main__":
    main()
