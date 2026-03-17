#!/usr/bin/env python3
"""Quick test of vanilla comparison focusing on neural and MCTS."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig
import json

config = ComparisonConfig(
    db_path='data/cards_vanilla.json',
    checkpoint_path='checkpoints/vanilla_overnight/best.pt',
    deck_source='ai/decks/muse_cup.txt',
    time_per_move=0.5,
    num_games=2,
    seed_base=7000,
    verbosity=False,
)

comp = VanillaComparison(config)

# Test only neural and MCTS (skip problematic turnseq for now)
matchups = [
    ("neural", "random"),
    ("mcts", "random"),
    ("neural", "mcts"),
]

results = {}
for s1, s2 in matchups:
    print(f"\n{'='*60}")
    print(f"Testing: {s1} vs {s2}")
    print('='*60)
    
    result = comp.run_matchup(s1, s2, 2, 0.5)
    results[f"{s1}_vs_{s2}"] = {
        "strategy1": result.strategy1,
        "strategy2": result.strategy2,
        "strategy1_wins": result.strategy1_wins,
        "strategy2_wins": result.strategy2_wins,
        "draws": result.draws,
        "avg_turns_s1": result.avg_turns_s1,
        "avg_turns_s2": result.avg_turns_s2,
        "total_time": result.total_time,
    }
    
    # Compute computation statistics
    import numpy as np
    strategy_times = {"neural": [], "turnseq": [], "mcts": [], "random": []}
    
    for game_result in result.all_game_results:
        move_details = game_result.get("move_time_details", {})
        for strat, avg_time in move_details.items():
            if strat in strategy_times and avg_time > 0:
                strategy_times[strat].append(avg_time)
    
    print(f"\nResults: {s1}={result.strategy1_wins}, {s2}={result.strategy2_wins}, draws={result.draws}")
    print(f"Avg turns: {s1}={result.avg_turns_s1:.1f}, {s2}={result.avg_turns_s2:.1f}")
    print(f"Total time spent: {result.total_time:.2f}s")
    print(f"\nMove timing analysis:")
    for strat in ["neural", "turnseq", "mcts", "random"]:
        if strat in strategy_times and strategy_times[strat]:
            times = strategy_times[strat]
            print(f"  {strat:8s}: {np.mean(times):.4f}s avg per move (n={len(times)} games sampled)")
        elif strat in strategy_times:
            print(f"  {strat:8s}: no data")

# Print final summary
print(f"\n\n{'='*80}")
print("SUMMARY")
print('='*80)
for match_name, result in results.items():
    print(f"\n{result['strategy1'].upper()} vs {result['strategy2'].upper()}")
    print(f"  Wins: {result['strategy1']}={result['strategy1_wins']}, {result['strategy2']}={result['strategy2_wins']}")
    
# Save results
with open("vanilla_comparison_quick.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to vanilla_comparison_quick.json")
