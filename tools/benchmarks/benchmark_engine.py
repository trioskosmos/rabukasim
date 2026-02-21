import os
import random
import sys
import time

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

import lovecasim_engine as rust_engine

from engine.game.game_state import GameState as PyGameState
from engine.game.game_state import initialize_game as py_initialize_game


def run_benchmark(num_games=10, parity_check=True):
    print(f"Starting Detailed Engine Benchmark: {num_games} games...")

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        card_data_json = f.read()

    rust_db = rust_engine.PyCardDatabase(card_data_json)
    py_initialize_game(use_real_data=True, deck_type="vanilla")

    m_ids = []
    l_ids = []
    for cid, card in PyGameState.member_db.items():
        if card.card_no in ["PL!-sd1-010-SD", "PL!-sd1-013-SD", "PL!-sd1-014-SD", "PL!-sd1-017-SD", "PL!-sd1-018-SD"]:
            m_ids.append(cid)
    for cid, card in PyGameState.live_db.items():
        if card.card_no in ["PL!-sd1-019-SD", "PL!-sd1-020-SD", "PL!-sd1-021-SD", "PL!-sd1-022-SD"]:
            l_ids.append(cid)

    if not m_ids:
        m_ids = [1]
    if not l_ids:
        l_ids = [100]

    p0_deck = (m_ids * 10)[:48]
    p1_deck = (m_ids * 10)[:48]
    p0_lives = (l_ids * 5)[:12]
    p1_lives = (l_ids * 5)[:12]

    seeds = [42, 123, 999, 1337, 2024]
    if num_games > len(seeds):
        seeds.extend([random.randint(0, 1000000) for _ in range(num_games - len(seeds))])
    seeds = seeds[:num_games]

    print(f"| {'Game':<5} | {'P Steps':<8} | {'R Steps':<8} | {'P Time':<10} | {'R Time':<10} | {'Status':<10} |")
    print(f"|{'-' * 7}|{'-' * 10}|{'-' * 10}|{'-' * 12}|{'-' * 12}|{'-' * 12}|")

    for i in range(num_games):
        seed = seeds[i]

        # --- RUST GAME ---
        rust_start = time.perf_counter()
        gs_rust = rust_engine.PyGameState(rust_db)
        gs_rust.initialize_game_with_seed(p0_deck, p1_deck, [], [], p0_lives, p1_lives, seed)

        rust_steps = 0
        phases_hit = set()
        while not gs_rust.is_terminal() and rust_steps < 1000:
            phases_hit.add(gs_rust.phase)
            mask = gs_rust.get_legal_actions()
            actions = [idx for idx, legal in enumerate(mask) if legal]
            if not actions:
                break
            rng = random.Random(seed + rust_steps)
            gs_rust.step(rng.choice(actions))
            rust_steps += 1
        rust_end = time.perf_counter()
        rust_time = (rust_end - rust_start) * 1000

        # --- PYTHON GAME ---
        py_start = time.perf_counter()
        # Note: PyGameState needs seed for internal random calls
        random.seed(seed)
        np.random.seed(seed)
        gs_py = py_initialize_game(use_real_data=True, deck_type="vanilla")

        py_steps = 0
        while not gs_py.is_terminal() and py_steps < 1000:
            mask = gs_py.get_legal_actions()
            actions = np.where(mask)[0]
            if len(actions) == 0:
                break
            rng = random.Random(seed + py_steps)
            gs_py.step(rng.choice(actions))
            py_steps += 1
        py_end = time.perf_counter()
        py_time = (py_end - py_start) * 1000

        status = (
            "BOTH_TERM"
            if gs_rust.is_terminal() and gs_py.is_terminal()
            else "R_STUCK"
            if not gs_rust.is_terminal()
            else "P_STUCK"
            if not gs_py.is_terminal()
            else "BOTH_STUCK"
        )

        print(f"| {i:<5} | {py_steps:>8} | {rust_steps:>8} | {py_time:>9.2f} | {rust_time:>9.2f} | {status:<10} |")
        if not gs_rust.is_terminal():
            print(
                f"  [Rust Trace] Final Phase: {gs_rust.phase}, Player: {gs_rust.current_player}, Turn: {gs_rust.turn}, Score: {gs_rust.get_player(0).score} vs {gs_rust.get_player(1).score}"
            )


if __name__ == "__main__":
    run_benchmark(5)
