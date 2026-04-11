#!/usr/bin/env python3
"""Check what the SparseSourceManager is actually loading."""
import json
import sys
sys.path.insert(0, '/'.join(__file__.split('\\')[:-1]))  # Add data dir to path

from engine.compiler.sparse_source import SparseSourceManager

# Load the sparse manager
manager = SparseSourceManager('ability_frame_source.json')

print(f"Sparse manager loaded")
print(f"Mapping entries: {len(manager.mapping) if hasattr(manager, 'mapping') and manager.mapping else 'None/0'}")

# Try to get an ability
test_cards = ['PL!S-bp2-004-P', 'PL!S-bp1-001-P', 'PL!-sd1-010-SD']
for card_no in test_cards:
    entry = manager.get_ability(card_no, 0)
    print(f"  {card_no} ab#0: {'Found' if entry else 'NOT FOUND'}")
