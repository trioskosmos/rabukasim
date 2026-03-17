#!/usr/bin/env python3
"""Diagnostic test to check strategy dispatch and move selection."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig
import random

config = ComparisonConfig(
    db_path='data/cards_vanilla.json',
    checkpoint_path='checkpoints/vanilla_overnight/best.pt',
    deck_source='ai/decks/muse_cup.txt',
    time_per_move=0.5,
    num_games=1,
    seed_base=9000,
    verbosity=True,
)

comp = VanillaComparison(config)

# Play a single game with verbose output
print("="*60)
print("Playing Neural (P0) vs Random (P1) with verbose output")
print("="*60)

result = comp.play_game(
    seed=9000,
    strategy_p0="neural",
    strategy_p1="random",
    time_limit=0.5,
    verbose=True,
)

print(f"\nGame Result:")
print(f"  Winner: {result['winner']} (-1=draw, 0=P0, 1=P1)")
print(f"  Turns: {result['turns']}")
print(f"  P0 (neural) total time: {result['p0_total_time']:.3f}s ({result['p0_moves']} moves)")
print(f"  P1 (random) total time: {result['p1_total_time']:.3f}s ({result['p1_moves']} moves)")
print(f"  Move time details: {result['move_time_details']}")
print(f"  Terminal: {result['terminal']}")
