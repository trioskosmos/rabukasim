#!/usr/bin/env python3
"""
Manually parse the visible output from heuristic decisions.
"""

data = """
[TURN 1] P1 EVALUATION: 4 candidate moves
   1 - Total:    97.2 Board:  23.4 Live:  73.8
   2 - Total:    97.2 Board:  23.4 Live:  73.8
   3 - Total:    97.2 Board:  23.4 Live:  73.8
   4 - Total:    56.3 Board:  10.7 Live:  45.6
CHOSEN: Total=97.2 Board=23.4 Live EV=73.8

[TURN 1] P0 EVALUATION: 13 candidate moves
   1 - Total:   113.1 Board:  32.2 Live:  80.8
   2 - Total:   113.1 Board:  32.2 Live:  80.8
   3 - Total:   113.1 Board:  32.2 Live:  80.8
   4 - Total:   113.1 Board:  32.2 Live:  80.8
   5 - Total:   113.1 Board:  32.2 Live:  80.8
CHOSEN: Total=113.1 Board=32.2 Live EV=80.8

[TURN 2] P1 EVALUATION: 10 candidate moves
   1 - Total:    31.8 Board:  31.8 Live:   -0.0
   2 - Total:    31.8 Board:  31.8 Live:   -0.0
   3 - Total:    28.9 Board:  28.9 Live:   -0.0
   4 - Total:    28.9 Board:  28.9 Live:   -0.0
   5 - Total:    28.9 Board:  28.9 Live:   -0.0
CHOSEN: Total=31.8 Board=31.8 Live EV=-0.0

[TURN 2] P0 EVALUATION: 13 candidate moves
   1 - Total:   133.6 Board:  52.8 Live:  80.8
   2 - Total:   133.6 Board:  52.8 Live:  80.8
   3 - Total:   131.2 Board:  50.4 Live:  80.8
   4 - Total:   131.2 Board:  50.4 Live:  80.8
   5 - Total:   131.2 Board:  50.4 Live:  80.8
CHOSEN: Total=133.6 Board=52.8 Live EV=80.8

[TURN 3] P1 EVALUATION: 12 candidate moves
   1 - Total:    44.8 Board:  44.8 Live:   -0.0
   2 - Total:    44.8 Board:  44.8 Live:   -0.0
   3 - Total:    41.9 Board:  41.9 Live:   -0.0
   4 - Total:    41.9 Board:  41.9 Live:   -0.0
   5 - Total:    36.8 Board:  36.8 Live:   -0.0
CHOSEN: Total=44.8 Board=44.8 Live EV=-0.0

[TURN 3] P0 EVALUATION: 13 candidate moves
   1 - Total:   251.1 Board:  62.5 Live: 188.7
   2 - Total:   251.1 Board:  62.5 Live: 188.7
   3 - Total:   248.7 Board:  60.0 Live: 188.7
   4 - Total:   248.7 Board:  60.0 Live: 188.7
   5 - Total:   248.7 Board:  60.0 Live: 188.7
CHOSEN: Total=251.1 Board=62.5 Live EV=188.7

[TURN 4] P1 EVALUATION: 18 candidate moves
   1 - Total:    52.4 Board:  52.4 Live:   -0.0
   2 - Total:    52.4 Board:  52.4 Live:   -0.0
   3 - Total:    51.4 Board:  51.4 Live:   -0.0
   4 - Total:    49.8 Board:  49.8 Live:   -0.0
   5 - Total:    49.5 Board:  49.5 Live:   -0.0
CHOSEN: Total=52.4 Board=52.4 Live EV=-0.0

[TURN 4] P0 EVALUATION: 16 candidate moves
   1 - Total:    52.7 Board:  52.7 Live:   -0.0
   2 - Total:    52.2 Board:  52.2 Live:   -0.0
   3 - Total:    49.8 Board:  49.8 Live:   -0.0
   4 - Total:    49.8 Board:  49.8 Live:   -0.0
   5 - Total:    49.8 Board:  49.8 Live:   -0.0
CHOSEN: Total=52.7 Board=52.7 Live EV=-0.0

[TURN 5] P1 EVALUATION: 19 candidate moves
   1 - Total:    61.8 Board:  61.8 Live:   -0.0
   2 - Total:    59.8 Board:  59.8 Live:   -0.0
   3 - Total:    59.0 Board:  59.0 Live:   -0.0
   4 - Total:    58.9 Board:  58.9 Live:   -0.0
   5 - Total:    58.9 Board:  58.9 Live:   -0.0
CHOSEN: Total=61.8 Board=61.8 Live EV=-0.0

[TURN 5] P0 EVALUATION: 15 candidate moves
   1 - Total:    53.4 Board:  53.4 Live:   -0.0
   2 - Total:    47.5 Board:  47.5 Live:   -0.0
   3 - Total:    47.5 Board:  47.5 Live:   -0.0
   4 - Total:    47.5 Board:  47.5 Live:   -0.0
   5 - Total:    47.5 Board:  47.5 Live:   -0.0
CHOSEN: Total=53.4 Board=53.4 Live EV=-0.0

[TURN 6] P1 EVALUATION: 22 candidate moves
   1 - Total:    68.6 Board:  68.6 Live:   -0.0
   2 - Total:    64.7 Board:  64.7 Live:   -0.0
   3 - Total:    64.7 Board:  64.7 Live:   -0.0
   4 - Total:    64.7 Board:  64.7 Live:   -0.0
   5 - Total:    64.7 Board:  64.7 Live:   -0.0
CHOSEN: Total=68.6 Board=68.6 Live EV=-0.0
""".strip()

