#!/usr/bin/env python3
"""
OPTIMIZED benchmarking: Use pure Rust sim_random_games for maximum speed.
This bypasses Python loop entirely and runs games in compiled Rust.
"""

import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from engine_rust.engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_tournament_decks, load_vanilla_database_json

def run_benchmark(num_games=100):
    db_path = ROOT_DIR / "data" / "cards_compiled.json"
    deck_source = ROOT_DIR / "ai" / "decks" / "muse_cup.txt"
    
    print(f"Loading database...")
    full_db, db_json = load_vanilla_database_json(db_path)
    
    rust_db = PyCardDatabase(db_json)
    rust_db.is_vanilla = False  # Full rules enabled
    
    print(f"Loading decks from tournament pool...")
    decks = load_tournament_decks(full_db, deck_source)
    
    if not decks:
        print("ERROR: No decks loaded")
        return
    
    # Create game state
    game = PyGameState(rust_db)
    selected_deck = decks[0]
    game.initialize_game_with_seed(
        selected_deck["initial_deck"],
        selected_deck["initial_deck"],
        selected_deck["energy"],
        selected_deck["energy"],
        [], [], 42
    )
    
    print(f"\n[RUNNING] {num_games} games in pure Rust (no Python loop overhead)...\n")
    
    overall_start = time.perf_counter()
    
    # Pure Rust batch simulation - this is THE way to get max speed!
    results = game.sim_random_games(rust_db, num_games)
    
    overall_end = time.perf_counter()
    overall_duration = overall_end - overall_start
    
    pure_mps = results.get("mps", 0)
    total_games = results.get("total_games", 0)
    total_moves = results.get("total_moves", 0)
    meaningful_moves = results.get("total_meaningful_moves", 0)
    gameplay_seconds = results.get("gameplay_seconds", 0)
    
    print("=" * 70)
    print("[PURE RUST ENGINE BENCHMARK - Maximum Possible Speed]")
    print("=" * 70)
    print(f"Total Games:              {total_games}")
    print(f"Total Moves:              {total_moves:,}")
    print(f"Meaningful Moves:         {meaningful_moves:,}")
    print(f"Gameplay Time (Rust):     {gameplay_seconds:.4f}s")
    print(f"Total Program Time:       {overall_duration:.4f}s")
    print(f"\n[RESULTS]")
    print(f"  Moves Per Second:       {pure_mps:,.0f} MPS")
    print(f"  Games Per Second:       {total_games/gameplay_seconds:,.2f} GPS")
    print(f"  Avg Moves Per Game:     {total_moves/total_games:.1f}")
    print(f"\n[EFFICIENCY]")
    print(f"  Per-Move Cost:          {gameplay_seconds/total_moves*1e6:.2f} microseconds")
    print("=" * 70)
    print(f"\n[ACTION TIMINGS]")
    action_timings = results.get("action_timings", {})
    if action_timings:
        # Sort by average time
        sorted_actions = sorted(action_timings.items(), key=lambda x: x[1]["avg_time"], reverse=True)
        
        print(f"{'Action Category':<25} | {'Count':<8} | {'Avg (µs)':<10} | {'Total (s)':<10}")
        print("-" * 70)
        for cat, stats in sorted_actions:
            avg_us = stats["avg_time"] * 1e6
            print(f"{cat:<25} | {stats['count']:<8} | {avg_us:<10.2f} | {stats['total_time']:<10.4f}")
        
        print("-" * 70)
        print(f"Longest Action:  {sorted_actions[0][0]} ({sorted_actions[0][1]['avg_time']*1e6:.2f} µs)")
        print(f"Shortest Action: {sorted_actions[-1][0]} ({sorted_actions[-1][1]['avg_time']*1e6:.2f} µs)")
    else:
        print("No action timing data available.")
    
    # Save results
    output_data = {
        "benchmark": "pure_rust_sim",
        "total_games": total_games,
        "total_moves": total_moves,
        "meaningful_moves": meaningful_moves,
        "pure_mps": pure_mps,
        "pure_gps": total_games/gameplay_seconds if gameplay_seconds > 0 else 0,
        "gameplay_seconds": gameplay_seconds,
        "program_time": overall_duration,
        "avg_moves_per_game": total_moves / total_games if total_games > 0 else 0,
        "action_timings": action_timings,
    }
    with open("bench_results.json", "w") as f:
        json.dump(output_data, f, indent=4)
    
    print("\nResults saved to bench_results.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    args = parser.parse_args()
    
    run_benchmark(args.games)
