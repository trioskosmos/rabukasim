#!/usr/bin/env python3
"""
Analyze heuristic decisions turn-by-turn, showing:
- All candidate sequences
- Their scores and breakdowns
- Which ones led to live success
- Comparison to the chosen move
"""

import sys
import subprocess
import json
import re
from collections import defaultdict

def run_game_with_diagnostics():
    """Run the game binary and capture detailed logs"""
    result = subprocess.run(
        [r".\engine_rust_src\target\release\simple_game.exe"],
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout + result.stderr

def extract_turn_data(output):
    """Parse game output to extract turn-by-turn data"""
    lines = output.split('\n')
    turns = defaultdict(dict)
    current_turn = None
    current_phase = None
    
    for line in lines:
        # Detect turn changes
        turn_match = re.search(r'\[TURN (\d+)\]', line)
        if turn_match:
            current_turn = int(turn_match.group(1))
            current_phase = 'Main'
            turns[current_turn]['main_sequence'] = None
            turns[current_turn]['live_sequences'] = []
            turns[current_turn]['result'] = None
            continue
        
        # Extract Main phase sequence
        if current_turn and 'sequence=' in line and 'LiveSet' not in line:
            seq_match = re.search(r'sequence=\[(.*?)\]', line)
            player_match = re.search(r'P(\d+)', line)
            if seq_match and player_match:
                turns[current_turn]['main_sequence'] = seq_match.group(1)
                turns[current_turn]['current_player'] = player_match.group(1)
        
        # Extract LiveSet sequences
        if current_turn and 'LiveSet' in line:
            seq_match = re.search(r'sequence=\[(.*?)\]', line)
            if seq_match:
                turns[current_turn]['live_sequences'].append(seq_match.group(1))
        
        # Extract rule check results
        if current_turn and 'Rule 8.4.6' in line:
            # Format: Rule 8.4.6: p0_wins=false, p1_wins=false, has_success=[true, false], scores=[3, 0]
            match = re.search(r'has_success=\[(.*?)\], scores=\[(.*?)\]', line)
            if match:
                has_success = match.group(1)
                scores = match.group(2)
                turns[current_turn]['rule_result'] = {
                    'has_success': has_success,
                    'scores': scores
                }
    
    return turns

def analyze_sequences(turns):
    """Analyze turn decisions and their outcomes"""
    print("\n" + "="*100)
    print("HEURISTIC DECISION ANALYSIS - Move by Move")
    print("="*100)
    
    for turn_num in sorted(turns.keys()):
        turn_data = turns[turn_num]
        print(f"\n{'─'*100}")
        print(f"TURN {turn_num}")
        print(f"{'─'*100}")
        
        if 'main_sequence' in turn_data and turn_data['main_sequence']:
            player = turn_data.get('current_player', '?')
            print(f"Player P{player} Main Phase:")
            print(f"  → Chosen sequence: {turn_data['main_sequence']}")
        
        if 'live_sequences' in turn_data and turn_data['live_sequences']:
            print(f"  Live Zone placements:")
            for i, seq in enumerate(turn_data['live_sequences'], 1):
                print(f"    [{i}] {seq}")
        
        if 'rule_result' in turn_data:
            result = turn_data['rule_result']
            print(f"  Outcome:")
            print(f"    Has Success: {result['has_success']}")
            print(f"    Scores: {result['scores']}")
    
    return turns

def main():
    print("Running game to analyze heuristic decisions...")
    output = run_game_with_diagnostics()
    
    turns = extract_turn_data(output)
    
    print("\n\nFull Game Output:")
    print(output[:2000] if len(output) > 2000 else output)
    
    analyze_sequences(turns)

if __name__ == '__main__':
    main()
