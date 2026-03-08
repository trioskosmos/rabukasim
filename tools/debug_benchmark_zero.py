import sys, os, json
from pathlib import Path
import numpy as np
import torch

# Add project root to sys.path
root_dir = Path(os.getcwd())
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import engine_rust
print(f"Engine loaded from: {engine_rust.__file__}")

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    db_json = f.read()
db = engine_rust.PyCardDatabase(db_json)

state = engine_rust.PyGameState(db)
print(f"Initial state: Turn={state.turn}, Phase={state.phase}, Terminal={state.is_terminal()}")

# Use one of the problematic decks/seeds
m_ids = db.get_member_ids()
deck = (m_ids * 60)[:60]
energy = [38] * 12
seed = 101

print(f"\nInitializing game with seed {seed}...")
state.initialize_game_with_seed(deck, deck, energy, energy, [], [], seed)

print(f"After init: Turn={state.turn}, Phase={state.phase}, Terminal={state.is_terminal()}")
legal = state.get_legal_action_ids()
print(f"Legal actions count: {len(legal)}")
if legal:
    print(f"First 5 legal actions: {legal[:5]}")

p0 = state.get_player(0)
print(f"P0 Hand: {list(p0.hand)}")
print(f"P0 Deck len: {len(p0.deck)}")
print(f"P0 Initial Deck len: {len(p0.initial_deck)}")

if not state.is_terminal() and len(legal) > 0:
    print("\nStepping through first action...")
    action = legal[0]
    state.step(action)
    state.auto_step(db)
    print(f"After step(0): Turn={state.turn}, Phase={state.phase}, Terminal={state.is_terminal()}")
