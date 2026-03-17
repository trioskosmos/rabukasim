#!/usr/bin/env python3
"""
Investigate game initialization outliers
Which decks/seeds cause 2+ second init times?
"""

import time
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks

db_path = str(ROOT_DIR / "data/cards_compiled.json")
full_db, db_json = load_vanilla_database_json(db_path)
db = PyCardDatabase(db_json)
db.is_vanilla = False
decks = load_tournament_decks(full_db, str(ROOT_DIR / 'ai/decks/muse_cup.txt'))

print("\nTesting initialization time across different decks...")
print("(Analyzing first 15 decks with 3 seeds each)\n")

slow_cases = []

for deck_idx, deck in enumerate(decks[:15]):
    print(f"Deck {deck_idx}: {deck.get('name', 'Unknown')}")
    for seed_offset in range(3):
        seed = 10000 + deck_idx * 100 + seed_offset
        
        t0 = time.perf_counter()
        game = PyGameState(db)
        game.initialize_game_with_seed(
            deck['initial_deck'], 
            deck['initial_deck'], 
            deck['energy'], 
            deck['energy'], 
            [], [], seed
        )
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000
        
        marker = " ⚠️  SLOW" if elapsed_ms > 100 else ""
        print(f"  Seed {seed}: {elapsed_ms:7.1f}ms{marker}")
        
        if elapsed_ms > 100:
            slow_cases.append({
                'deck_idx': deck_idx,
                'deck_name': deck.get('name', 'Unknown'),
                'seed': seed,
                'time_ms': elapsed_ms
            })

if slow_cases:
    print(f"\nFound {len(slow_cases)} SLOW cases (>100ms):")
    for case in sorted(slow_cases, key=lambda x: x['time_ms'], reverse=True)[:5]:
        print(f"  {case['deck_name']} (deck {case['deck_idx']}, seed {case['seed']}): {case['time_ms']:.1f}ms")
else:
    print("\nNo initialization times > 100ms found in first 15 decks")

print("\n" + "="*60)
print("NOTE: Initialization happens only once per game")
print("This is NOT part of per-move overhead")
print("Focus optimization on per-move speed, not initialization")
