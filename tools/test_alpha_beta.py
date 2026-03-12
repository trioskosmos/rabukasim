#!/usr/bin/env python3
"""Quick A/B test of alpha-beta pruning effectiveness."""

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

from heuristic_tuner import HeuristicTuner

if __name__ == '__main__':
    tuner = HeuristicTuner(games_per_config=2, timeout_sec=180)
    
    print("\n" + "="*70)
    print("ALPHA-BETA PRUNING: Effectiveness Demonstration")
    print("="*70)
    
    ab_result, nm_result = tuner.test_alpha_beta_effectiveness()
    
    if ab_result and nm_result:
        print(f"\n{'─'*70}")
        print(f"RESULTS COMPARISON:")
        print(f"{'─'*70}")
        print(f"\nWith Alpha-Beta:")
        print(f"  Evaluations: {ab_result.total_evaluations:>10}")
        print(f"  Elapsed:     {ab_result.elapsed_secs:>10.2f}s")
        print(f"  Eval/s:      {ab_result.sqps:>10.0f}")
        print(f"  Win Rate:    {ab_result.win_rate:>10.1%}")
        
        print(f"\nWithout Alpha-Beta (Pure DFS):")
        print(f"  Evaluations: {nm_result.total_evaluations:>10}")
        print(f"  Elapsed:     {nm_result.elapsed_secs:>10.2f}s")
        print(f"  Eval/s:      {nm_result.sqps:>10.0f}")
        print(f"  Win Rate:    {nm_result.win_rate:>10.1%}")
        
        speedup = ab_result.sqps / nm_result.sqps if nm_result.sqps > 0 else 0
        node_reduction = (1.0 - ab_result.total_evaluations / nm_result.total_evaluations) * 100 if nm_result.total_evaluations > 0 else 0
        time_reduction = (1.0 - ab_result.elapsed_secs / nm_result.elapsed_secs) * 100 if nm_result.elapsed_secs > 0 else 0
        
        print(f"\n{'─'*70}")
        print(f"IMPROVEMENT METRICS:")
        print(f"{'─'*70}")
        print(f"  Speedup (eval/s):     {speedup:.2f}x faster")
        print(f"  Node reduction:       {node_reduction:.1f}%")
        print(f"  Time reduction:       {time_reduction:.1f}%")
        print(f"  Quality preserved:    {ab_result.win_rate == nm_result.win_rate} (same win rate)")
        print(f"{'─'*70}\n")
    else:
        print("Error: Could not complete A/B test")
