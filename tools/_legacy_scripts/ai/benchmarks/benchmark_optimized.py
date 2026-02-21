import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from engine.game.ai_compat import njit
from engine.game.fast_logic import resolve_bytecode

# Use the same constants as fast_logic.py for consistency
OP_DRAW = 10
OP_ENERGY_CHARGE = 23
OP_ADD_BLADES = 11
OP_CHECK_LIFE_LEAD = 207
OP_JUMP_IF_FALSE = 3
OP_BOOST_SCORE = 16
OP_RETURN = 1

G_P_HAND_SIZE = 3
G_P_DECK_SIZE = 6
G_P_ENERGY_SIZE = 5


@njit(cache=True)
def run_production_bench(
    iters,
    bytecode,
    flat_ctx,
    global_ctx,
    p_hand,
    p_deck,
    p_stage,
    p_energy_vec,
    p_energy_count,
    p_cont_vec,
    p_tapped,
    p_live,
    opp_tapped,
):
    for _ in range(iters):
        # Reset simple state
        global_ctx[G_P_DECK_SIZE] = 50
        global_ctx[G_P_HAND_SIZE] = 0
        global_ctx[G_P_ENERGY_SIZE] = 0

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


def benchmark_optimized():
    iters = 1_000_000

    # Complex sequence
    bytecode = np.array(
        [
            [OP_DRAW, 2, 0, 0],
            [OP_ENERGY_CHARGE, 2, 0, 0],
            [OP_ADD_BLADES, 1, 0, 0],
            [OP_CHECK_LIFE_LEAD, 0, 0, 0],
            [OP_JUMP_IF_FALSE, 2, 0, 0],
            [OP_BOOST_SCORE, 1, 0, 0],
            [OP_RETURN, 0, 0, 0],
        ],
        dtype=np.int32,
    )

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

    # Warmup
    print("Compiling Production VM...")
    run_production_bench(
        100,
        bytecode,
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

    print(f"Running Optimized VM Benchmark ({iters:,} iterations)...")
    start = time.perf_counter()
    run_production_bench(
        iters,
        bytecode,
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

    ops_sec = iters / dur
    print(f"Optimized VM Result: {dur:.4f}s | Speed: {ops_sec:,.0f} turns/sec")

    # Python comparison (hardcoded from prev batch as baseline)
    py_speed = 777_181
    print(f"Vs Python Baseline (777k): {ops_sec / py_speed:.2f}x Speedup")


if __name__ == "__main__":
    benchmark_optimized()
