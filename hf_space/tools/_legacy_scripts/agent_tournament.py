import argparse
import os
import random
import sys
import time
from multiprocessing import Pool, cpu_count
from typing import Tuple

import numpy as np

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import (
    AbilityFocusAgent,
    ConservativeAgent,
    GambleAgent,
    NNAgent,
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


import subprocess


class ResourceMonitor:
    @staticmethod
    def get_free_vram() -> int:
        """Returns free VRAM in MB"""
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], encoding="utf-8"
            )
            return int(output.strip().split("\n")[0])
        except Exception:
            return 999999  # Treat as infinite if no NVIDIA GPU

    @staticmethod
    def get_free_ram() -> int:
        """Returns free RAM in MB"""
        try:
            output = subprocess.check_output(["wmic", "OS", "get", "FreePhysicalMemory", "/Value"], encoding="utf-8")
            # Output format: FreePhysicalMemory=XXXX
            for line in output.splitlines():
                if "FreePhysicalMemory" in line:
                    return int(line.split("=")[1].strip()) // 1024
            return 4096  # Fallback
        except Exception:
            return 4096


def profile_worker_memory(loader, device_nn) -> Tuple[int, int]:
    """Measures RAM/VRAM cost of a single worker after initialization."""
    print(f"Profiling process memory for device: {device_nn}...")

    # 1. Base measurement
    ram_before = ResourceMonitor.get_free_ram()
    vram_before = ResourceMonitor.get_free_vram()

    # 2. Initialize (this will load models into the current process)
    m, l, e = loader.load()
    GameState.member_db = m
    GameState.live_db = l

    # Force NN load
    nn = NNAgent(device=device_nn)

    # 3. Measurement after
    ram_after = ResourceMonitor.get_free_ram()
    vram_after = ResourceMonitor.get_free_vram()

    ram_cost = max(50, ram_before - ram_after)
    vram_cost = max(0, vram_before - vram_after)

    # Clean up to be safe (though we usually exit soon)
    del nn
    import torch

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print(f"  Profiled Cost: RAM ~{ram_cost}MB, VRAM ~{vram_cost}MB")
    return ram_cost, vram_cost


# Global storage for worker processes to avoid re-loading models
G_AGENTS = {}
G_DB = {}


def init_worker(member_db, live_db, device_nn):
    """Initialize worker process: load models and DBs once."""
    global G_AGENTS, G_DB

    # Set class-level DBs for GameState
    GameState.member_db = member_db
    GameState.live_db = live_db
    G_DB = {"member": member_db, "live": live_db}

    # Pre-instantiate heuristic agents (low memory)
    G_AGENTS["TrueRandom"] = TrueRandomAgent()
    G_AGENTS["Random"] = RandomAgent()
    G_AGENTS["Smart"] = SmartHeuristicAgent()
    G_AGENTS["Ability"] = AbilityFocusAgent()
    G_AGENTS["Conservative"] = ConservativeAgent()
    G_AGENTS["Gamble"] = GambleAgent()

    # NN is loaded LAZILY to save VRAM/RAM if worker only handles heuristic games
    G_AGENTS["NN"] = None
    G_AGENTS["device_nn"] = device_nn


def get_agent(name):
    """Retrieve agent, instantiating NN lazily if needed."""
    global G_AGENTS
    if name == "NN" and G_AGENTS["NN"] is None:
        # Load NN now
        device = G_AGENTS["device_nn"]
        # print(f"  [Worker {os.getpid()}] Lazy-loading NN on {device}...")
        G_AGENTS["NN"] = NNAgent(device=device)
    return G_AGENTS[name]


