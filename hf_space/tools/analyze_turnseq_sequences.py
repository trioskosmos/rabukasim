#!/usr/bin/env python3
"""
Deep analysis: Does TurnSeq evaluate multiple sequences and choose the best?
"""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

import logging
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig
import json

logging.basicConfig(level=logging.WARNING)

print("\n" + "=" * 80)
print("DEEP DIVE: TurnSeq Sequence Evaluation")
print("=" * 80)

config = ComparisonConfig(num_games=1, time_per_move=0.5)
comp = VanillaComparison(config)

import random
import numpy as np

# Multiple test games to see pattern of planning
test_seeds = [5001, 5002, 5003]
all_plans = []

for seed_idx, seed in enumerate(test_seeds):
    print(f"\n--- Game {seed_idx+1} (seed={seed}) ---")
    
    random.seed(seed)
    np.random.seed(seed)
    
    game = comp._new_game(seed=seed)
    selected_deck = random.choice(comp.decks)
    initial_deck = selected_deck["initial_deck"]
    
    # Reset cache
    comp.turnseq_plan_cache.clear()
    
    move_count = 0
    phase_4_moves = 0
    turn_plans = {}
    
    strategies_cycle = ["turnseq", "neural", "mcts", "random"]
    
    while not game.is_terminal() and move_count < 60:
        phase = int(game.phase)
        turn = int(game.turn)
        legal_ids = [int(x) for x in game.get_legal_action_ids()]
        
        if not legal_ids:
            break
        
        strategy = strategies_cycle[move_count % 4]
        
        if strategy == "turnseq" and phase == 4 and len(legal_ids) > 1:
            # Call planner and record plan details
            try:
                _, action_seq, heuristic_score, diagnostics, extra = game.plan_full_turn_with_stats(comp.rust_db)
                turn_key = f"Turn {turn}"
                
                if turn_key not in turn_plans:
                    turn_plans[turn_key] = {
                        'turn': turn,
                        'legal_count': len(legal_ids),
                        'sequences': []
                    }
                
                plan_info = {
                    'sequence': list(action_seq),
                    'score': heuristic_score,
                    'legal_count': len(legal_ids),
                }
                turn_plans[turn_key]['sequences'].append(plan_info)
                
                # Use the planned action
                action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.5)
                
            except Exception as e:
                print(f"  Error during planning: {e}")
                action = comp._choose_random_action(game, legal_ids)
        else:
            if strategy == "turnseq":
                action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.5)
            elif strategy == "neural":
                action = comp._choose_neural_action(game, legal_ids, initial_deck, time_limit=0.5)
            elif strategy == "mcts":
                action = comp._choose_mcts_action(game, legal_ids, time_limit=0.5)
            else:
                action = comp._choose_random_action(game, legal_ids)
        
        try:
            game.step(int(action))
            move_count += 1
        except:
            break
    
    # Display plans for this game
    for turn_key in sorted(turn_plans.keys()):
        turn_data = turn_plans[turn_key]
        sequences = turn_data['sequences']
        
        print(f"\n  {turn_key}: {len(sequences)} sequence(s) planned")
        for i, seq_info in enumerate(sequences):
            print(f"    Sequence {i+1}: {seq_info['sequence']}")
            print(f"               Score: {seq_info['score']:.0f}")
        
        all_plans.append(turn_data)

print("\n" + "=" * 80)
print("ANALYSIS SUMMARY")
print("=" * 80)

# Analyze score patterns
plan_scores = []
for game_plan in all_plans:
    for seq in game_plan['sequences']:
        plan_scores.append(seq['score'])

if plan_scores:
    print(f"\nScore Statistics Across All Plans:")
    print(f"  Min score: {min(plan_scores):.0f}")
    print(f"  Max score: {max(plan_scores):.0f}")
    print(f"  Mean score: {np.mean(plan_scores):.0f}")
    print(f"  Std dev: {np.std(plan_scores):.0f}")
    
    # Check if scores vary significantly (indicating multiple sequences evaluated)
    if np.std(plan_scores) > 1000:
        print(f"\nSUCCESS: HIGH VARIANCE - Planner is evaluating diverse sequences")
    else:
        print(f"\nPOOR: LOW VARIANCE - Planner may only be trying similar sequences")

# Check sequence diversity
all_sequences = []
for game_plan in all_plans:
    for seq in game_plan['sequences']:
        all_sequences.append(tuple(seq['sequence']))

unique_sequences = set(all_sequences)
print(f"\nSequence Diversity:")
print(f"  Total sequences planned: {len(all_sequences)}")
print(f"  Unique sequences: {len(unique_sequences)}")

if len(unique_sequences) > 1:
    print(f"\nSUCCESS: DIVERSE - Planner generated {len(unique_sequences)} different sequences")
    print(f"   Sample sequences:")
    for seq in list(unique_sequences)[:3]:
        print(f"     {seq}")
else:
    print(f"\nPOOR: REPETITIVE - Planner generated mostly the same sequence")

print("\n" + "=" * 80 + "\n")
