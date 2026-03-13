#!/usr/bin/env python3
"""
Analyze heuristic decision logs to identify improvement opportunities.
Compares scores and identifies:
1. Moves that don't match the highest-scored option
2. Live EV variance across turns
3. Decision consistency issues
"""

import re
from collections import defaultdict

def parse_log_file(log_path):
    """Parse the heuristic_decisions.log file."""
    turns = []
    current_turn = None
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Split by turn headers
    turn_blocks = re.split(r'\[TURN \d+\]', content)
    
    for block in turn_blocks[1:]:  # Skip empty first element
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
            
        header = lines[0]
        match = re.match(r'(.+?) EVALUATION: (\d+) candidate moves', header)
        if not match:
            continue
            
        player_turn = match.group(1)  # e.g., "P0", "P1"
        num_candidates = int(match.group(2))
        
        # Extract scores from lines
        scores = []
        chosen = None
        
        for line in lines:
            # Match score lines: "   X 笏・       XXX.X 笏・ XX.X 笏・   XX.X"
            score_match = re.search(r'(\d+)\s+笏・\s+([\d\.-]+)\s+笏・\s+([\d\.-]+)\s+笏・\s+([\d\.-]+)', line)
            if score_match:
                rank = int(score_match.group(1))
                total = float(score_match.group(2))
                board = float(score_match.group(3))
                live_ev = float(score_match.group(4))
                scores.append({
                    'rank': rank,
                    'total': total,
                    'board': board,
                    'live_ev': live_ev
                })
            
            # Match CHOSEN line
            if 'CHOSEN:' in line:
                chosen_match = re.search(r'Total=([\d\.-]+)\s+Board=([\d\.-]+)\s+Live EV=([\d\.-]+)', line)
                if chosen_match:
                    chosen = {
                        'total': float(chosen_match.group(1)),
                        'board': float(chosen_match.group(2)),
                        'live_ev': float(chosen_match.group(3))
                    }
        
        if scores and chosen:
            turns.append({
                'player': player_turn,
                'num_candidates': num_candidates,
                'scores': scores,
                'chosen': chosen
            })
    
    return turns

def analyze_turns(turns):
    """Analyze turns for improvement opportunities."""
    print("=" * 80)
    print("HEURISTIC EVALUATION ANALYSIS")
    print("=" * 80)
    
    for i, turn in enumerate(turns):
        print(f"\nTurn {i+1}: {turn['player']} ({turn['num_candidates']} candidates)")
        print("-" * 80)
        
        if not turn['scores']:
            print("  No score data")
            continue
        
        # Get best score
        best_score = max(turn['scores'], key=lambda x: x['total'])
        
        # Check if chosen matches best
        is_chosen_best = abs(turn['chosen']['total'] - best_score['total']) < 0.01
        
        print(f"  Chosen: Total={turn['chosen']['total']:.1f} Board={turn['chosen']['board']:.1f} Live EV={turn['chosen']['live_ev']:.1f}")
        print(f"  Best:   Total={best_score['total']:.1f} Board={best_score['board']:.1f} Live EV={best_score['live_ev']:.1f}")
        
        if not is_chosen_best:
            print(f"  ⚠️  SUBOPTIMAL: Left {best_score['total'] - turn['chosen']['total']:.1f} points on table")
        else:
            print(f"  ✓ Chose best option")
        
        # Show top 5 scores
        print(f"\n  Top 5 scores:")
        for j, score in enumerate(turn['scores'][:5]):
            bar = "█" * int(score['total'] / 10) if score['total'] > 0 else ""
            marker = " ← CHOSEN" if abs(score['total'] - turn['chosen']['total']) < 0.01 else ""
            print(f"    {score['rank']}: {score['total']:7.1f} │ Board={score['board']:6.1f} Live={score['live_ev']:7.1f} {bar}{marker}")
        
        # Live EV analysis
        live_vals = [s['live_ev'] for s in turn['scores'][:5]]
        print(f"\n  Live EV analysis:")
        print(f"    Highest: {max(live_vals):.1f} | Lowest: {min(live_vals):.1f} | Avg: {sum(live_vals)/len(live_vals):.1f}")
        
        if max(live_vals) > 0 and min(live_vals) < max(live_vals) * 0.5:
            print(f"    ⚠️  HIGH VARIANCE: Some moves see {max(live_vals):.1f} win potential, others see {min(live_vals):.1f}")

def find_patterns(turns):
    """Find patterns in turn decisions."""
    print("\n" + "=" * 80)
    print("PATTERNS & INSIGHTS")
    print("=" * 80)
    
    # Group by player
    p0_turns = [t for t in turns if t['player'] == 'P0']
    p1_turns = [t for t in turns if t['player'] == 'P1']
    
    print(f"\nPlayer 0: {len(p0_turns)} turns")
    print(f"  Average Live EV (top choice): {sum(t['chosen']['live_ev'] for t in p0_turns) / len(p0_turns) if p0_turns else 0:.1f}")
    print(f"  Max Live EV seen: {max(max(s['live_ev'] for s in t['scores']) for t in p0_turns) if p0_turns else 0:.1f}")
    
    print(f"\nPlayer 1: {len(p1_turns)} turns")
    print(f"  Average Live EV (top choice): {sum(t['chosen']['live_ev'] for t in p1_turns) / len(p1_turns) if p1_turns else 0:.1f}")
    print(f"  Max Live EV seen: {max(max(s['live_ev'] for s in t['scores']) for t in p1_turns) if p1_turns else 0:.1f}")
    
    # Check for suboptimal choices
    suboptimal = [t for t in turns if not any(
        abs(t['chosen']['total'] - s['total']) < 0.01 
        for s in t['scores']
    )]
    
    if suboptimal:
        print(f"\n⚠️  SUBOPTIMAL CHOICES: {len(suboptimal)} instances")
        for t in suboptimal:
            best = max(t['scores'], key=lambda x: x['total'])
            print(f"  {t['player']}: Lost {best['total'] - t['chosen']['total']:.1f} points")
    else:
        print(f"\n✓ All chosen moves are among the highest-scoring options")

if __name__ == '__main__':
    log_file = 'heuristic_decisions.log'
    turns = parse_log_file(log_file)
    
    if turns:
        analyze_turns(turns)
        find_patterns(turns)
    else:
        print("No turn data found in log file")
    
    print("\n" + "=" * 80)
