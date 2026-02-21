import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from engine.game.ai_compat import njit
from engine.game.fast_logic import resolve_bytecode
from engine.models.opcodes import Opcode

# Constants
G_P_HAND_SIZE = 3
G_P_DECK_SIZE = 6
ITERATIONS = 5_000_000


@njit(cache=True)
def run_internal_loop(
    bytecode: np.ndarray,
    iters: int,
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
    """
    Simulates a loop entirely inside Numba VM.
    This represents 'Massive Batch' performance where we process
    thousands of games/steps without returning to Python.
    """
    for _ in range(iters):
        # Reset simple state for stability
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
    return 1


def bench_internal():
    print(f"--- Numba Internal Loop Benchmark ({ITERATIONS:,} ops) ---")

    # Data
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

    bytecode = np.array([[int(Opcode.DRAW), 2, 0, 0]], dtype=np.int32)

    # Warmup (compilation)
    print("Compiling...")
    run_internal_loop(
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
    print("Compiled.")

    start = time.perf_counter()
    run_internal_loop(
        bytecode,
        ITERATIONS,
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
    dur = time.perf_counter() - start
    ops_sec = ITERATIONS / dur
    print(f"Numba Internal Time: {dur:.4f}s | Speed: {ops_sec:,.0f} ops/sec")

    # Reference Python speed (from prev run)
    py_speed = 2_250_000
    print(f"vs Python Ref (~2.25M ops/sec): {ops_sec / py_speed:.2f}x Speedup")


if __name__ == "__main__":
    bench_internal()
