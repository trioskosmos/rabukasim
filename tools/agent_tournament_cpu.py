"""
CPU-Only Agent Tournament
Runs only heuristic agents (no neural network).
Optimized for maximum CPU parallelism.
"""

import argparse
import os
import random
import subprocess
import sys
import time
from multiprocessing import Pool, cpu_count

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import (
    AbilityFocusAgent,
    ConservativeAgent,
    GambleAgent,
    RandomAgent,
    SmartHeuristicAgent,
    TrueRandomAgent,
)


class EloRating:
    def __init__(self, k_factor=32):
        self.k_factor = k_factor
        self.ratings = {}
        self.matches = {}
        self.wins = {}
        self.draws = {}

    def init_agent(self, name):
        if name not in self.ratings:
            self.ratings[name] = 1000
            self.matches[name] = 0
            self.wins[name] = 0
            self.draws[name] = 0

    def expected_score(self, rating_a, rating_b):
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update(self, agent_a, agent_b, score_a):
        self.init_agent(agent_a)
        self.init_agent(agent_b)

        self.matches[agent_a] += 1
        self.matches[agent_b] += 1

        if score_a == 1:
            self.wins[agent_a] += 1
        elif score_a == 0:
            self.wins[agent_b] += 1
        elif score_a == 0.5:
            self.draws[agent_a] += 1
            self.draws[agent_b] += 1

        k_a = self.k_factor * 2 if self.matches[agent_a] <= 20 else self.k_factor
        k_b = self.k_factor * 2 if self.matches[agent_b] <= 20 else self.k_factor

        ra = self.ratings[agent_a]
        rb = self.ratings[agent_b]

        ea = self.expected_score(ra, rb)
        eb = self.expected_score(rb, ra)

        self.ratings[agent_a] = ra + k_a * (score_a - ea)
        self.ratings[agent_b] = rb + k_b * ((1 - score_a) - eb)


def get_free_ram() -> int:
    """Returns free RAM in MB"""
    try:
        output = subprocess.check_output(["wmic", "OS", "get", "FreePhysicalMemory", "/Value"], encoding="utf-8")
        for line in output.splitlines():
            if "FreePhysicalMemory" in line:
                return int(line.split("=")[1].strip()) // 1024
        return 4096
    except Exception:
        return 4096


# Global storage for worker processes
G_AGENTS = {}
G_DB = {}


def init_worker(member_db, live_db):
    """Initialize worker process with pre-loaded data."""
    global G_AGENTS, G_DB

    GameState.member_db = member_db
    GameState.live_db = live_db
    G_DB = {"member": member_db, "live": live_db}

    # Pre-instantiate all heuristic agents (very low memory)
    G_AGENTS["TrueRandom"] = TrueRandomAgent()
    G_AGENTS["Random"] = RandomAgent()
    G_AGENTS["Smart"] = SmartHeuristicAgent()
    G_AGENTS["Ability"] = AbilityFocusAgent()
    G_AGENTS["Conservative"] = ConservativeAgent()
    G_AGENTS["Gamble"] = GambleAgent()


def run_single_game(args_tuple):
    """Run a single game between two agents."""
    agent_name_a, agent_name_b, game_seed = args_tuple

    global G_AGENTS, G_DB
    member_db = G_DB["member"]
    live_db = G_DB["live"]

    agent_a = G_AGENTS[agent_name_a]
    agent_b = G_AGENTS[agent_name_b]

    random.seed(game_seed)
    np.random.seed(game_seed)

    state = GameState(verbose=False)

    # Setup decks
    for p in state.players:
        m_ids = list(member_db.keys())
        l_ids = list(live_db.keys())
        p.energy_deck = [2000] * 12
        p.main_deck = [random.choice(m_ids) for _ in range(40)] + [random.choice(l_ids) for _ in range(10)]
        random.shuffle(p.main_deck)

        for _ in range(5):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    first_player = random.randint(0, 1)
    state.first_player = first_player
    state.current_player = first_player
    state.phase = Phase.MULLIGAN_P1

    # Run game
    turn_limit = 2000
    for turn in range(turn_limit):
        if state.game_over:
            break

        mask = state.get_legal_actions()
        if not np.any(mask):
            state.game_over = True
            state.winner = 2
            break

        pid = state.current_player
        if first_player == 0:
            active_agent = agent_a if pid == 0 else agent_b
        else:
            active_agent = agent_b if pid == 0 else agent_a

        action = active_agent.choose_action(state, pid)
        state = state.step(action)

    # Result
    if not state.game_over:
        s0 = len(state.players[0].success_lives)
        s1 = len(state.players[1].success_lives)
        winner = 0 if s0 > s1 else (1 if s1 > s0 else 2)
    else:
        winner = state.winner

    if winner == 2:
        return 0.5  # Draw
    if first_player == 0:
        return 1.0 if winner == 0 else 0.0
    else:
        return 0.0 if winner == 0 else 1.0


