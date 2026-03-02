import os
import sys
import json
import torch
import numpy as np

# Path hacks
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

search_paths = [
    root_dir / "engine_rust_src" / "target" / "dev-release",
    root_dir / "engine_rust_src" / "target" / "debug",
    root_dir / "engine_rust_src" / "target" / "release",
]
for p in search_paths:
    if (p / "engine_rust.pyd").exists() or (p / "engine_rust.dll").exists():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
            break

import engine_rust

def verify():
    # Load compiler db
    db_path = root_dir / "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))

    state = engine_rust.PyGameState(db_engine)
    # Minimal initial deck
    # 20 Honoka members, 12 Lives, 4 Energy
    members = [1000] * 48
    lives = [10] * 12
    energy = [1] * 12
    state.initialize_game(members + lives, members + lives, energy, energy, [], [])

    # Get tensor before moving anything
    tensor_before = np.array(state.to_alphazero_tensor())
    
    # Let's say we play the first card in hand
    # Hand is initially 4 cards. We know UIDs for hand cards are some specific index.
    legal_actions = state.get_legal_action_ids()
    print("Legal actions:", legal_actions)
    
    # Just draw 1 card to be sure, or do some action
    # Let's step until a card moves
    
    # We can just check the encoding directly by finding where Zone ID is Hand (1)
    # the 170 slice format:
    # 0..15: One-hot Zone
    
    # Find a card in hand in the tensor
    # There are 120 entities. Entity 0-59 are player 0.
    def get_entity_zones(tensor):
        zones = []
        for i in range(120):
            start = 25 + i * 170
            zone_slice = tensor[start:start+16]
            zone_idx = np.argmax(zone_slice) if np.sum(zone_slice) > 0 else -1
            zones.append(zone_idx)
        return zones

    zones_before = get_entity_zones(tensor_before)
    print("Zones before:", collections.Counter(zones_before) if 'collections' in globals() else "")
    for i, z in enumerate(zones_before):
        if z == 1: # HAND
            print(f"Entity {i} is in HAND")
            break

    # Make a random legal move
    if legal_actions:
        state.step(legal_actions[-1])
        state.auto_step(db_engine)
        
    tensor_after = np.array(state.to_alphazero_tensor())
    zones_after = get_entity_zones(tensor_after)
    
    diffs = []
    for i in range(120):
        if zones_before[i] != zones_after[i]:
            diffs.append((i, zones_before[i], zones_after[i]))
            
    print("Entity Zone Changes:", diffs)
    
    # Check if action mask still aligns properly
    
if __name__ == "__main__":
    import collections
    verify()
