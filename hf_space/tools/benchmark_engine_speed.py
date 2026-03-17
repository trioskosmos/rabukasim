#!/usr/bin/env python3
"""
Benchmark engine speed (Moves Per Second) with full rules (abilities enabled).
"""

import json
import os
import sys
import time
import random
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import engine_rust
try:
    from engine_rust.engine_rust import PyCardDatabase, PyGameState
except ImportError:
    print("Error: engine_rust not found. Please ensure it's compiled and in the path.")
    sys.exit(1)

# Import training infrastructure for deck loading
try:
    from alphazero.training.overnight_vanilla import load_tournament_decks
except ImportError:
    # Minimal fallback for deck loading if infrastructure is missing
    def load_tournament_decks(full_db, source_path):
        # Very basic implementation if the real one fails
        with open(source_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        decks = []
        for line in lines:
            if line.strip() and not line.startswith("#"):
                parts = line.split("|")
                if len(parts) >= 2:
                    card_ids = [int(x) for x in parts[0].split(",")]
                    energy = int(parts[1])
                    decks.append({"initial_deck": card_ids, "energy": energy})
        return decks

def run_benchmark(num_games=100):
    db_path = ROOT_DIR / "data" / "cards_compiled.json"
    deck_source = ROOT_DIR / "ai" / "decks" / "muse_cup.txt"
    
    print(f"Loading database from {db_path}...")
    with open(db_path, "r", encoding="utf-8") as f:
        db_json = f.read()
    
    rust_db = PyCardDatabase(db_json)
    rust_db.is_vanilla = False  # Full rules (abilities on)
    
    print(f"Starting pure Rust benchmark: {num_games} games...")
    
    # Create a dummy game state to call sim_random_games
    game = PyGameState(rust_db)
    
    # Initialize with dummy decks
    deck = list(range(1, 51))  # Deck ID 1-50
    energy = [50] * 12  # Energy deck (12 cards, each worth 50 energy)
    game.initialize_game_with_seed(deck, deck, energy, energy, [], [], 0)
    
    print("Running games in pure Rust (no Python overhead)...\n")
    
    overall_start = time.perf_counter()
    
    # Use pure Rust batch simulation
    results = game.sim_random_games(rust_db, num_games)
    
    overall_end = time.perf_counter()
    overall_duration = overall_end - overall_start
    
    pure_mps = results.get("mps", 0)
    total_games = results.get("total_games", 0)
    total_moves = results.get("total_moves", 0)
    gameplay_seconds = results.get("gameplay_seconds", 0)
    
    print("\n" + "="*45)
    print("BENCHMARK RESULTS (Pure Rust - No Python Loop)")
    print("="*45)
    print(f"Total Games:           {total_games}")
    print(f"Total Moves:           {total_moves}")
    print(f"Total Program Time:    {overall_duration:.2f}s")
    print(f"Pure Gameplay Time:    {gameplay_seconds:.2f}s")
    print(f"Pure Moves Per Second: {pure_mps:.2f}")
    print(f"Pure Games Per Second: {total_games/gameplay_seconds:.2f}")
    print("="*45)
    
    # Save to JSON
    output_data = {
        "total_games": total_games,
        "total_moves": total_moves,
        "pure_mps": pure_mps,
        "pure_gps": total_games/gameplay_seconds if gameplay_seconds > 0 else 0,
        "avg_moves_per_game": total_moves / total_games if total_games > 0 else 0,
        "metadata": results
    }
    with open("bench_results.json", "w") as f:
        json.dump(output_data, f, indent=4)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    args = parser.parse_args()
    
    run_benchmark(args.games)
