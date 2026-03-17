"""
1-Minute Randomized Tournament
Runs as many games as possible in 60 seconds with random agent pairings and random decks.
Uses high-performance GameState optimizations (pooling, JIT).
"""

import argparse
import os
import random
import sys
import time
from multiprocessing import Pool, cpu_count

import numpy as np

# Add parent dir to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
    sys.path.append(os.path.join(ROOT_DIR, "engine"))
    sys.path.append(os.path.join(ROOT_DIR, "ai"))

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

# Global storage for worker processes
G_MEMBER_DB = {}
G_LIVE_DB = {}
G_AGENT_NAMES = ["TrueRandom", "Random", "Smart", "Ability", "Conservative", "Gamble"]


def init_worker(member_db, live_db):
    global G_MEMBER_DB, G_LIVE_DB
    G_MEMBER_DB = member_db
    G_LIVE_DB = live_db
    GameState.member_db = member_db
    GameState.live_db = live_db
    GameState._init_jit_arrays()


def get_agent(name):
    agent_map = {
        "TrueRandom": TrueRandomAgent(),
        "Random": RandomAgent(),
        "Smart": SmartHeuristicAgent(),
        "Ability": AbilityFocusAgent(),
        "Conservative": ConservativeAgent(),
        "Gamble": GambleAgent(),
    }
    return agent_map[name]


def run_single_game(seed):
    try:
        random.seed(seed)
        np.random.seed(seed)

        # Select random agents
        name_a = random.choice(G_AGENT_NAMES)
        name_b = random.choice(G_AGENT_NAMES)
        agent_a = get_agent(name_a)
        agent_b = get_agent(name_b)

        state = GameState()
        m_ids = list(G_MEMBER_DB.keys())
        l_ids = list(G_LIVE_DB.keys())

        # Setup random decks
        for p in state.players:
            p.main_deck = [random.choice(m_ids) for _ in range(40)] + [random.choice(l_ids) for _ in range(10)]
            random.shuffle(p.main_deck)
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

        for _ in range(1000):  # Safety turn limit
            if state.game_over:
                break
            mask = state.get_legal_actions()
            if not np.any(mask):
                break
            pid = state.current_player
            active = agent_a if (first_player == 0 and pid == 0) or (first_player == 1 and pid == 1) else agent_b
            action = active.choose_action(state, pid)
            state = state.step(action)

        return {"winner": state.winner, "agents": (name_a, name_b), "error": None}
    except Exception as e:
        import traceback

        return {
            "winner": -1,
            "agents": (None, None),
            "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=10, help="Tournament duration in seconds")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()

    num_workers = args.workers if args.workers > 0 else max(1, cpu_count() - 1)
    print(f"Starting {args.duration}s Randomized Tournament using {num_workers} workers...")

    start_time = time.time()
    total_games = 0
    results = []

    # Stats aggregation
    agent_stats = {name: {"matches": 0, "wins": 0, "draws": 0} for name in G_AGENT_NAMES}

    with Pool(processes=num_workers, initializer=init_worker, initargs=(m, l)) as pool:
        batch_size = num_workers * 2
        while time.time() - start_time < args.duration:
            # Submit a batch of games
            batch_seeds = [args.seed + total_games + i for i in range(batch_size)]
            batch_results = pool.map(run_single_game, batch_seeds)

            for res in batch_results:
                if res["error"]:
                    print(f"\nWorker Error: {res['error']}")
                    continue

                total_games += 1
                name_a, name_b = res["agents"]
                winner = res["winner"]

                agent_stats[name_a]["matches"] += 1
                agent_stats[name_b]["matches"] += 1

                if winner == 0:
                    agent_stats[name_a]["wins"] += 1
                elif winner == 1:
                    agent_stats[name_b]["wins"] += 1
                elif winner == 2:
                    agent_stats[name_a]["draws"] += 1
                    agent_stats[name_b]["draws"] += 1

            elapsed = time.time() - start_time
            print(
                f"\r  Elapsed: {elapsed:.1f}s | Games: {total_games} | Rate: {total_games / elapsed:.1f} g/s",
                end="",
                flush=True,
            )

    end_time = time.time()
    total_elapsed = end_time - start_time
    print("\n\nTournament Complete!")
    print(f"Total Games Played: {total_games}")
    print(f"Total Duration:     {total_elapsed:.2f}s")
    print(f"Overall Throughput: {total_games / total_elapsed:.1f} games/sec")

    print("\n" + "=" * 60)
    print(f"{'Agent':<15} | {'Matches':<8} | {'Wins':<6} | {'Draws':<6} | {'Win Rate'}")
    print("-" * 60)
    for name in sorted(
        G_AGENT_NAMES, key=lambda x: (agent_stats[x]["wins"] / (agent_stats[x]["matches"] or 1)), reverse=True
    ):
        stats = agent_stats[name]
        m_count = stats["matches"]
        w = stats["wins"]
        d = stats["draws"]
        wr = f"{(w / m_count * 100):.1f}%" if m_count > 0 else "N/A"
        print(f"{name:<15} | {m_count:<8} | {w:<6} | {d:<6} | {wr}")
    print("=" * 60)


if __name__ == "__main__":
    main()