def main():
    parser = argparse.ArgumentParser(description="CPU-Only Agent Tournament (no neural network)")
    parser.add_argument("--games_per_pair", type=int, default=10, help="Games per matchup")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--workers", type=int, default=0, help="Number of workers (0=auto)")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    # CPU-only agents (no NNAgent)
    agent_names = ["TrueRandom", "Random", "Smart", "Ability", "Conservative", "Gamble"]

    elo = EloRating()
    for name in agent_names:
        elo.init_agent(name)

    matchups = {}
    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            matchups[(agent_names[i], agent_names[j])] = [0, 0, 0]

    # Load card data
    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()

    # Calculate optimal workers
    system_cores = cpu_count()
    ram_free = get_free_ram()
    ram_per_worker = 80  # Estimated ~80MB per worker for heuristic agents

    max_by_ram = ram_free // ram_per_worker
    optimal_workers = min(max_by_ram, system_cores - 1)

    if args.workers > 0:
        num_workers = args.workers
    else:
        num_workers = max(1, optimal_workers)

    print(f"System: {system_cores} cores, {ram_free}MB free RAM")
    print(f"Using {num_workers} workers (max by RAM: {max_by_ram})")

    # Build game tasks
    game_tasks = []
    task_metadata = []

    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            name_a, name_b = agent_names[i], agent_names[j]
            for game_idx in range(args.games_per_pair):
                game_tasks.append((name_a, name_b, args.seed + len(game_tasks)))
                task_metadata.append((name_a, name_b))

    print(f"\nStarting Tournament: {len(game_tasks)} games using {num_workers} workers...")
    start_time = time.time()

    with Pool(processes=num_workers, initializer=init_worker, initargs=(m, l)) as pool:
        results = list(pool.imap(run_single_game, game_tasks, chunksize=4))

    # Process Results
    for result, (name_a, name_b) in zip(results, task_metadata):
        elo.update(name_a, name_b, result)
        if result == 1.0:
            matchups[(name_a, name_b)][0] += 1
        elif result == 0.0:
            matchups[(name_a, name_b)][1] += 1
        else:
            matchups[(name_a, name_b)][2] += 1

    elapsed = time.time() - start_time
    print(f"\nTournament Complete in {elapsed:.2f}s ({elapsed / len(game_tasks):.3f}s/game)")

    # Print ELO Table
    print("\n" + "=" * 60)
    print(f"{'Agent':<15} | {'ELO':<6} | {'Wins':<6} | {'Draws':<6} | {'Win Rate'}")
    print("-" * 60)
    for name in sorted(agent_names, key=lambda x: elo.ratings[x], reverse=True):
        e_score = int(elo.ratings[name])
        w = elo.wins[name]
        d = elo.draws[name]
        m_count = elo.matches[name]
        wr = f"{(w / m_count * 100):.1f}%" if m_count > 0 else "N/A"
        print(f"{name:<15} | {e_score:<6} | {w:<6} | {d:<6} | {wr}")
    print("=" * 60)

    # Matchup Matrix
    print("\nMATCHUP WINRATE MATRIX (Row vs Column %)")
    header = " " * 15 + " | " + " | ".join([f"{n[:5]:<5}" for n in agent_names])
    print(header)
    print("-" * len(header))

    for row_name in agent_names:
        row_str = f"{row_name:<15} | "
        rates = []
        for col_name in agent_names:
            if row_name == col_name:
                rates.append(" --- ")
                continue
            pair = (row_name, col_name)
            if pair in matchups:
                w, l, d = matchups[pair]
                total = w + l + d
                rate = (w / total * 100) if total > 0 else 0
            else:
                pair = (col_name, row_name)
                l, w, d = matchups[pair]
                total = w + l + d
                rate = (w / total * 100) if total > 0 else 0
            rates.append(f"{rate:>4.1f}%")
        print(row_str + " | ".join(rates))
    print("=" * 60)


if __name__ == "__main__":
    main()
