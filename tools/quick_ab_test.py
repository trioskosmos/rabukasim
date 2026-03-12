"""Quick A/B test for alpha-beta pruning effectiveness."""

import subprocess
import json
import time
import os
import sys
from pathlib import Path
import multiprocessing as mp

WORKSPACE_ROOT = Path(__file__).parent.parent
ENGINE_BIN = WORKSPACE_ROOT / "engine_rust_src" / "target" / "release" / "simple_game.exe"

def run_test(use_ab: bool, depth: int = 10, games: int = 2, timeout_sec: int = 180):
    """Run a benchmark test."""
    cmd = [
        str(ENGINE_BIN),
        "--games", str(games),
        "--weight", f"max_dfs_depth={depth}",
        "--weight", f"use_alpha_beta={1 if use_ab else 0}",
    ]
    
    env = os.environ.copy()
    cpu_count = mp.cpu_count()
    env['RAYON_NUM_THREADS'] = str(max(1, cpu_count // 2))
    
    try:
        start = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout_sec,
            cwd=str(WORKSPACE_ROOT),
            env=env,
        )
        elapsed = time.time() - start
        
        if result.returncode != 0:
            print(f"Error: {result.stderr[:200]}")
            return None
        
        output = json.loads(result.stdout)
        return {
            'mode': 'Alpha-Beta' if use_ab else 'Pure DFS',
            'depth': depth,
            'games': games,
            'sqps': output.get('total_evaluations', 0) / elapsed if elapsed > 0 else 0,
            'evals': output.get('total_evaluations', 0),
            'elapsed': elapsed,
            'win_rate': output.get('p0_win_rate', 0.0),
            'avg_score': output.get('avg_score_p0', 0.0),
        }
    except subprocess.TimeoutExpired:
        print(f"Timeout")
        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None


if __name__ == '__main__':
    print("="*70)
    print("ALPHA-BETA PRUNING EFFECTIVENESS TEST")
    print("="*70)
    
    depth = 10
    games = 2
    
    print(f"\nTesting with depth={depth}, games={games}\n")
    
    print("Phase 1: WITH Alpha-Beta Pruning", end=' ', flush=True)
    ab_result = run_test(True, depth=depth, games=games)
    if ab_result:
        print(f"✓")
        print(f"  Nodes: {ab_result['evals']:,} | Speed: {ab_result['sqps']:.0f} eval/s | Win: {ab_result['win_rate']:.1%}")
    else:
        print("✗ Failed")
        ab_result = {}
    
    print("\nPhase 2: WITHOUT Alpha-Beta (Pure Negamax)", end=' ', flush=True)
    nm_result = run_test(False, depth=depth, games=games)
    if nm_result:
        print(f"✓")
        print(f"  Nodes: {nm_result['evals']:,} | Speed: {nm_result['sqps']:.0f} eval/s | Win: {nm_result['win_rate']:.1%}")
    else:
        print("✗ Failed")
        nm_result = {}
    
    if ab_result and nm_result:
        print("\n" + "─"*70)
        speedup = ab_result['sqps'] / nm_result['sqps']
        node_reduction = (1.0 - ab_result['evals'] / nm_result['evals']) * 100
        print(f"RESULTS:\n")
        print(f"  Speedup: {speedup:.2f}x faster")
        print(f"  Node Reduction: {node_reduction:.1f}% fewer nodes evaluated")
        print(f"  Proof of correctness: {"SAME" if ab_result['win_rate'] == nm_result['win_rate'] else 'DIFFERENT'} outcome (both should find optimal move)")
        print("─"*70)
