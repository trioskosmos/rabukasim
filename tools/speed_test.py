#!/usr/bin/env python3
"""
Quick performance test - run all strategies at maximum speed.
Useful for benchmarking optimizations.
"""

import argparse
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.perf_optimizations import disable_debug_logging, enable_torch_optimizations

# Enable optimizations first (before importing models)
disable_debug_logging()
enable_torch_optimizations()

from tools.compare_vanilla_strategies import VanillaComparison, ComparisonConfig

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=5)
    parser.add_argument("--time-per-move", type=float, default=0.1)
    parser.add_argument("--strategy", choices=["neural", "turnseq", "mcts", "random"], default="neural")
    args = parser.parse_args()
    
    config = ComparisonConfig(
        time_per_move=args.time_per_move,
        num_games=1,
    )
    comp = VanillaComparison(config)
    
    print(f"Running {args.games} games with {args.strategy} strategy...")
    print(f"Time per move: {args.time_per_move}s")
    print()
    
    total_time = 0
    total_moves = 0
    
    for i in range(args.games):
        start = time.time()
        result = comp.play_game(
            seed=5000 + i,
            strategy_p0=args.strategy,
            strategy_p1="random",  # Opponent is always random for baseline
            time_limit=args.time_per_move
        )
        elapsed = time.time() - start
        total_time += elapsed
        total_moves += result["total_moves"]
        
        winner = result["winner"]
        winner_str = f"P{winner} wins" if winner >= 0 else "Draw"
        mps = result['total_moves']/elapsed if elapsed > 0.0001 else result['total_moves']/0.0001
        print(f"Game {i+1}: {winner_str}, {result['turns']} turns, {elapsed:.3f}s, "
              f"{result['total_moves']} moves @ {mps:.0f} moves/sec")
    
    print()
    print("=" * 60)
    print(f"Total: {args.games} games, {total_moves} moves in {total_time:.2f}s")
    print(f"Average: {total_moves/total_time:.0f} moves per second")
    print(f"Average game time: {total_time/args.games:.3f}s")
    print("=" * 60)

if __name__ == "__main__":
    main()
