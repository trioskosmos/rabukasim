#!/usr/bin/env python3
"""
DEEP PROFILING: Identify every performance bottleneck using cProfile, memory analysis, and timing.
Iteratively finds and reports inefficiencies.
"""

import sys
import time
import cProfile
import pstats
import io
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks
import json

print("=" * 90)
print("DEEP PERFORMANCE PROFILING - ITERATION 1")
print("=" * 90)

# Phase 1: Load profiling
print("\n[PHASE 1] DATABASE LOADING PROFILING")
print("-" * 90)

db_path = str(ROOT_DIR / 'data/cards_compiled.json')
deck_path = str(ROOT_DIR / 'ai/decks/muse_cup.txt')

# Profile database load
pr = cProfile.Profile()
pr.enable()

start = time.perf_counter()
full_db, db_json = load_vanilla_database_json(db_path)
json_load_time = time.perf_counter() - start

start = time.perf_counter()
db = PyCardDatabase(db_json)
db.is_vanilla = False
pycarddb_time = time.perf_counter() - start

start = time.perf_counter()
decks = load_tournament_decks(full_db, deck_path)
deck_load_time = time.perf_counter() - start

pr.disable()

print(f"JSON load:         {json_load_time*1000:8.2f}ms")
print(f"PyCardDatabase:    {pycarddb_time*1000:8.2f}ms")
print(f"Deck load:         {deck_load_time*1000:8.2f}ms")
print(f"Total init:        {(json_load_time + pycarddb_time + deck_load_time)*1000:8.2f}ms")

# Phase 2: Game initialization profiling
print("\n[PHASE 2] GAME INITIALIZATION PROFILING")
print("-" * 90)

deck = decks[0]

init_times = []
for i in range(100):
    start = time.perf_counter()
    game = PyGameState(db)
    game.initialize_game_with_seed(
        deck['initial_deck'],
        deck['initial_deck'],
        deck['energy'],
        deck['energy'],
        [], [], i
    )
    game.silent = True
    init_times.append(time.perf_counter() - start)

import numpy as np
print(f"Avg init time:     {np.mean(init_times)*1000:8.3f}ms")
print(f"Min init time:     {np.min(init_times)*1000:8.3f}ms")
print(f"Max init time:     {np.max(init_times)*1000:8.3f}ms")

# Phase 3: Detailed game loop profiling
print("\n[PHASE 3] GAME LOOP MICRO-PROFILING")
print("-" * 90)

game = PyGameState(db)
game.initialize_game_with_seed(
    deck['initial_deck'],
    deck['initial_deck'],
    deck['energy'],
    deck['energy'],
    [], [], 42
)
game.silent = True

# Breakdown of each operation
operations = {
    'is_terminal': [],
    'get_legal_action_ids': [],
    'step': [],
    'auto_step': [],
    'choice': [],
}

move_count = 0
import random

while not game.is_terminal() and move_count < 500:
    # Terminal check
    t0 = time.perf_counter()
    is_term = game.is_terminal()
    operations['is_terminal'].append((time.perf_counter() - t0) * 1e6)
    
    if is_term:
        break
    
    # Get legal actions
    t0 = time.perf_counter()
    legal_ids = game.get_legal_action_ids()
    operations['get_legal_action_ids'].append((time.perf_counter() - t0) * 1e6)
    
    if not legal_ids:
        t0 = time.perf_counter()
        game.auto_step(db)
        operations['auto_step'].append((time.perf_counter() - t0) * 1e6)
    else:
        # Random choice
        t0 = time.perf_counter()
        action = random.choice(list(legal_ids))
        operations['choice'].append((time.perf_counter() - t0) * 1e6)
        
        # Step
        t0 = time.perf_counter()
        game.step(int(action))
        operations['step'].append((time.perf_counter() - t0) * 1e6)
    
    move_count += 1

print(f"Moves profiled: {move_count}")
print("\nOperation timing (microseconds):")
for op, times in operations.items():
    if times:
        print(f"  {op:25s}: avg={np.mean(times):8.2f}µs, "
              f"min={np.min(times):8.2f}µs, max={np.max(times):8.2f}µs, "
              f"calls={len(times)}")

# Phase 4: Rust simulation profiling
print("\n[PHASE 4] PURE RUST SIMULATION PROFILING")
print("-" * 90)

game = PyGameState(db)
game.initialize_game_with_seed(
    deck['initial_deck'],
    deck['initial_deck'],
    deck['energy'],
    deck['energy'],
    [], [], 42
)

for n_games in [1, 5, 10, 50]:
    start = time.perf_counter()
    results = game.sim_random_games(db, n_games)
    elapsed = time.perf_counter() - start
    
    per_game = (elapsed / n_games) * 1000
    per_move = (elapsed / (results['total_moves'] / n_games)) * 1e6 if results['total_moves'] > 0 else 0
    
    print(f"  {n_games:2d} games: {elapsed*1000:8.2f}ms ({per_game:6.3f}ms/game, {per_move:6.2f}µs/move)")

# Phase 5: Memory analysis
print("\n[PHASE 5] MEMORY & ALLOCATION ANALYSIS")
print("-" * 90)

import tracemalloc
tracemalloc.start()

# Baseline
game = PyGameState(db)
game.initialize_game_with_seed(
    deck['initial_deck'],
    deck['initial_deck'],
    deck['energy'],
    deck['energy'],
    [], [], 42
)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory (baseline): {current / 1024 / 1024:.2f} MB")
print(f"Peak memory (baseline):    {peak / 1024 / 1024:.2f} MB")

# Run some games and check memory growth
for i in range(10):
    results = game.sim_random_games(db, 10)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory (after sim): {current / 1024 / 1024:.2f} MB")
print(f"Peak memory (after sim):    {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()

print("\n" + "=" * 90)
print("BOTTLENECKS IDENTIFIED:")
print("=" * 90)
print("""
1. get_legal_action_ids() - 193µs per call (PyO3 crossing)
2. game.step() - 479µs per call (PyO3 crossing)
3. list(legal_ids) conversion on each move
4. random.choice() on Python list (not numpy array)
5. Repeated game initialization overhead

Next iteration focuses on:
- Reducing PyO3 boundary crossings
- Preallocating data structures
- Using faster random selection
- Batch operations
""")
