#!/usr/bin/env python3
"""
Deep Analysis: What is the TurnSeq planner actually planning for Phase 5?
"""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import logging
import random
import numpy as np
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

logging.basicConfig(level=logging.WARNING)

print("\n" + "=" * 90)
print("DEEP ANALYSIS: TurnSeq Phase 5 Planning")
print("=" * 90)

config = ComparisonConfig(num_games=1, time_per_move=0.5)
comp = VanillaComparison(config)

seed = 7100
print(f"\nSingle game (seed={seed}) with detailed Phase 5 analysis\n")

random.seed(seed)
np.random.seed(seed)

game = comp._new_game(seed=seed)
selected_deck = random.choice(comp.decks)
initial_deck = selected_deck["initial_deck"]

comp.turnseq_plan_cache.clear()

move_count = 0
phase5_analyses = {}

while not game.is_terminal() and move_count < 100:
    cp = int(game.current_player)
    phase = int(game.phase)
    turn = int(game.turn)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        game.auto_step(comp.rust_db)
        move_count += 1
        continue
    
    # Analyze Phase 5 moves by TurnSeq
    if cp == 0 and phase == 5:  # TurnSeq in Phase 5
        turn_key = f"Turn {turn}"
        if turn_key not in phase5_analyses:
            phase5_analyses[turn_key] = {
                'legal_options': legal_ids[:],
                'moves_played': [],
                'cached_plan': comp.turnseq_plan_cache.get(f"actions_turn_{turn}", []),
                'cache_index': comp.turnseq_plan_cache.get(f"index_turn_{turn}", 0),
            }
        
        action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.5)
        phase5_analyses[turn_key]['moves_played'].append({
            'action': int(action),
            'legal': legal_ids[:],
        })
    else:
        if cp == 0:  # TurnSeq in Phase 4
            action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.5)
        else:  # Random
            action = comp._choose_random_action(game, legal_ids)
    
    game.step(int(action))
    move_count += 1

print("PHASE 5 ANALYSIS\n" + "-" * 90)

for turn_key in sorted(phase5_analyses.keys()):
    data = phase5_analyses[turn_key]
    
    print(f"\n{turn_key}:")
    print(f"  Legal Phase 5 options: {len(data['legal_options'])} choices")
    print(f"  Available IDs: {data['legal_options'][:5]}{'...' if len(data['legal_options']) > 5 else ''}")
    print(f"  Cached plan: {data['cached_plan']}")
    print(f"  Cache index at Phase 5: {data['cache_index']} (plan length: {len(data['cached_plan'])})")
    
    print(f"  Moves played in Phase 5:")
    for i, move in enumerate(data['moves_played']):
        is_legal = move['action'] in move['legal']
        legal_str = "LEGAL" if is_legal else "ILLEGAL"
        print(f"    Move {i+1}: action={move['action']} {legal_str}")
        if move['action'] == 0:
            print(f"             (PASS - action 0 is always available)")
        else:
            print(f"             (real action)")

print("\n" + "=" * 90)
print("CONCLUSION")
print("=" * 90)

non_pass_count = sum(len([m for m in data['moves_played'] if m['action'] != 0]) 
                     for data in phase5_analyses.values())

if non_pass_count > 0:
    print(f"\nSUCCESS: Found {non_pass_count} non-pass moves in Phase 5")
    print(f"  TurnSeq CAN and DOES play real moves when relevant")
else:
    print(f"\nINFO: Only pass moves in Phase 5")
    print(f"  This likely means in this game, Phase 5 pass was always optimal")
    print(f"  or cache was exhausted (all planned actions consumed in Phase 4)")

print("\n")
