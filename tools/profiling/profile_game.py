"""
Single-process profiling script for game loop.
"""

import cProfile
import os
import pstats
import random
import sys
from io import StringIO

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data_loader import CardDataLoader
from game.game_state import GameState, Phase
from headless_runner import RandomAgent, SmartHeuristicAgent


def run_game_optimized(member_db, live_db, seed):
    """Run one game with optimized copy"""
    random.seed(seed)
    np.random.seed(seed)

    state = GameState()
    agents = [SmartHeuristicAgent(), RandomAgent()]

    # Setup decks
    m_ids = list(member_db.keys())
    l_ids = list(live_db.keys())

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

    state.first_player = 0
    state.current_player = 0
    state.phase = Phase.MULLIGAN_P1

    for _ in range(2000):
        if state.game_over:
            break
        mask = state.get_legal_actions()
        if not np.any(mask):
            break
        pid = state.current_player
        action = agents[pid].choose_action(state, pid)
        state = state.step(action)

    return state.winner


if __name__ == "__main__":
    # Load cards
    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()

    # Initialize GameState DBs
    GameState.member_db = m
    GameState.live_db = l
    GameState._init_jit_arrays()

    # Warmup (JIT compilation)
    print("Warming up JIT...")
    run_game_optimized(m, l, 0)

    # Profile 10 games
    print("Profiling 10 games...")
    profiler = cProfile.Profile()
    profiler.enable()

    for i in range(10):
        run_game_optimized(m, l, 42 + i)

    profiler.disable()

    # Print stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats("cumulative")
    stats.print_stats(40)
    print(s.getvalue())
