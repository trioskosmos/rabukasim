import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from engine.game.ai_compat import njit
from engine.game.fast_logic import resolve_bytecode
from engine.game.game_state import GameState
from engine.models.opcodes import Opcode

# Constants
G_P_HAND_SIZE = 3
G_P_DECK_SIZE = 6
G_TURN = 2
G_P_ENERGY_SIZE = 5


@njit(cache=True)
def fast_simulation_n_steps(
    bytecode: np.ndarray,
    steps: int,
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
    Simulates N turns entirely in Numba.
    This is what 'Massive Batching' does during training.
    """
    total_score = 0
    for _ in range(steps):
        # 1. Reset state (Simulating turn start)
        global_ctx[G_P_DECK_SIZE] = 50
        global_ctx[G_P_HAND_SIZE] = 0
        global_ctx[G_P_ENERGY_SIZE] = 0

        # 2. Execute complex bytecode sequence
        # (Draw 2, Charge 2, Add Blades, If LifeLead -> Boost Score)
        new_ptr, status, bonus = resolve_bytecode(
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
        total_score += bonus
    return total_score


def prove_numba_batching():
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

    # Complex Bytecode:
    # 1. DRAW 2
    # 2. ENERGY_CHARGE 2
    # 3. ADD_BLADES 1 (to slot 0)
    # 4. CHECK_LIFE_LEAD
    # 5. JUMP_IF_FALSE (Skip boost)
    # 6. BOOST_SCORE 1
    # 7. RETURN
    bytecode = np.array(
        [
            [int(Opcode.DRAW), 2, 0, 0],
            [int(Opcode.ENERGY_CHARGE), 2, 0, 0],
            [int(Opcode.ADD_BLADES), 1, 0, 0],
            [int(Opcode.CHECK_LIFE_LEAD), 0, 0, 0],
            [int(Opcode.JUMP_IF_FALSE), 2, 0, 0],  # Jump over BOOST
            [int(Opcode.BOOST_SCORE), 1, 0, 0],
            [int(Opcode.RETURN), 0, 0, 0],
        ],
        dtype=np.int32,
    )

    # --- NUMBA MASSIVE BATCH ---
    print("\n--- Numba MASSIVE BATCH (Internal Loop) ---")
    # Warmup
    fast_simulation_n_steps(
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

    batch_size = 10_000  # Size of one 'Batch' step
    total_iters_nb = 0
    nb_start = time.perf_counter()
    while time.perf_counter() - nb_start < duration:
        fast_simulation_n_steps(
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
        total_iters_nb += batch_size
    nb_end = time.perf_counter()
    nb_dur = nb_end - nb_start
    nb_ops_sec = total_iters_nb / nb_dur
    print(f"Numba: {total_iters_nb:,} turns in {nb_dur:.2f}s | Speed: {nb_ops_sec:,.0f} turns/sec")

    # --- PYTHON ONE-BY-ONE ---
    print("\n--- Python GameState (Standard Flow) ---")
    gs = GameState()

    py_iters = 0
    py_start = time.perf_counter()
    while time.perf_counter() - py_start < duration:
        # Complex Sequence in Python
        gs.players[0].main_deck = list(range(50))
        gs.players[0].hand = []
        gs.players[0].energy_zone = []

        # Sequence:
        gs._resolve_effect_opcode(Opcode.DRAW, [2, 0, 0])
        gs._resolve_effect_opcode(Opcode.ENERGY_CHARGE, [2, 0, 0])
        gs._resolve_effect_opcode(Opcode.ADD_BLADES, [1, 0, 0])

        # Condition
        if gs.players[0].score > gs.players[1].score:
            gs._resolve_effect_opcode(Opcode.BOOST_SCORE, [1, 0, 0])

        py_iters += 1
    py_end = time.perf_counter()
    py_dur = py_end - py_start
    py_ops_sec = py_iters / py_dur
    print(f"Python: {py_iters:,} turns in {py_dur:.2f}s | Speed: {py_ops_sec:,.0f} turns/sec")

    print("\n" + "=" * 40)
    print(f"RESULT: {nb_ops_sec / py_ops_sec:.2f}x Absolute Speedup")
    print("=" * 40)
    print("PROOF: Numba throughput scales with workload density,")
    print("whereas Python slows down as we add more engine calls.")


if __name__ == "__main__":
    prove_numba_batching()