def run_single_game(args_tuple):
    """Wrapper for parallel execution using pre-initialized worker agents"""
    agent_name_a, agent_name_b, game_seed = args_tuple

    global G_AGENTS, G_DB
    member_db = G_DB["member"]
    live_db = G_DB["live"]

    # Use pre-instantiated agents (or lazy load NN)
    agent_a = get_agent(agent_name_a)
    agent_b = get_agent(agent_name_b)

    # Set seed for this specific game
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
        return 1.0 if winner == 0 else 0.0  # 1.0 if A wins
    else:
        return 0.0 if winner == 0 else 1.0  # 1.0 if B wins (pid 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games_per_pair", type=int, default=10, help="Games per matchup (Round Robin mode)")
    parser.add_argument("--total_games", type=int, default=0, help="Total games in tournament (Random Balanced mode)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--workers", type=int, default=0, help="Number of worker processes (0=auto)")
    parser.add_argument("--benchmark", action="store_true", help="Run 1-game-per-pairing GPU vs CPU benchmark")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    agent_names = ["TrueRandom", "Random", "Smart", "Ability", "Conservative", "Gamble", "NN"]

    elo = EloRating()
    for name in agent_names:
        elo.init_agent(name)

    matchups = {}
    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            matchups[(agent_names[i], agent_names[j])] = [0, 0, 0]

    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()

    import torch

    gpu_available = torch.cuda.is_available()
    system_cores = cpu_count()

    # Profiling and Worker Calculation
    def calculate_optimal_workers(device):
        ram_initial = ResourceMonitor.get_free_ram()
        vram_initial = ResourceMonitor.get_free_vram()
        print(f"  Initial free: RAM={ram_initial}MB, VRAM={vram_initial}MB")

        # Profile cost
        ram_cost, vram_cost = profile_worker_memory(loader, device)

        # Free memory AFTER profiling (since the model might still be partially resident or cached)
        ram_free = ResourceMonitor.get_free_ram()
        vram_free = ResourceMonitor.get_free_vram()

        # Safety margin (25% for high-load stability)
        safe_ram = ram_free - (ram_initial * 0.10)  # Reserve at least 10% of total free plus some buffer
        safe_vram = vram_free - (vram_initial * 0.10)

        max_by_ram = int(max(0, safe_ram) // ram_cost) if ram_cost > 0 else system_cores
        max_by_vram = int(max(0, safe_vram) // vram_cost) if vram_cost > 0 else system_cores

        print(f"  Limits: Max by RAM={max_by_ram}, Max by VRAM={max_by_vram}, Cores-1={system_cores - 1}")
        optimal = min(max_by_ram, max_by_vram, system_cores - 1)

        final_workers = max(1, optimal)
        print(f"  Final selected workers for {device}: {final_workers}")
        return final_workers

    if args.benchmark:
        print("\n" + "=" * 60)
        print("RUNNING GPU VS CPU BENCHMARK WITH DYNAMIC SCALING")
        print("=" * 60)

        other_agents = [n for n in agent_names if n != "NN"]
        # For a proper comparison, we want a significant number of games
        # to fill up the parallel pipeline.
        bench_games_count = len(other_agents) * 5
        bench_tasks = []
        for i in range(bench_games_count):
            other = other_agents[i % len(other_agents)]
            bench_tasks.append(("NN", other, args.seed + 1000 + i))

        # CPU Benchmark
        cpu_workers = args.workers if args.workers > 0 else calculate_optimal_workers("cpu")
        print(f"Benchmarking CPU ({len(bench_tasks)} games using {cpu_workers} workers)...")
        start_cpu = time.time()
        with Pool(processes=cpu_workers, initializer=init_worker, initargs=(m, l, "cpu")) as pool:
            pool.map(run_single_game, bench_tasks)
        cpu_time = time.time() - start_cpu

        # GPU Benchmark
        gpu_device = "cuda" if gpu_available else "cpu"
        gpu_workers = args.workers if args.workers > 0 else calculate_optimal_workers(gpu_device)
        print(f"Benchmarking GPU ({len(bench_tasks)} games using {gpu_workers} workers)...")
        start_gpu = time.time()
        with Pool(processes=gpu_workers, initializer=init_worker, initargs=(m, l, gpu_device)) as pool:
            pool.map(run_single_game, bench_tasks)
        gpu_time = time.time() - start_gpu

        print("\nBENCHMARK RESULTS (Dynamic Scaling):")
        print(f"  CPU: {cpu_workers} workers, {cpu_time:.2f}s total ({cpu_time / len(bench_tasks):.2f}s/game)")
        print(f"  GPU: {gpu_workers} workers, {gpu_time:.2f}s total ({gpu_time / len(bench_tasks):.2f}s/game)")
        if gpu_time > 0:
            print(f"  Overall Throughput Speedup: {cpu_time / gpu_time:.2f}x")
        print("=" * 60 + "\n")

    # Final Tournament Setup
    tournament_device = "cuda" if gpu_available else "cpu"
    if args.workers > 0:
        num_workers = args.workers
    else:
        num_workers = calculate_optimal_workers(tournament_device)

    game_tasks = []
    task_metadata = []

    all_possible_pairs = []
    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            all_possible_pairs.append((agent_names[i], agent_names[j]))

    if args.total_games > 0:
        random.shuffle(all_possible_pairs)
        for i in range(args.total_games):
            name_a, name_b = all_possible_pairs[i % len(all_possible_pairs)]
            game_tasks.append((name_a, name_b, args.seed + i))
            task_metadata.append((name_a, name_b))
    else:
        for name_a, name_b in all_possible_pairs:
            for game_idx in range(args.games_per_pair):
                game_tasks.append((name_a, name_b, args.seed + len(game_tasks)))
                task_metadata.append((name_a, name_b))

    print(f"Starting Tournament: {len(game_tasks)} games using {num_workers} workers...")
    start_time = time.time()

    with Pool(processes=num_workers, initializer=init_worker, initargs=(m, l, tournament_device)) as pool:
        results = list(pool.imap(run_single_game, game_tasks, chunksize=1))

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
    print(f"\nTournament Complete in {elapsed:.2f}s")

    # 1. Print ELO Table
    print("\n" + "=" * 60)
    print(f"{'Agent':<15} | {'ELO':<6} | {'Wins':<6} | {'Draws':<6} | {'Win Rate'}")
    print("-" * 60)
    for name in sorted(agent_names, key=lambda x: elo.ratings[name], reverse=True):
        e_score = int(elo.ratings[name])
        w = elo.wins[name]
        d = elo.draws[name]
        m_count = elo.matches[name]
        wr = f"{(w / m_count * 100):.1f}%" if m_count > 0 else "N/A"
        print(f"{name:<15} | {e_score:<6} | {w:<6} | {d:<6} | {wr}")
    print("=" * 60)

    # 2. Matchup Matrix
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
