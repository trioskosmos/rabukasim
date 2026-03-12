#!/usr/bin/env python3
"""
Measure actual branching factor and legal move sequences per turn.
Simple: just call the game engine and count legal actions at each state.
"""

import subprocess
import json
import sys

def get_legal_actions(state_json):
    """Call simple_game with a game state and get legal action count."""
    try:
        # Run one game and capture verbose output
        result = subprocess.run(
            ["engine_rust_src/target/release/simple_game.exe", "--count", "1", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="."
        )
        
        if result.returncode != 0:
            return None
        
        output = json.loads(result.stdout)
        return output
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def analyze_game_tree():
    """
    Run a game and print move statistics.
    """
    print("\n" + "="*70)
    print("ACTUAL LEGAL MOVE SEQUENCE ANALYSIS")
    print("="*70 + "\n")
    
    print("Running one 1-turn game to analyze move space...\n")
    
    # Run with depth=1 to see root branching only
    result = subprocess.run(
        ["engine_rust_src/target/release/simple_game.exe", 
         "--count", "1", 
         "--json",
         "--weight", "max_dfs_depth=1"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd="."
    )
    
    if result.returncode != 0:
        print("Error running game")
        print(result.stderr)
        return
    
    try:
        data = json.loads(result.stdout)
    except:
        print("Failed to parse output:")
        print(result.stdout[:500])
        return
    
    print("Game Statistics:\n")
    game = data["results"][0]
    print(f"  Seed: {game['seed']}")
    print(f"  Winner: P{game['winner'] if game['winner'] >= 0 else '?'}")
    print(f"  Score: P0={game['score_p0']} vs P1={game['score_p1']}")
    print(f"  Turns: {game['turns']}")
    print(f"  Total evaluations (depth=1): {game['evaluations']:,}")
    print(f"  Evaluations per turn: {game['evaluations'] / max(game['turns'], 1):.0f}")
    
    print("\n" + "-"*70)
    print("INTERPRETATION:\n")
    
    evals_per_turn = game['evaluations'] / max(game['turns'], 1)
    
    print(f"At depth=1, we visit {evals_per_turn:.0f} nodes per turn.")
    print(f"Each node = 1 legal action explored.")
    print(f"\nSo average legal actions per state = {evals_per_turn:.1f}")
    
    # Now test depth=2
    result2 = subprocess.run(
        ["engine_rust_src/target/release/simple_game.exe", 
         "--count", "1", 
         "--json",
         "--weight", "max_dfs_depth=2"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd="."
    )
    
    if result2.returncode == 0:
        try:
            data2 = json.loads(result2.stdout)
            game2 = data2["results"][0]
            evals_per_turn_2 = game2['evaluations'] / max(game2['turns'], 1)
            
            print(f"\nAt depth=2, we visit {evals_per_turn_2:.0f} nodes per turn.")
            branching = evals_per_turn_2 / evals_per_turn if evals_per_turn > 0 else 0
            print(f"Branching factor (depth2 / depth1): {branching:.2f}")
            
            print(f"\n" + "-"*70)
            print("ESTIMATE:\n")
            print(f"Average sequences per turn (approximate):")
            print(f"  With branching factor {branching:.2f}:")
            for d in range(1, 7):
                seqs = branching ** d
                print(f"    Depth {d}: ~{seqs:,.0f}")
        except:
            pass

if __name__ == "__main__":
    analyze_game_tree()
