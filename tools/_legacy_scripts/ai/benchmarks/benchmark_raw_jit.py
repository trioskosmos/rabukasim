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
ITERATIONS = 1_000_000


@njit(cache=True)
def draw_raw(global_ctx, val):
    if global_ctx[G_P_DECK_SIZE] >= val:
        global_ctx[G_P_DECK_SIZE] -= val
        global_ctx[G_P_HAND_SIZE] += val
    else:
        v = global_ctx[G_P_DECK_SIZE]
        global_ctx[G_P_DECK_SIZE] = 0
        global_ctx[G_P_HAND_SIZE] += v
    return 0


@njit(cache=True)
def run_raw_batch(iters, global_ctx, val):
    for _ in range(iters):
        global_ctx[G_P_DECK_SIZE] = 50
        global_ctx[G_P_HAND_SIZE] = 0
        draw_raw(global_ctx, val)
    return 0


@njit(cache=True)
def run_vm_batch(
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


def micro_benchmark():
    global_ctx = np.zeros(128, dtype=np.int32)
    bytecode = np.array([[int(Opcode.DRAW), 2, 0, 0]], dtype=np.int32)
    flat_ctx = np.zeros(64, dtype=np.int32)
    p_stage = np.full(3, -1, dtype=np.int32)
    p_deck = np.zeros(50, dtype=np.int32)
    p_hand = np.zeros(50, dtype=np.int32)
    p_energy_vec = np.zeros((3, 32), dtype=np.int32)
    p_energy_count = np.zeros(3, dtype=np.int32)
    p_cont_vec = np.zeros((32, 10), dtype=np.int32)
    p_tapped = np.zeros(3, dtype=np.int32)
    p_live = np.zeros(3, dtype=np.int32)
    opp_tapped = np.zeros(3, dtype=np.int32)

    # Warmup
    draw_raw(global_ctx, 2)
    run_raw_batch(100, global_ctx, 2)
    run_vm_batch(
        100,
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
    )

    print(f"Running micro-benchmark ({ITERATIONS:,} iterations)...")

    # Raw
    start = time.perf_counter()
    run_raw_batch(ITERATIONS, global_ctx, 2)
    raw_dur = time.perf_counter() - start
    print(f"Raw JIT Draw: {raw_dur:.6f}s | {ITERATIONS / raw_dur:,.0f} ops/sec")

    # VM
    start = time.perf_counter()
    run_vm_batch(
        ITERATIONS,
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
    )
    vm_dur = time.perf_counter() - start
    print(f"VM JIT Draw:  {vm_dur:.6f}s | {ITERATIONS / vm_dur:,.0f} ops/sec")

    print(f"Ratio (VM / Raw): {vm_dur / raw_dur:.2f}x Overhead")


if __name__ == "__main__":
    micro_benchmark()
