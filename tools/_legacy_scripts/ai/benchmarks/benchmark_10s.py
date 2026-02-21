import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from engine.game.ai_compat import njit
from engine.game.fast_logic import resolve_bytecode
from engine.game.game_state import GameState
from engine.models.opcodes import Opcode

# Constants for Fast Logic
G_P_HAND_SIZE = 3
G_P_DECK_SIZE = 6
G_TURN = 2


@njit(cache=True)
def run_numba_batch(
    bytecode: np.ndarray,
    batch_size: int,
    flat_ctx: np.ndarray,
    global_ctx: np.ndarray,
    p_hand: np.ndarray,
    p_deck: np.ndarray,
    p_stage: np.ndarray,
    p_energy_vec: np.ndarray,
    p_energy_count: np.ndarray,
    p_cont_vec: np.ndarray,
    p_tapped: np.ndarray,
    p_live: np.ndarray,
    opp_tapped: np.ndarray,
):
    for _ in range(batch_size):
        # Reset simple state for consistency
        global_ctx[G_P_DECK_SIZE] = 50
        global_ctx[G_P_HAND_SIZE] = 0

        resolve_bytecode(
            bytecode,
            flat_ctx,
            global_ctx,
            0,
            p_hand,
            p_deck,
            p_stage,
            p_energy_vec,
            p_energy_count,
            p_cont_vec,
            0,
            p_tapped,
            p_live,
            opp_tapped,
        )
    return 0


def benchmark_10s():
    duration = 10.0

    # --- Data Setup ---
    flat_ctx = np.zeros(64, dtype=np.int32)
    global_ctx = np.zeros(128, dtype=np.int32)
    p_stage = np.full(3, -1, dtype=np.int32)
    p_deck = np.zeros(50, dtype=np.int32)
    p_hand = np.zeros(50, dtype=np.int32)
    p_stage_energy_vec = np.zeros((3, 32), dtype=np.int32)
    p_stage_energy_count = np.zeros(3, dtype=np.int32)
    p_continuous_effects_vec = np.zeros((32, 10), dtype=np.int32)
    p_tapped_members = np.zeros(3, dtype=np.int32)
    p_live_revealed = np.zeros(3, dtype=np.int32)
    opp_tapped_members = np.zeros(3, dtype=np.int32)

    # DRAW 2 bytecode
    bytecode = np.array([[int(Opcode.DRAW), 2, 0, 0]], dtype=np.int32)

    # --- VERIFY WORKABILITY ---
    print("\n--- Correctness Check ---")
    global_ctx[G_P_DECK_SIZE] = 10
    global_ctx[G_P_HAND_SIZE] = 0
    resolve_bytecode(
        bytecode,
        flat_ctx,
        global_ctx,
        0,
        p_hand,
        p_deck,
        p_stage,
        p_stage_energy_vec,
        p_stage_energy_count,
        p_continuous_effects_vec,
        0,
        p_tapped_members,
        p_live_revealed,
        opp_tapped_members,
    )
    print("Initial: Deck=10, Hand=0")
    print(f"After Draw 2: Deck={global_ctx[G_P_DECK_SIZE]}, Hand={global_ctx[G_P_HAND_SIZE]}")
    if global_ctx[G_P_HAND_SIZE] == 2:
        print("Success: DRAW 2 works correctly!")
    else:
        print("Failure: DRAW 2 did not work as expected.")

    # --- NUMBA BENCHMARK ---
    print(f"\n--- Numba Benchmark (Running for {duration} seconds) ---")
    # Warmup
    run_numba_batch(
        bytecode,
        100,
        flat_ctx,
        global_ctx,
        p_hand,
        p_deck,
        p_stage,
        p_stage_energy_vec,
        p_stage_energy_count,
        p_continuous_effects_vec,
        p_tapped_members,
        p_live_revealed,
        opp_tapped_members,
    )

    total_iters = 0
    batch_size = 50_000  # Large enough to bury transition overhead
    nb_start = time.perf_counter()
    while time.perf_counter() - nb_start < duration:
        run_numba_batch(
            bytecode,
            batch_size,
            flat_ctx,
            global_ctx,
            p_hand,
            p_deck,
            p_stage,
            p_stage_energy_vec,
            p_stage_energy_count,
            p_continuous_effects_vec,
            p_tapped_members,
            p_live_revealed,
            opp_tapped_members,
        )
        total_iters += batch_size
    nb_end = time.perf_counter()
    nb_dur = nb_end - nb_start
    nb_ops_sec = total_iters / nb_dur
    print(f"Numba: {total_iters:,} ops in {nb_dur:.2f}s | Speed: {nb_ops_sec:,.0f} ops/sec")

    # --- PYTHON BENCHMARK ---
    print(f"\n--- Python Benchmark (Running for {duration} seconds) ---")
    gs = GameState()
    # Reset deck for fair comparison (GameState normally handles lists)
    gs.players[0].main_deck = list(range(50))
    gs.players[0].hand = []

    py_iters = 0
    py_start = time.perf_counter()
    while time.perf_counter() - py_start < duration:
        # Reset simple counters to prevent deckout crashes if any
        # though _resolve_effect_opcode is usually robust
        gs.players[0].main_deck = list(range(50))
        gs.players[0].hand = []
        gs._resolve_effect_opcode(Opcode.DRAW, [2, 0, 0])
        py_iters += 1
    py_end = time.perf_counter()
    py_dur = py_end - py_start
    py_ops_sec = py_iters / py_dur
    print(f"Python: {py_iters:,} ops in {py_dur:.2f}s | Speed: {py_ops_sec:,.0f} ops/sec")

    print("\n=" + "=" * 30)
    print(f"Speedup Factor: {nb_ops_sec / py_ops_sec:.2f}x")
    print("=" + "=" * 30)


if __name__ == "__main__":
    benchmark_10s()
