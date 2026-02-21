import os
import random
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

import engine_rust as rust_engine


def run_final_benchmark(num_steps=10000):
    print(f"Starting Final High-Speed Rust-Python Benchmark: {num_steps} steps...")

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        card_data_json = f.read()

    rust_db = rust_engine.PyCardDatabase(card_data_json)

    m_ids = [1]
    l_ids = [100]
    p0_deck = (m_ids * 50)[:48]
    p1_deck = (m_ids * 50)[:48]
    p0_lives = (l_ids * 10)[:12]
    p1_lives = (l_ids * 10)[:12]

    gs = rust_engine.PyGameState(rust_db)
    gs.initialize_game_with_seed(p0_deck, p1_deck, [], [], p0_lives, p1_lives, 42)

    start = time.perf_counter()
    steps = 0
    while steps < num_steps:
        # USE OPTIMIZED ACCESSOR
        actions = gs.get_legal_action_ids()
        if not actions:
            break

        # In Python we still have some overhead for random selection
        gs.step(random.choice(actions))
        steps += 1

        if gs.is_terminal():
            gs = rust_engine.PyGameState(rust_db)
            gs.initialize_game_with_seed(p0_deck, p1_deck, [], [], p0_lives, p1_lives, 42 + steps)

    end = time.perf_counter()
    duration = end - start
    print("--- RESULTS ---")
    print(f"Total Steps: {steps}")
    print(f"Total Time:  {duration:.4f}s")
    print(f"Steps/sec:   {steps / duration:.2f}")
    print(f"Avg Time:    {duration * 1000 / steps:.6f} ms/step")


if __name__ == "__main__":
    run_final_benchmark(10000)
