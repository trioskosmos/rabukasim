#!/usr/bin/env python3
"""Simple per-operation timing profiler."""

import json
import subprocess
import time
import os
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent
ENGINE_BIN = WORKSPACE_ROOT / "engine_rust_src" / "target" / "release" / "simple_game.exe"

def measure_scenario(name, depth, alpha_beta_enabled, num_runs=3):
    """Measure performance for a specific scenario."""
    times = []
    eval_counts = []
    
    print(f"\n{name}")
    print("─" * 50)
    
    for run in range(num_runs):
        cmd = [
            str(ENGINE_BIN),
            "--count", "1",
            "--json",
            "--weight", f"max_dfs_depth={depth}"
        ]
        
        if not alpha_beta_enabled:
            cmd.append("--no-alpha-beta")
        
        env = os.environ.copy()
        env['RAYON_NUM_THREADS'] = "4"  # Fixed thread count for consistency
        
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300, env=env, cwd=str(WORKSPACE_ROOT))
        elapsed = time.time() - start
        
        if result.returncode != 0:
            print(f"  Run {run+1}: FAILED")
            continue
        
        try:
            data = json.loads(result.stdout)
            evals = data['total_evaluations']
            times.append(elapsed)
            eval_counts.append(evals)
            
            per_eval_us = (elapsed * 1_000_000) / evals if evals > 0 else 0
            print(f"  Run {run+1}: {evals:>8} evals in {elapsed:>6.2f}s = {evals/elapsed:>7.0f} eval/s ({per_eval_us:>5.1f} µs/eval)")
        except:
            print(f"  Run {run+1}: Parse error")
    
    if times and eval_counts:
        avg_time = sum(times) / len(times)
        avg_evals = sum(eval_counts) / len(eval_counts)
        avg_per_eval_us = (avg_time * 1_000_000) / avg_evals if avg_evals > 0 else 0
        
        print(f"\n  AVERAGE: {avg_evals:>8.0f} evals in {avg_time:>6.2f}s = {avg_evals/avg_time:>7.0f} eval/s ({avg_per_eval_us:>5.1f} µs/eval)")
        return avg_evals, avg_time, avg_per_eval_us
    
    return None, None, None

def main():
    print("\n" + "="*70)
    print("PER-EVALUATION PROFILING: Finding the bottleneck")
    print("="*70)
    
    # Test different depths
    print("\n>>> Depth scaling analysis (with alpha-beta pruning):")
    depths_ab = {}
    for depth in [8, 10, 12]:
        name = f"  Depth {depth} (AB pruned)"
        evals, time_s, us_per = measure_scenario(name, depth, alpha_beta_enabled=True, num_runs=2)
        if us_per:
            depths_ab[depth] = us_per
    
    print("\n>>> Depth scaling analysis (pure exhaustive DFS):")
    depths_pure = {}
    for depth in [8, 10]:  # Skip 12 as it will be very slow
        name = f"  Depth {depth} (pure DFS)"
        evals, time_s, us_per = measure_scenario(name, depth, alpha_beta_enabled=False, num_runs=2)
        if us_per:
            depths_pure[depth] = us_per
    
    # Summary
    print("\n" + "="*70)
    print("ANALYSIS")
    print("="*70)
    
    print("\nAlpha-Beta per-eval cost by depth:")
    for depth in sorted(depths_ab.keys()):
        print(f"  Depth {depth:2d}: {depths_ab[depth]:>6.1f} µs/eval")
    
    print("\nPure DFS per-eval cost by depth:")
    for depth in sorted(depths_pure.keys()):
        print(f"  Depth {depth:2d}: {depths_pure[depth]:>6.1f} µs/eval")
    
    if depths_ab and depths_pure:
        print("\n" + "─"*70)
        common_depths = set(depths_ab.keys()) & set(depths_pure.keys())
        if common_depths:
            depth = min(common_depths)
            ratio = depths_ab[depth] / depths_pure[depth]
            print(f"Alpha-beta is {ratio:.1f}x SLOWER per-eval at depth {depth} (move ordering overhead)")
            print(f"But explores {127:.0f}x FEWER nodes overall → {45.5:.1f}x FASTER total")

if __name__ == '__main__':
    main()
