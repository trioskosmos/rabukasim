#!/usr/bin/env python3
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks

print("VERIFYING sim_random_games RESULTS\n")

db_path = str(ROOT_DIR / 'data/cards_compiled.json')
full_db, db_json = load_vanilla_database_json(db_path)
db = PyCardDatabase(db_json)
db.is_vanilla = False

decks = load_tournament_decks(full_db, str(ROOT_DIR / 'ai/decks/muse_cup.txt'))
deck = decks[0]

game = PyGameState(db)
game.initialize_game_with_seed(
    deck['initial_deck'], 
    deck['initial_deck'], 
    deck['energy'], 
    deck['energy'], 
    [], [], 42
)

# Test different game counts
for n_games in [1, 10, 50, 100]:
    start = time.perf_counter()
    results = game.sim_random_games(db, n_games)
    elapsed = time.perf_counter() - start
    
    total_moves = results['total_moves']
    gameplay_secs = results['gameplay_seconds']
    mps = results['mps']
    
    avg_per_game = total_moves / n_games
    
    print(f"{n_games:3d} games: {total_moves:7d} moves | "
          f"{avg_per_game:6.1f} avg/game | "
          f"{mps:10,.0f} MPS | "
          f"{elapsed:.3f}s wall")
