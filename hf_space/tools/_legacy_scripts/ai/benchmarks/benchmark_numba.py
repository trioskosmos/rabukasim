import os
import sys
import time

import numpy as np

# Append root to path
sys.path.append(os.getcwd())

from engine.game.fast_logic import G_P_DECK_SIZE, G_P_HAND_SIZE, resolve_bytecode
from engine.game.game_state import GameState
from engine.models.ability import Effect, EffectType, TargetType
from engine.models.opcodes import Opcode

# --- CONFIG ---
ITERATIONS = 500_000
WARMUP = 10_000


def benchmark_python():
    print(f"--- Python GameState Benchmark ({ITERATIONS} ops) ---")

    # Setup
    gs = GameState()
    p = gs.players[0]
    p.deck = list(range(1000, 1000 + 50))  # 50 cards
    p.hand = []

    # Operation: Draw 2 Cards
    # In Python, this involves creating Effect objects, calling resolve_effect, etc.
    # We will simulate the "Resolve Effect" loop which is the bottleneck.
    eff = Effect(EffectType.DRAW, 2, TargetType.PLAYER)

    start_time = time.perf_counter()

    for _ in range(ITERATIONS):
        # Reset state slightly to prevent empty deck
        p.deck = list(range(50))
        p.hand = []

        # Execute
        # Directly call the internal method if possible or standard flow
        # Use simpler simulation of "drawing" if exact method is private
        # But to be fair, we want to measure the OVERHEAD of objects.
        # So we do:
        gs._resolve_effect_opcode(Opcode.DRAW, [2, 0, 0])

    end_time = time.perf_counter()
    duration = end_time - start_time
    ops_sec = ITERATIONS / duration
    print(f"Time: {duration:.4f}s | Speed: {ops_sec:,.0f} ops/sec")
    return ops_sec


def benchmark_numba():
    print(f"--- Numba FastLogic Benchmark ({ITERATIONS} ops) ---")

    # Setup Data Structures
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

    # Bytecode: DRAW 2
    # [Opcode.DRAW, 2, 0, 0]
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

    # Run
    start_time = time.perf_counter()

    for _ in range(ITERATIONS):
        # Reset logic (fast array write)
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

    end_time = time.perf_counter()
    duration = end_time - start_time
    ops_sec = ITERATIONS / duration
    print(f"Time: {duration:.4f}s | Speed: {ops_sec:,.0f} ops/sec")

    # VERIFICATION
    # Check correctness
    # Hand should vary? No we reset it.
    # Logic: Start 0 hand, Draw 2 -> End 2 Hand.
    # Check last iteration state
    final_hand_size = global_ctx[G_P_HAND_SIZE]
    final_deck_size = global_ctx[G_P_DECK_SIZE]

    print(f"Verification: HandSize={final_hand_size} (Exp: 2), DeckSize={final_deck_size} (Exp: 48)")
    if final_hand_size == 2 and final_deck_size == 48:
        print("[PASS] Numba logic correctness verified.")
    else:
        print("[FAIL] Numba logic produced incorrect state.")

    return ops_sec


if __name__ == "__main__":
    py_speed = benchmark_python()
    print("-" * 30)
    nb_speed = benchmark_numba()

    print("=" * 30)
    print(f"Speedup Factor: {nb_speed / py_speed:.2f}x")
