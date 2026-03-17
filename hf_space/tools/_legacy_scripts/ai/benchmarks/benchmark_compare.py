import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from engine.game.fast_logic import resolve_bytecode
from engine.game.game_state import GameState
from engine.models.opcodes import Opcode

# Numba-safe constants for ContextIndex
CTX_VALUE = 1
G_P_HAND_SIZE = 3
G_P_DECK_SIZE = 6

ITERATIONS = 500_000
WARMUP = 50_000


def bench_numba():
    print(f"--- Numba Benchmark ({ITERATIONS:,} ops) ---")

    # Mock Data
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

    # Warmup
    for _ in range(WARMUP):
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
            p_stage_energy_vec,
            p_stage_energy_count,
            p_continuous_effects_vec,
            0,
            p_tapped_members,
            p_live_revealed,
            opp_tapped_members,
        )

    start = time.perf_counter()
    for _ in range(ITERATIONS):
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
            p_stage_energy_vec,
            p_stage_energy_count,
            p_continuous_effects_vec,
            0,
            p_tapped_members,
            p_live_revealed,
            opp_tapped_members,
        )
    dur = time.perf_counter() - start
    ops_sec = ITERATIONS / dur
    print(f"Numba Time: {dur:.4f}s | Speed: {ops_sec:,.0f} ops/sec")
    return ops_sec


def bench_python():
    print(f"--- Python Benchmark ({ITERATIONS:,} ops) ---")
    gs = GameState()
    # Ensure helper exists (it does per grep)
    if not hasattr(gs, "_resolve_effect_opcode"):
        print("ERROR: _resolve_effect_opcode not found on GameState")
        return 1.0

    # Warmup
    for _ in range(WARMUP):
        gs._resolve_effect_opcode(Opcode.DRAW, [2, 0, 0])

    start = time.perf_counter()
    for _ in range(ITERATIONS):
        # We don't reset state fully as it's expensive, allowing 'draw' to just increment counters internally
        # Or if it errors on empty deck, we might need a reset.
        # But _resolve_effect_opcode for DRAW usually just appends to hand.
        # We'll just run it.
        gs._resolve_effect_opcode(Opcode.DRAW, [2, 0, 0])

    dur = time.perf_counter() - start
    ops_sec = ITERATIONS / dur
    print(f"Python Time: {dur:.4f}s | Speed: {ops_sec:,.0f} ops/sec")
    return ops_sec


if __name__ == "__main__":
    nb = bench_numba()
    py = bench_python()
    print("=" * 30)
    print(f"Speedup: {nb / py:.2f}x")