def analyze_data():
    """Analyze the turn data."""
    print("=" * 90)
    print("HEURISTIC EVALUATION ANALYSIS - Game Results")
    print("=" * 90)
    
    turns = []
    current_section = None
    
    for line in data.split('\n'):
        if '[TURN' in line and ']' in line:
            # Parse turn header
            import re
            m = re.search(r'P(\d) EVALUATION: (\d+) candidate', line)
            if m:
                player = int(m.group(1))
                num_candidates = int(m.group(2))
                current_section = {
                    'player': player,
                    'num_candidates': num_candidates,
                    'scores': [],
                    'chosen': None,
                    'turn_num': len([t for t in turns if t['player'] == player]) + 1
                }
                turns.append(current_section)
        elif current_section and ' - Total:' in line:
            # Parse score line
            import re
            m = re.search(r'Total:\s+([\d.-]+)\s+Board:\s+([\d.-]+)\s+Live:\s+([\d.-]+)', line)
            if m:
                current_section['scores'].append({
                    'total': float(m.group(1)),
                    'board': float(m.group(2)),
                    'live': float(m.group(3))
                })
        elif current_section and 'CHOSEN:' in line:
            # Parse chosen line
            import re
            m = re.search(r'Total=([\d.-]+)\s+Board=([\d.-]+)\s+Live EV=([\d.-]+)', line)
            if m:
                current_section['chosen'] = {
                    'total': float(m.group(1)),
                    'board': float(m.group(2)),
                    'live': float(m.group(3))
                }
    
    # Analyze each turn
    for turn in turns:
        print(f"\nTurn {turn['turn_num']}: Player {turn['player']} ({turn['num_candidates']} candidates)")
        print("-" * 90)
        
        if not turn['scores']:
            print("  ⚠️  No score data")
            continue
        
        best = max(turn['scores'], key=lambda x: x['total'])
        chosen = turn['chosen']
        
        is_optimal = abs(chosen['total'] - best['total']) < 0.01
        
        print(f"  Chosen:   Total={chosen['total']:7.1f}  Board={chosen['board']:7.1f}  Live={chosen['live']:7.1f}")
        print(f"  Best:     Total={best['total']:7.1f}  Board={best['board']:7.1f}  Live={best['live']:7.1f}")
        
        if is_optimal:
            print(f"  ✓ Optimal choice")
        else:
            gap = best['total'] - chosen['total']
            print(f"  ⚠️  SUBOPTIMAL: Left {gap:.1f} points on table ({100*gap/best['total']:.1f}% difference)")
        
        # Show top 3
        print(f"\n  Top 3 moves:")
        for i, score in enumerate(turn['scores'][:3]):
            marker = " ← CHOSEN" if abs(score['total'] - chosen['total']) < 0.01 else ""
            print(f"    #{i+1}: Total={score['total']:7.1f}  Board={score['board']:7.1f}  Live={score['live']:7.1f}{marker}")
        
        # Live EV analysis
        live_vals = [s['live'] for s in turn['scores'][:5]]
        max_live = max(live_vals)
        min_live = min(live_vals)
        avg_live = sum(live_vals) / len(live_vals)
        
        print(f"\n  Live EV spread (top 5):")
        print(f"    Max: {max_live:7.1f}  Min: {min_live:7.1f}  Avg: {avg_live:7.1f}")
        
        if max_live > 10 and min_live < max_live * 0.3:
            print(f"    ⚠️  HIGH VARIANCE: Some paths see {max_live:.1f} win potential")
    
    # Summary analysis
    print("\n" + "=" * 90)
    print("SUMMARY FINDINGS")
    print("=" * 90)
    
    p0_turns = [t for t in turns if t['player'] == 0]
    p1_turns = [t for t in turns if t['player'] == 1]
    
    if p0_turns:
        p0_avg_live = sum(t['chosen']['live'] for t in p0_turns) / len(p0_turns)
        p0_max_live = max(max(s['live'] for s in t['scores']) for t in p0_turns)
        print(f"\nPlayer 0: {len(p0_turns)} turns evaluated")
        print(f"  Chosen avg Live EV: {p0_avg_live:7.1f}")
        print(f"  Max Live EV seen:   {p0_max_live:7.1f}")
    
    if p1_turns:
        p1_avg_live = sum(t['chosen']['live'] for t in p1_turns) / len(p1_turns)
        p1_max_live = max(max(s['live'] for s in t['scores']) for t in p1_turns)
        print(f"\nPlayer 1: {len(p1_turns)} turns evaluated")
        print(f"  Chosen avg Live EV: {p1_avg_live:7.1f}")
        print(f"  Max Live EV seen:   {p1_max_live:7.1f}")
    
    # Check optimality
    suboptimal = [t for t in turns if not any(abs(t['chosen']['total'] - s['total']) < 0.01 for s in t['scores'])]
    if suboptimal:
        print(f"\n⚠️  SUBOPTIMAL CHOICES: {len(suboptimal)} out of {len(turns)} turns")
        for t in suboptimal:
            best = max(t['scores'], key=lambda x: x['total'])
            gap = best['total'] - t['chosen']['total']
            print(f"    Turn {t['turn_num']} P{t['player']}: Lost {gap:.1f} points")
    else:
        print(f"\n✓ All chosen moves are optimal")
    
    print("\n" + "=" * 90)
    print("KEY OBSERVATIONS")
    print("=" * 90)
    
    print("""
1. Turn 3 P0: HUGE Live EV spike (188.7)
   - This suggests P0 sees a winning path
   - BUT it doesn't materialize - game ends in draw
   - Possible causes:
     a) Evaluation overestimated win probability
     b) P1's defense was underestimated
     c) Winning path requires perfect sequences (unlikely)

2. Turn 4+ Live EV drops to -0.0 across all moves
   - Suggests heuristic loses confidence in win paths
   - May indicate overcorrection in dynamic_live_ev_multiplier
   - Or indicates the board state no longer supports wins

3. Player 1 never sees significant Live EV until Turn 1-2
   - P1 consistently gets -0.0 live evaluation
   - Either P1 has poor win rate, or evaluator is pessimistic
   -This asymmetry may hurt P1's decision quality

IMPROVEMENT OPPORTUNITIES:
- Investigate why Turn 3 P0 Live EV (188.7) doesn't translate to actual win
- Check if dynamic_live_ev_multiplier is too aggressive in cooling down Live focus
- Review deficit-driven heart scoring - may be penalizing P1 too much
- Consider: Do ALL moves really have Live EV = -0.0 for P1?
""")

if __name__ == '__main__':
    analyze_data()
