import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import json
import time
import concurrent.futures
from alphazero.training.overnight_pure_zero import play_one_game, load_tournament_decks, init_worker

def benchmark_cpu_generation():
    print("\n--- CPU Game Generation Benchmark ---")
    db_path = root_dir / "data" / "cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_json_str = json.dumps(full_db)
    
    # Initialize workers (this is normally done per-process in concurrent.futures)
    init_worker(db_json_str)
    
    decks = load_tournament_decks(full_db)
    if len(decks) < 2:
        print("Error: Not enough decks for benchmarking.")
        return
        
    d0, d1 = decks[0], decks[1]
    
    # Settings for benchmark
    sims = 128
    num_games = 4 # Small count for quick benchmark
    
    print(f"Simulating {num_games} games with {sims} sims/move on CPU...")
    
    start = time.time()
    total_moves = 0
    
    # We use a single thread first to get the base "1 Core" speed
    for i in range(num_games):
        print(f"Starting game {i+1}...")
        game_start = time.time()
        transitions = play_one_game(d0, d1, sims, dirichlet_alpha=0.3, dirichlet_eps=0.25)
        game_time = time.time() - game_start
        total_moves += len(transitions)
        print(f"Game {i+1} complete: {len(transitions)} moves in {game_time:.2f}s ({len(transitions)/game_time:.2f} moves/sec)")
        
    total_time = time.time() - start
    print(f"\nTotal moves generated: {total_moves}")
    print(f"Average throughput (Single Core): {total_moves/total_time:.2f} moves/sec")
    
    # Estimate multi-core speed (assuming roughly 80% efficiency on typical CPUs)
    # We won't actually run it to save time, but we can report the single core reality.

if __name__ == "__main__":
    benchmark_cpu_generation()
