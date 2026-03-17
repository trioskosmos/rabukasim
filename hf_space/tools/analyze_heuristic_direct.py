#!/usr/bin/env python3
"""
Heuristic diagnostic tool - manually evaluate all root-level moves.
"""

import sys
sys.path.insert(0, '.')

from engine_rust_src import game_engine as ge
import random

def analyze_single_turn(game_state, db, player_idx, turn_num):
    """Analyze all possible first moves for current player"""
    
    print(f"\n{'='*100}")
    print(f"TURN {turn_num} -PLAYER P{player_idx} DECISION ANALYSIS")
    print(f"{'='*100}")
    
    # Get board state
    p = game_state.players[player_idx]
    print(f"Board: {p.stage}")
    print(f"Hand: {p.hand} ({len(p.hand)} cards)")
    print(f"Energy: {len(p.energy_zone)-p.tapped_energy_count()}/{len(p.energy_zone)} untapped")
    print(f"Live Zone: {[cid for cid in p.live_zone if cid >= 0]}")
    
    # Get legal actions
    legal_actions = game_state.get_legal_action_ids(db)
    print(f"\nLegal actions: {len(legal_actions)} options")
    
    # Evaluate each action
    evaluations = []
    for i, action in enumerate(legal_actions[:10]):  # Limit to first 10 for readability
        test_state = game_state.copy()
        
        if not test_state.step(db, action).is_ok():
            continue
        
        # Get score of this state
        # For now, just show basic state info
        test_p = test_state.players[player_idx]
        board_filled = sum(1 for c in test_p.stage if c >= 0)
        
        # Get heuristic score using turn sequencer
        from engine_rust_src.core.logic import turn_sequencer as ts
        seq, val, (b, l), evals = ts.TurnSequencer.plan_full_turn(test_state, db)
        
        evaluations.append({
            'action': action,
            'move_num': i,
            'total_val': val,
            'board_score': b,
            'live_ev': l,
            'board_filled': board_filled,
            'next_sequence': seq[:2] if seq else []  # next 2 moves
        })
    
    # Sort by value
    evaluations.sort(key=lambda x: x['total_val'], reverse=True)
    
    print(f"\nTOP MOVES (sorted by total value):")
    print(f"{'Rank':<5} {'Action':<10} {'Total':<10} {'Board':<10} {'Live EV':<10} {'Board Slots':<12} {'Next Moves'}")
    print(f"{'-'*90}")
    
    for rank, ev in enumerate(evaluations[:5], 1):
        marker = "★" if rank == 1 else " "
        print(f"{marker} {rank:<3} {ev['action']:<10} {ev['total_val']:<10.2f} {ev['board_score']:<10.2f} {ev['live_ev']:<10.2f} {ev['board_filled']:<12} {ev['next_sequence']}")
    
    return evaluations[0] if evaluations else None

def main():
    print("Loading game engine...")
    
    db = ge.CardDatabase.load_vanilla()
    game = ge.GameState()
    
    # Load decks
    deck0 = ge.load_deck("ai/decks/liella_cup.txt", db)
    deck1 = ge.load_deck("ai/decks/liella_cup.txt", db)
    
    game.setup_players(deck0, deck1)
    
    # Run game, analyzing specific turns
    target_turns = [1, 2, 3, 4, 5]  # Analyze first 5 turns
    turn_count = 0
    
    while turn_count < 20 and not game.is_terminal():
        turn_count += 1
        
        if turn_count in target_turns:
            player = game.current_player
            analyze_single_turn(game, db, player, turn_count)
        
        # Execute best move
        from engine_rust_src.core.logic import turn_sequencer as ts
        seq, val, brk, evals = ts.TurnSequencer.plan_full_turn(game, db)
        
        # Execute the sequence
        for action in seq:
            if not game.step(db, action).is_ok():
                break
    
    print(f"\n\nGame finished after {turn_count} turns")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
