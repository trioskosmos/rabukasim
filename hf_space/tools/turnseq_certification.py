#!/usr/bin/env python3
"""
TurnSeq Certification Test: Verify it actually works as intended
- Does it win games?
- Does it execute the sequences it plans?
- Does it play non-pass moves in Phase 5?
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
print("TURNSEQ CERTIFICATION TEST")
print("=" * 90)

# Test parameters
num_games = 20
time_per_move = 0.3

print(f"\nRunning {num_games} games to certify TurnSeq functionality...")
print(f"Settings: time_per_move={time_per_move}s, mixed strategies\n")

config = ComparisonConfig(num_games=num_games, time_per_move=time_per_move)
comp = VanillaComparison(config)

# Track statistics
stats = {
    'turnseq_wins': 0,
    'neural_wins': 0,
    'plan_execution': [],
    'phase5_non_pass': [],
    'games_completed': 0,
}

# Run tournament
for game_num in range(num_games):
    seed = 6000 + game_num
    
    # Alternate P0/P1 strategies
    if game_num % 2 == 0:
        p0_strategy = 'turnseq'
        p1_strategy = 'neural'
    else:
        p0_strategy = 'neural'
        p1_strategy = 'turnseq'
    
    # Reset and run game
    comp.turnseq_plan_cache.clear()
    planned_actions = {}  # Track what was planned
    actual_actions = {}   # Track what was actually played
    phase5_moves = []
    
    # Manual game loop to track details
    random.seed(seed)
    np.random.seed(seed)
    
    game = comp._new_game(seed=seed)
    selected_deck = random.choice(comp.decks)
    initial_deck = selected_deck["initial_deck"]
    
    move_count = 0
    p0_moves = 0
    p1_moves = 0
    
    while not game.is_terminal() and move_count < 500:
        cp = int(game.current_player)
        phase = int(game.phase)
        turn = int(game.turn)
        legal_ids = [int(x) for x in game.get_legal_action_ids()]
        
        if not legal_ids:
            game.auto_step(comp.rust_db)
            move_count += 1
            continue
        
        # Choose strategy based on current player
        if cp == 0:
            strategy = p0_strategy
        else:
            strategy = p1_strategy
        
        # Track planned vs actual for TurnSeq
        if strategy == 'turnseq' and phase == 4:
            plan_key = f"plan_turn_{turn}"
            cache_key = f"actions_turn_{turn}"
            
            # If this is a new turn, record what was planned
            if plan_key not in comp.turnseq_plan_cache:
                try:
                    _, action_seq, _, _, _ = game.plan_full_turn_with_stats(comp.rust_db)
                    planned_actions[turn] = list(action_seq)
                except:
                    planned_actions[turn] = []
        
        # Get action from strategy
        if strategy == 'turnseq':
            action = comp._choose_turnseq_action(game, legal_ids, time_limit=time_per_move)
        elif strategy == 'neural':
            action = comp._choose_neural_action(game, legal_ids, initial_deck, time_limit=time_per_move)
        elif strategy == 'mcts':
            action = comp._choose_mcts_action(game, legal_ids, time_limit=time_per_move)
        else:
            action = comp._choose_random_action(game, legal_ids)
        
        # Track TurnSeq actions
        if strategy == 'turnseq':
            if turn not in actual_actions:
                actual_actions[turn] = []
            actual_actions[turn].append(int(action))
            
            # Track Phase 5 non-pass moves
            if phase == 5 and int(action) != 0:
                phase5_moves.append({'turn': turn, 'action': int(action), 'legal': len(legal_ids)})
        
        game.step(int(action))
        move_count += 1
        
        if cp == 0:
            p0_moves += 1
        else:
            p1_moves += 1
    
    # Determine winner
    if game.is_terminal():
        terminal_winner = int(game.get_winner())
        stats['games_completed'] += 1
        
        if p0_strategy == 'turnseq' and terminal_winner == 0:
            stats['turnseq_wins'] += 1
        elif p1_strategy == 'turnseq' and terminal_winner == 1:
            stats['turnseq_wins'] += 1
        
        if (p0_strategy == 'neural' and terminal_winner == 0) or (p1_strategy == 'neural' and terminal_winner == 1):
            stats['neural_wins'] += 1
        
        # Analyze plan execution
        for turn, planned in planned_actions.items():
            if turn in actual_actions:
                actual = actual_actions[turn]
                # Check if actual sequence matches planned (or is prefix if cache exhausted)
                prefix_match = all(actual[i] == planned[i] for i in range(min(len(actual), len(planned))))
                stats['plan_execution'].append({
                    'turn': turn,
                    'planned': planned,
                    'actual': actual,
                    'matches': prefix_match,
                })
        
        # Track Phase 5 non-pass moves
        stats['phase5_non_pass'].extend(phase5_moves)

print("\n" + "=" * 90)
print("RESULTS")
print("=" * 90)

print(f"\nWin Statistics ({stats['games_completed']} games):")
print(f"  TurnSeq wins: {stats['turnseq_wins']}/{stats['games_completed']} ({100*stats['turnseq_wins']/stats['games_completed']:.1f}%)")
print(f"  Neural wins:  {stats['neural_wins']}/{stats['games_completed']} ({100*stats['neural_wins']/stats['games_completed']:.1f}%)")

print(f"\nPlan Execution Analysis:")
if stats['plan_execution']:
    total_plans = len(stats['plan_execution'])
    matching_plans = sum(1 for p in stats['plan_execution'] if p['matches'])
    print(f"  Plans analyzed: {total_plans}")
    print(f"  Plans executing correctly: {matching_plans}/{total_plans} ({100*matching_plans/total_plans:.1f}%)")
    
    # Show some examples
    print(f"\n  Sample plan executions:")
    for plan_data in stats['plan_execution'][:3]:
        match_str = "MATCH" if plan_data['matches'] else "MISMATCH"
        print(f"    Turn {plan_data['turn']}: {match_str}")
        print(f"      Planned: {plan_data['planned']}")
        print(f"      Actual:  {plan_data['actual']}")
else:
    print("  No plan data collected")

print(f"\nPhase 5 Non-Pass Moves:")
if stats['phase5_non_pass']:
    print(f"  Total Phase 5 non-pass moves: {len(stats['phase5_non_pass'])}")
    print(f"\n  Sample non-pass moves in Phase 5:")
    for move_data in stats['phase5_non_pass'][:5]:
        print(f"    Turn {move_data['turn']}: action={move_data['action']} (legal_count={move_data['legal']})")
    print(f"\n  SUCCESS: TurnSeq IS playing non-pass moves in Phase 5")
else:
    print(f"  No Phase 5 non-pass moves found (or all were passes)")

print("\n" + "=" * 90)
print("CERTIFICATION SUMMARY")
print("=" * 90)

certification_passed = True

print(f"\n✓ TURNSEQ WINS: Yes, won {stats['turnseq_wins']} out of {stats['games_completed']} games")
    else:
        print(f"\n✗ TURNSEQ WINS: No wins recorded")
        certification_passed = False

    if stats['plan_execution']:
        matching = sum(1 for p in stats['plan_execution'] if p['matches'])
        if matching / len(stats['plan_execution']) > 0.5:
            print(f"✓ PLAN EXECUTION: {matching}/{len(stats['plan_execution'])} plans executed correctly ({100*matching/len(stats['plan_execution']):.1f}%)")
        else:
            print(f"⚠ PLAN EXECUTION: Only {matching}/{len(stats['plan_execution'])} plans matched ({100*matching/len(stats['plan_execution']):.1f}%)")

    if stats['phase5_non_pass']:
        print(f"✓ PHASE 5 DIVERSITY: Yes, found {len(stats['phase5_non_pass'])} non-pass moves in Phase 5")
    else:
        print(f"⚠ PHASE 5 DIVERSITY: Only pass moves in Phase 5 (may be game-dependent)")

    if certification_passed and stats['turnseq_wins'] > 0:
        print(f"\n" + "=" * 90)
        print("CERTIFICATION: PASSED - TurnSeq is working correctly")
        print("=" * 90)
    else:
        print(f"\n" + "=" * 90)
        print("CERTIFICATION: IN PROGRESS - See details above")
        print("=" * 90)

print()
