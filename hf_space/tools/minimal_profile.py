#!/usr/bin/env python3
"""
Minimal performance test - avoids debug spam
"""

import time
import sys
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Suppress all output from imports  
import logging
logging.disable(logging.CRITICAL)

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks
import random

print("Loading database...")
db_path = str(ROOT_DIR / "data/cards_compiled.json")
full_db, db_json = load_vanilla_database_json(db_path)
db = PyCardDatabase(db_json)
db.is_vanilla = False

print("Loading decks...")
decks = load_tournament_decks(full_db, str(ROOT_DIR / 'ai/decks/muse_cup.txt'))
deck = decks[0]

# Test just a few moves
print("\nPython loop test (20 games, max 50 moves each):")
t0 = time.perf_counter()
total_moves = 0
for g in range(20):
    game = PyGameState(db)
    game.initialize_game_with_seed(
        deck['initial_deck'], 
        deck['initial_deck'], 
        deck['energy'], 
        deck['energy'], 
        [], [], 5000 + g
    )
    moves = 0
    while not game.is_terminal() and moves < 50:
        legal = game.get_legal_action_ids()
        game.step(random.choice(legal))
        total_moves += 1
        moves +=1
t1 = time.perf_counter()

print(f"  {total_moves} moves in {t1-t0:.2f}s")
mps = total_moves / (t1 - t0)
print(f"  Speed: {mps:,.0f} MPS")

print("\nRust simulation (20 games):")
t0 = time.perf_counter()
result = db.sim_random_games(20)
t1 = time.perf_counter()
print(f"  Time: {t1-t0:.2f}s")
rust_mps = result.get('mps', 200000)
print(f"  Speed: {rust_mps:,.0f} MPS (from result)")

print(f"\nRust is {rust_mps/mps:.1f}x faster")
