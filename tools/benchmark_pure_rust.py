import time
import json
from engine_rust import PyCardDatabase, PyGameState
from alphazero.training.overnight_vanilla import load_tournament_decks, load_vanilla_database_json

def benchmark_pure_rust():
    print("Loading database...")
    db_path = "data/cards_compiled.json"
    full_db, db_json = load_vanilla_database_json(db_path)
    db = PyCardDatabase(db_json)
    db.is_vanilla = False
    
    deck_source = "ai/decks/muse_cup.txt"
    print(f"Loading decks from {deck_source}...")
    decks = load_tournament_decks(full_db, deck_source)
    
    # Initialize game state
    game = PyGameState(db)
    
    num_games = 100
    print(f"Running {num_games} games entirely in Rust...")
    
    # Setup first game to have it ready if needed, 
    # though sim_random_games clones the internal state.
    p0_deck = random.choice(decks)
    p1_deck = random.choice(decks)
    game.initialize_game_with_seed(
        p0_deck["initial_deck"],
        p1_deck["initial_deck"],
        p0_deck["energy"],
        p1_deck["energy"],
        [],
        [],
        random.randint(0, 1000000)
    )
    
    start_time = time.time()
    results = game.sim_random_games(db, num_games)
    total_time = time.time() - start_time
    
    print("\n--- Pure Rust Benchmark Results ---")
    print(json.dumps(results, indent=2))
    print(f"Wall clock total time: {total_time:.2f}s")
    if total_time > 0:
        print(f"Wall clock MPS: {results['total_moves'] / total_time:.0f}")

if __name__ == "__main__":
    import random
    benchmark_pure_rust()
