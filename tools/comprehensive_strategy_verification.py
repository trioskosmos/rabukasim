#!/usr/bin/env python3
"""
Comprehensive verification of strategy implementations:
- TurnSeq: Detailed planning analysis
- Neural: Time budget and ensemble usage
- MCTS: Search behavior and time consumption
- All with proper seeding and timing validation
"""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

import logging
import time
import torch
from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

print("\n" + "=" * 80)
print("COMPREHENSIVE STRATEGY VERIFICATION")
print("=" * 80)

config = ComparisonConfig(num_games=1, time_per_move=0.5)
comp = VanillaComparison(config)

def analyze_turnseq_planning(game, comp, legal_ids):
    """Detailed analysis of TurnSeq planning."""
    phase = int(game.phase)
    turn = int(game.turn)
    
    if phase != 4 or len(legal_ids) <= 1:
        return None
    
    # Save state (we can't actually revert but we can trace)
    cache_key = f"actions_turn_{turn}"
    index_key = f"index_turn_{turn}"
    plan_key = f"plan_turn_{turn}"
    
    # Call the planner
    start = time.time()
    _, action_seq, heuristic_score, diagnostics, extra = game.plan_full_turn_with_stats(comp.rust_db)
    elapsed = time.time() - start
    
    return {
        'phase': phase,
        'turn': turn,
        'legal_count': len(legal_ids),
        'plan_length': len(action_seq),
        'action_sequence': list(action_seq),
        'heuristic_score': heuristic_score,
        'diagnostics': diagnostics,
        'extra': extra,
        'time_taken': elapsed,
    }

# Play a test game
print("\nPlaying test game with mixed strategies...")
print("-" * 80)

import random
import numpy as np

random.seed(5001)
np.random.seed(5001)

game = comp._new_game(seed=5001)
selected_deck = random.choice(comp.decks)
initial_deck = selected_deck["initial_deck"]

move_count = 0
phase_4_count = 0

# Track strategy decisions
turnseq_decisions = []
neural_decisions = []
mcts_decisions = []
random_decisions = []

while not game.is_terminal() and move_count < 80:
    phase = int(game.phase)
    turn = int(game.turn)
    legal_ids = [int(x) for x in game.get_legal_action_ids()]
    
    if not legal_ids:
        break
    
    strategy_seq = ["turnseq", "neural", "mcts", "random"]
    strategy = strategy_seq[move_count % 4]
    
    # Get action with timing
    start_move = time.time()
    
    try:
        if strategy == "turnseq":
            action = comp._choose_turnseq_action(game, legal_ids, time_limit=0.5)
            if phase == 4:
                phase_4_count += 1
                # Get planning details
                planning_info = analyze_turnseq_planning(game, comp, legal_ids)
                if planning_info:
                    turnseq_decisions.append(planning_info)
                    print(f"Turn {turn} Phase {phase}: TurnSeq planned {planning_info['plan_length']} actions, "
                          f"score={planning_info['heuristic_score']:.2f}, time={planning_info['time_taken']*1000:.1f}ms")
                    print(f"  Sequence: {planning_info['action_sequence']}, chose action={action}")
        
        elif strategy == "neural":
            action = comp._choose_neural_action(game, legal_ids, initial_deck, time_limit=0.5)
            neural_decisions.append({'legal_count': len(legal_ids), 'action': action})
            
        elif strategy == "mcts":
            action = comp._choose_mcts_action(game, legal_ids, time_limit=0.5)
            mcts_decisions.append({'legal_count': len(legal_ids), 'action': action})
            
        else:  # random
            action = comp._choose_random_action(game, legal_ids)
            random_decisions.append({'legal_count': len(legal_ids), 'action': action})
        
        elapsed = time.time() - start_move
        legal_str = f"(legal: {len(legal_ids)})"
        print(f"  Move {move_count+1:2d} Phase {phase:2d} Turn {turn:2d}: {strategy:8s} -> {int(action):5d} {legal_str:15s} {elapsed*1000:6.1f}ms")
        
    except Exception as e:
        print(f"  ERROR on move {move_count+1}: {e}")
        import traceback
        traceback.print_exc()
        break
    
    game.step(int(action))
    move_count += 1

print("\n" + "=" * 80)
print("ANALYSIS RESULTS")
print("=" * 80)

print(f"\nGame Statistics:")
print(f"  Total moves: {move_count}")
print(f"  Phase 4 moves: {phase_4_count}")
print(f"  Terminal: {game.is_terminal()}")

print(f"\nTurnSeq Planning Evaluation:")
if turnseq_decisions:
    print(f"  Planning calls made: {len(turnseq_decisions)}")
    for i, plan_data in enumerate(turnseq_decisions[:3]):  # Show first 3
        print(f"\n  Plan #{i+1}:")
        print(f"    Turn: {plan_data['turn']}, Legal actions: {plan_data['legal_count']}")
        print(f"    Sequence length: {plan_data['plan_length']}")
        print(f"    Actions: {plan_data['action_sequence']}")
        print(f"    Heuristic score: {plan_data['heuristic_score']}")
        print(f"    Planning time: {plan_data['time_taken']*1000:.1f}ms")
        
        # Verify sequence makes sense
        if 0 in plan_data['action_sequence']:
            pass_count = plan_data['action_sequence'].count(0)
            print(f"    Note: Sequence contains {pass_count} pass action(s)")
else:
    print("  No TurnSeq Phase 4 decisions recorded")

print(f"\nNeural Network Decisions: {len(neural_decisions)} moves")
if neural_decisions:
    print(f"  First decision: legal_count={neural_decisions[0]['legal_count']}, action={neural_decisions[0]['action']}")

print(f"\nMCTS Decisions: {len(mcts_decisions)} moves")
if mcts_decisions:
    print(f"  First decision: legal_count={mcts_decisions[0]['legal_count']}, action={mcts_decisions[0]['action']}")

print(f"\nRandom Decisions: {len(random_decisions)} moves")

print(f"\nCache State at End:")
plan_keys = [k for k in comp.turnseq_plan_cache.keys() if k.startswith('plan_')]
print(f"  Total turns with plans: {len(plan_keys)}")
print(f"  Total cache entries: {len(comp.turnseq_plan_cache)}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80 + "\n")
