import os

import engine_rust


def run_profiled_game():
    print("Starting Profiled MCTS Game...")

    # Path handling
    cards_path = "data/cards_compiled.json"
    if not os.path.exists(cards_path):
        print(f"Error: {cards_path} not found.")
        return

    with open(cards_path, "r", encoding="utf-8") as f:
        db_content = f.read()
    db = engine_rust.PyCardDatabase(db_content)

    # Member IDs (Standard R/SR cards)
    member_ids = [0, 1, 2, 3, 4, 107, 108, 109, 110, 111]
    # Live IDs (from 30000 range)
    live_ids = [30000, 30001, 30002]
    # Energy IDs (usually 2000+)
    energy_ids = [2000]  # Pink Energy

    deck = [member_ids[i % len(member_ids)] for i in range(40)]
    lives = [live_ids[i % len(live_ids)] for i in range(3)]
    energies = [energy_ids[0]] * 12

    g = engine_rust.PyGameState(db)
    g.initialize_game_with_seed(deck, deck, energies, energies, lives, lives, 42)

    print("\nRunning MCTS vs MCTS (1000 sims/move)...")
    # This should now trigger the internal profiling prints
    winner, turns = g.play_mirror_match(1000, 1000, 0, 0, engine_rust.SearchHorizon.TurnEnd)

    print(f"\nGame Result: {winner} in {turns} turns.")


if __name__ == "__main__":
    run_profiled_game()
