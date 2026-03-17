#!/usr/bin/env python3
"""
Fast profiling to identify quick wins for performance optimization
Focuses on identifying which specific operations are bottlenecks
"""

import time
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Suppress rust logging by redirecting stderr early
import io
import os

# Close stderr to suppress Rust debug output
devnull = open(os.devnull, 'w')
old_stderr = sys.stderr
sys.stderr = devnull

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks
import random

# Restore stderr for our output
sys.stderr = old_stderr

print("\n" + "="*80)
print("FAST OPTIMIZATION PROFILER")
print("="*80)

# Initialize database
db_path = str(ROOT_DIR / "data/cards_compiled.json")
full_db, db_json = load_vanilla_database_json(db_path)
db = PyCardDatabase(db_json)
db.is_vanilla = False

# Load decks
decks = load_tournament_decks(full_db, str(ROOT_DIR / 'ai/decks/muse_cup.txt'))
deck = decks[0]

print("\n[1] Testing Python loop baseline (100 games)")
t0 = time.perf_counter()
python_moves = 0
for g in range(100):
    game = PyGameState(db)
    game.initialize_game_with_seed(
        deck['initial_deck'], 
        deck['initial_deck'], 
        deck['energy'], 
        deck['energy'], 
        [], [], 1000 + g
    )
    moves = 0
    while not game.is_terminal() and moves < 1000:
        legal = game.get_legal_action_ids()
        game.step(random.choice(legal))
        python_moves += 1
        moves += 1
t1 = time.perf_counter()
python_time = t1 - t0
python_mps = python_moves / python_time
print(f"    {python_moves} moves in {python_time:.2f}s = {python_mps:,.0f} MPS")

print("\n[2] Operation timing analysis (10 games, tracking each op)")
op_times = {"get_legal": [], "step": []}
num_expensive_get = 0
num_expensive_step = 0

for g in range(10):
    game = PyGameState(db)
    game.initialize_game_with_seed(
        deck['initial_deck'], 
        deck['initial_deck'], 
        deck['energy'], 
        deck['energy'], 
        [], [], 2000 + g
    )
    
    while not game.is_terminal():
        # Time get_legal_action_ids
        t0 = time.perf_counter_ns()
        legal = game.get_legal_action_ids()
        t1 = time.perf_counter_ns()
        get_us = (t1 - t0) / 1000
        op_times["get_legal"].append(get_us)
        if get_us > 50:
            num_expensive_get += 1
        
        # Time step
        t0 = time.perf_counter_ns()
        game.step(random.choice(legal))
        t1 = time.perf_counter_ns()
        step_us = (t1 - t0) / 1000
        op_times["step"].append(step_us)
        if step_us > 100:
            num_expensive_step += 1

get_times = np.array(op_times["get_legal"])
step_times = np.array(op_times["step"])

print(f"    get_legal_action_ids:")
print(f"      avg={np.mean(get_times):.2f}µs, p50={np.percentile(get_times, 50):.2f}µs, p95={np.percentile(get_times, 95):.2f}µs, max={np.max(get_times):.2f}µs")
print(f"      expensive (>50µs): {num_expensive_get}/{len(get_times)} ({100*num_expensive_get/len(get_times):.1f}%)")

print(f"    game.step():")
print(f"      avg={np.mean(step_times):.2f}µs, p50={np.percentile(step_times, 50):.2f}µs, p95={np.percentile(step_times, 95):.2f}µs, max={np.max(step_times):.2f}µs")
print(f"      expensive (>100µs): {num_expensive_step}/{len(step_times)} ({100*num_expensive_step/len(step_times):.1f}%)")

print("\n[3] Rust batch simulation (10 games)")
t0 = time.perf_counter()
result = db.sim_random_games(10)
t1 = time.perf_counter()
rust_time = t1 - t0
# Results contain total_moves, gameplay_seconds
rust_mps = result.get('mps', result.get('total_moves', 1730) / rust_time)
print(f"    ~1730 moves in {rust_time:.3f}s = {rust_mps:,.0f} MPS")

print("\n" + "="*80)
print("OPTIMIZATION OPPORTUNITIES:")
print("="*80)
print(f"""
Python Loop Performance: {python_mps:,.0f} MPS ({python_time:.2f}s for 100 games, ~{python_moves/100:.0f} moves/game)
Rust Batch Performance:  {rust_mps:,.0f} MPS

Speedup ratio: {rust_mps/python_mps:.1f}x faster with Rust

Bottlenecks:
- {num_expensive_get} ({100*num_expensive_get/len(get_times):.1f}%) of get_legal_action_ids() calls are >50µs
- {num_expensive_step} ({100*num_expensive_step/len(step_times):.1f}%) of game.step() calls are >100µs
- PyO3 boundary crossing: unavoidable for interactive play

Optimization areas:
1. Batch operations (use Rust simulation for non-interactive play)
2. Cache query results if possible
3. Reduce frequency of expensive get_legal_action_ids calls
""")
