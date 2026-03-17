#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_vanilla_database_json, load_tournament_decks
import json

db_path = str(ROOT_DIR / 'data/cards_compiled.json')
full_db, db_json = load_vanilla_database_json(db_path)
db = PyCardDatabase(db_json)
db.is_vanilla = False

decks = load_tournament_decks(full_db, str(ROOT_DIR / 'ai/decks/muse_cup.txt'))
print(f'Decks: {len(decks)}')

if decks:
    deck = decks[0]
    print(f'Deck size: {len(deck["initial_deck"])} cards')
    print(f'Deck energy length: {len(deck["energy"])} items')
    
    game = PyGameState(db)
    game.initialize_game_with_seed(
        deck['initial_deck'], 
        deck['initial_deck'], 
        deck['energy'], 
        deck['energy'], 
        [], [], 42
    )
    
    print('\nSim 10 games:')
    results = game.sim_random_games(db, 10)
    print(json.dumps(results, indent=2))
