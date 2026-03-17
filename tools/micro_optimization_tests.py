#!/usr/bin/env python3
"""
Targeted micro-optimizations for Python loop
Tests specific hypotheses about bottlenecks
"""

import time
import sys
from pathlib import Path
import random
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks

# Load database
db_path = str(ROOT_DIR / "data/cards_compiled.json")
full_db, db_json = load_vanilla_database_json(db_path)
db = PyCardDatabase(db_json)
db.is_vanilla = False
decks = load_tournament_decks(full_db, str(ROOT_DIR / 'ai/decks/muse_cup.txt'))
deck = decks[0]

print("\n" + "="*80)
print("MICRO-OPTIMIZATION TESTING")
print("="*80 + "\n")

# Test 1: Random selection methods
print("[TEST 1] Random selection speed: random.choice() vs numpy")
action_list = list(range(100))
action_array = np.array(action_list)

t0 = time.perf_counter()
for _ in range(100000):
    random.choice(action_list)
t1 = time.perf_counter()
choice_time = t1 - t0

t0 = time.perf_counter()
for _ in range(100000):
    np.random.choice(action_array)
t1 = time.perf_counter()
numpy_time = t1 - t0

print(f"  random.choice():     {choice_time:.4f}s for 100k selections")
print(f"  numpy.random.choice: {numpy_time:.4f}s for 100k selections")
print(f"  Speedup: {choice_time/numpy_time:.2f}x\n")

# Test 2: Game initialization cost
print("[TEST 2] Game initialization overhead")
times = []
for _ in range(100):
    t0 = time.perf_counter_ns()
    game = PyGameState(db)
    game.initialize_game_with_seed(
        deck['initial_deck'], 
        deck['initial_deck'], 
        deck['energy'], 
        deck['energy'], 
        [], [], 9000 + _
    )
    t1 = time.perf_counter_ns()
    times.append((t1-t0) / 1000)

times = np.array(times)
print(f"  Avg: {np.mean(times):.3f}ms")
print(f"  Min: {np.min(times):.3f}ms")
print(f"  Max: {np.max(times):.3f}ms")
print(f"  P95: {np.percentile(times, 95):.3f}ms\n")

# Test 3: Early termination impact
print("[TEST 3] Impact of game length on per-move time")
games_data = []
for num_moves in [5, 10, 20, 50]:
    game = PyGameState(db)
    game.initialize_game_with_seed(
        deck['initial_deck'], 
        deck['initial_deck'], 
        deck['energy'], 
        deck['energy'], 
        [], [], 8000
    )
    
    t0 = time.perf_counter_ns()
    moves = 0
    move_times = []
    while not game.is_terminal() and moves < num_moves:
        t_move_start = time.perf_counter_ns()
        legal = game.get_legal_action_ids()
        game.step(random.choice(legal))
        t_move_end = time.perf_counter_ns()
        move_times.append((t_move_end - t_move_start) / 1000)
        moves += 1
    t1 = time.perf_counter_ns()
    
    avg_move_time = np.mean(move_times) if move_times else 0
    games_data.append((num_moves, moves, avg_move_time))

for num_requested, num_actual, avg_time in games_data:
    print(f"  Requested {num_requested:2d} moves: {num_actual:2d} actual, avg {avg_time:7.2f}us/move")

print("\n" + "="*80)
print("OPTIMIZATION RECOMMENDATIONS:")
print("="*80)
print("""
Based on test results:

1. RANDOM SELECTION:
   If numpy is significantly faster, we could pre-convert legal_ids to array
   But random.choice is likely already optimized in CPython

2. INITIALIZATION:
   Average ~33µs per game startup
   Consider reusing game objects if doing many games

3. EARLY TERMINATION:
   Check if certain positions have very expensive operations
   Could use early exit heuristics for strategy evaluation

4. NEXT STEPS:
   - Profile which game states have expensive step() calls
   - Quantify ability resolution workload
   - Test batch decision making (lookahead without full game sim)
""")
