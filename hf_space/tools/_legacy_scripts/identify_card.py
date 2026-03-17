import os
import sys

# Add parent dir to path
sys.path.append(os.getcwd())

from game.data_loader import CardDataLoader

loader = CardDataLoader("data/cards.json")
members, lives, energy = loader.load()

target_id = int(sys.argv[1]) if len(sys.argv) > 1 else 491
if target_id in members:
    m = members[target_id]
    print(f"ID {target_id}: {m.name}")
    print(f"Ability Text: {m.ability_text}")
    print(f"Abilities Count: {len(m.abilities)}")
    for i, ab in enumerate(m.abilities):
        print(f"  Ability {i}:")
        print(f"    Trigger: {ab.trigger}")
        print(f"    Costs: {ab.costs}")
        print(f"    Once per turn: {ab.is_once_per_turn}")
        print(f"    Effects: {ab.effects}")
else:
    print(f"ID {target_id} not found in members.")
