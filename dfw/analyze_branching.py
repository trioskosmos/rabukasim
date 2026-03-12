#!/usr/bin/env python3
"""
Analyze actual branching factor from DFS search metrics.

Instead of enumerating all sequences (which is expensive), we analyze
the relationship between depth, nodes explored, and branching factor.
"""

import json
import subprocess
import sys

def run_game_analysis(depth):
    """Run game with given depth, return eval count"""
    cmd = [
        "engine_rust_src/target/release/simple_game.exe",
        "--count", "1",
        "--json",
        f"--weight", f"max_dfs_depth={depth}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        print(f"Error running depth {depth}: {result.stderr}")
        return None
    
    try:
        data = json.loads(result.stdout)
        return data['total_evaluations']
    except:
        print(f"Failed to parse JSON for depth {depth}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return None

def main():
    print("\n╔═════════════════════════════════════════════════════╗")
    print("║  Branching Factor Analysis from DFS Metrics       ║")
    print("╚═════════════════════════════════════════════════════╝\n")
    
    print("Testing different search depths to measure branching factor...\n")
    
    results = {}
    depths = [3, 4, 5, 6, 7, 8, 9, 10, 12, 15]
    
    for depth in depths:
        print(f"Testing depth={depth}...", end="", flush=True)
        evals = run_game_analysis(depth)
        
        if evals is None:
            print(f" FAILED")
            continue
        
        results[depth] = evals
        print(f" {evals:,} evaluations")
    
    print("\n╔═════════════════════════════════════════════════════╗")
    print("║  Analysis Results                                  ║")
    print("╚═════════════════════════════════════════════════════╝\n")
    
    print(f"{'Depth':<7} {'Nodes':<15} {'Branching':<12} {'per_level*':<12}")
    print("-" * 50)
    
    prev_depth = None
    prev_nodes = None
    
    for depth in sorted(results.keys()):
        nodes = results[depth]
        
        # Estimate avg branching per level: B^d = N, so B = N^(1/d)
        if depth > 0:
            avg_branching = nodes ** (1/depth) if nodes > 0 else 0
        else:
            avg_branching = 0
        
        # Change in nodes per additional depth
        if prev_depth is not None and depth > prev_depth:
            delta_d = depth - prev_depth
            delta_n = nodes / prev_nodes if prev_nodes > 0 else 0
            per_level = delta_n ** (1/delta_d)
        else:
            per_level = None
        
        per_str = f"{per_level:.2f}x" if per_level else "---"
        print(f"{depth:<7} {nodes:<15,} {avg_branching:<12.2f} {per_str:<12}")
        
        prev_depth = depth
        prev_nodes = nodes
    
    print("\n* 'per_level' shows effective branching between successive depths")
    print("\n╔═════════════════════════════════════════════════════╗")
    print("║  Key Insights                                      ║")
    print("╚═════════════════════════════════════════════════════╝\n")
    
    if len(results) >= 2:
        depths_sorted = sorted(results.keys())
        
        # Depth 9 should be threshold where move ordering kicks in
        depth_8_nodes = results.get(8)
        depth_9_nodes = results.get(9)
        depth_10_nodes = results.get(10)
        
        if depth_8_nodes and depth_9_nodes:
            ratio_8_to_9 = depth_9_nodes / depth_8_nodes
            print(f"Depth 8→9 ratio (no mov ordering yet): {ratio_8_to_9:.2f}x")
        
        if depth_9_nodes and depth_10_nodes:
            ratio_9_to_10 = depth_10_nodes / depth_9_nodes
            print(f"Depth 9→10 ratio (move ordering active): {ratio_9_to_10:.2f}x")
        
        print("\nObservation:")
        print("- If depth 10 has MUCH fewer nodes than depth 9 expects,")
        print("  move ordering is effectively pruning.")
        print("- Without move ordering, we expect ~3-4x increase per depth")
        print("  (due to board state branching)")
        print("- With move ordering, increase should be ~1.5-2x (less pruning)")
        
        # Analysis of depth 15 specifically
        depth_15_nodes = results.get(15)
        if depth_15_nodes and 15 in results:
            print(f"\nDepth 15 exploration: {depth_15_nodes:,} nodes")
            print("This is the actual search cost per full turn evaluation")
            
            # Estimate board states from sequence count
            # If N sequences lead to M unique boards, then M ≈ sequences / avg_permutations
            # For 6 actions, if order doesn't matter: M ≈ N / 6! = N / 720
            if depth_15_nodes > 0:
                estimated_states_if_ordered = depth_15_nodes / 720
                print(f"If sequences are ordered equivalent: ~{estimated_states_if_ordered:,.0f} unique board states")
                print(f"Actual sequences explored: {depth_15_nodes:,}")
                print(f"Ratio (redundancy): {depth_15_nodes / estimated_states_if_ordered:.1f}x")

if __name__ == "__main__":
    main()
