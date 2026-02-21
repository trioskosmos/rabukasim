import os
import random
import sys
import time

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

# Mock Numba to toggle it
import lovecasim_engine as rust_engine

import engine.game.numba_utils as numba_utils
from engine.game.game_state import initialize_game as py_initialize_game


def run_numba_benchmark(num_steps=5000):
    print(f"Starting Numba vs Rust Comparison: {num_steps} steps...")

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        card_data_json = f.read()

    rust_db = rust_engine.PyCardDatabase(card_data_json)
    py_initialize_game(use_real_data=True, deck_type="vanilla")

    m_ids = [1]  # Generic ID
    l_ids = [100]
    p0_deck = (m_ids * 50)[:48]
    p1_deck = (m_ids * 50)[:48]
    p0_lives = (l_ids * 10)[:12]
    p1_lives = (l_ids * 10)[:12]

    results = {}

    # 1. Python + Numba (Default)
    numba_utils.JIT_AVAILABLE = True
    print("\n[1] Benchmarking Python + Numba...")
    start = time.perf_counter()
    gs = py_initialize_game(use_real_data=True, deck_type="vanilla")
    steps = 0
    while steps < num_steps:
        mask = gs.get_legal_actions()
        actions = np.where(mask)[0]
        if len(actions) == 0:
            break
        gs.step(random.choice(actions))
        steps += 1
        if gs.is_terminal():
            gs = py_initialize_game(use_real_data=True, deck_type="vanilla")
    end = time.perf_counter()
    results["Py+Numba"] = (end - start) * 1000 / steps
    print(f"  Avg: {results['Py+Numba']:.4f} ms/step")

    # 2. Pure Python (Disable Numba)
    numba_utils.JIT_AVAILABLE = False
    print("\n[2] Benchmarking Pure Python (Numba Disabled)...")
    start = time.perf_counter()
    gs = py_initialize_game(use_real_data=True, deck_type="vanilla")
    steps = 0
    while steps < num_steps:
        mask = gs.get_legal_actions()
        actions = np.where(mask)[0]
        if len(actions) == 0:
            break
        gs.step(random.choice(actions))
        steps += 1
        if gs.is_terminal():
            gs = py_initialize_game(use_real_data=True, deck_type="vanilla")
    end = time.perf_counter()
    results["Py_Pure"] = (end - start) * 1000 / steps
    print(f"  Avg: {results['Py_Pure']:.4f} ms/step")

    # 3. Rust (via Bindings)
    print("\n[3] Benchmarking Rust (via Python Bindings)...")
    start = time.perf_counter()
    gs = rust_engine.PyGameState(rust_db)
    gs.initialize_game_with_seed(p0_deck, p1_deck, [], [], p0_lives, p1_lives, 42)
    steps = 0
    while steps < num_steps:
        mask = gs.get_legal_actions()
        actions = [i for i, v in enumerate(mask) if v]
        if not actions:
            break
        gs.step(random.choice(actions))
        steps += 1
        if gs.is_terminal():
            gs = rust_engine.PyGameState(rust_db)
            gs.initialize_game_with_seed(p0_deck, p1_deck, [], [], p0_lives, p1_lives, 42 + steps)
    end = time.perf_counter()
    results["Rust_Py"] = (end - start) * 1000 / steps
    print(f"  Avg: {results['Rust_Py']:.4f} ms/step")

    print("\n--- SUMMARY ---")
    print(f"Python Pure:  {results['Py_Pure']:.4f} ms/step")
    print(f"Python+Numba: {results['Py+Numba']:.4f} ms/step ({results['Py_Pure'] / results['Py+Numba']:.1f}x vs Py)")
    print(
        f"Rust Bind:    {results['Rust_Py']:.4f} ms/step ({results['Py_Pure'] / results['Rust_Py']:.1f}x vs Py, {results['Py+Numba'] / results['Rust_Py']:.1f}x vs Numba)"
    )

    # Static Ref
    rust_native = 0.0015
    print(
        f"Rust Native:  {rust_native:.4f} ms/step ({results['Py_Pure'] / rust_native:.1f}x vs Py, {results['Py+Numba'] / rust_native:.1f}x vs Numba)"
    )


if __name__ == "__main__":
    run_numba_benchmark(2000)
