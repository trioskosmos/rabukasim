import os
import sys
import time

import numpy as np

# Add local directory to path
sys.path.append(os.getcwd())

from engine.game.fast_logic import resolve_bytecode
from engine.game.game_state import GameState
from engine.models.ability import Effect, EffectType, ResolvingEffect

# Opcodes for manual bytecode construction
O_DRAW = 10
O_SELECT_MODE = 30
O_SEARCH_DECK = 22
O_TRIGGER_REMOTE = 47
O_RETURN = 1
O_JUMP = 2


def setup_vm_state():
    flat_ctx = np.zeros(64, dtype=np.int32)
    global_ctx = np.zeros(128, dtype=np.int32)
    global_ctx[6] = 60  # Deck size

    p_hand = np.zeros(60, dtype=np.int32)
    p_deck = np.random.randint(1, 100, size=60).astype(np.int32)
    p_stage = np.full(3, -1, dtype=np.int32)
    p_stage[0] = 101  # Dummy member

    p_energy_vec = np.zeros((3, 32), dtype=np.int32)
    p_energy_count = np.zeros(3, dtype=np.int32)
    p_cont_vec = np.zeros((32, 10), dtype=np.int32)
    p_tapped = np.zeros(3, dtype=np.int32)
    p_live = np.zeros(50, dtype=np.int32)
    opp_tapped = np.zeros(3, dtype=np.int32)

    # Bytecode lookup dummies
    b_map = np.zeros((10, 128, 4), dtype=np.int32)
    b_idx = np.full((1000, 1), -1, dtype=np.int32)

    # Target dummy for Trigger Remote
    target_card_id = 101
    b_map[1, 0] = [O_DRAW, 1, 0, 0]
    b_map[1, 1] = [O_RETURN, 0, 0, 0]
    b_idx[target_card_id, 0] = 1

    return (
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
        b_map,
        b_idx,
    )


def benchmark_vm_opcodes(n_iterations=500000):
    state = setup_vm_state()
    (
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
        b_map,
        b_idx,
    ) = state

    out_cptr = np.zeros(1, dtype=np.int32)
    out_bonus = np.zeros(1, dtype=np.int32)

    # 1. Baseline: Simple Draw
    bc_draw = np.array([[O_DRAW, 1, 0, 0], [O_RETURN, 0, 0, 0]], dtype=np.int32)

    # Warmup
    resolve_bytecode(
        bc_draw,
        flat_ctx,
        global_ctx,
        0,
        p_hand,
        p_deck,
        p_stage,
        p_energy_vec,
        p_energy_count,
        p_cont_vec,
        out_cptr,
        p_tapped,
        p_live,
        opp_tapped,
        b_map,
        b_idx,
        out_bonus,
    )

    print(f"Benchmarking VM Opcodes ({n_iterations} iterations)...")

    start = time.time()
    for _ in range(n_iterations):
        out_cptr[0] = 0
        resolve_bytecode(
            bc_draw,
            flat_ctx,
            global_ctx,
            0,
            p_hand,
            p_deck,
            p_stage,
            p_energy_vec,
            p_energy_count,
            p_cont_vec,
            out_cptr,
            p_tapped,
            p_live,
            opp_tapped,
            b_map,
            b_idx,
            out_bonus,
        )
    end = time.time()
    draw_time = end - start
    print(f"O_DRAW: {n_iterations / draw_time:.2f} ops/sec")

    # 2. SELECT_MODE (Branching)
    bc_select = np.array(
        [
            [O_SELECT_MODE, 2, 0, 0],
            [O_JUMP, 2, 0, 0],
            [O_JUMP, 4, 0, 0],
            [O_DRAW, 1, 0, 0],
            [O_RETURN, 0, 0, 0],
            [O_DRAW, 2, 0, 0],
            [O_RETURN, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    flat_ctx[15] = 1  # CTX_CHOICE_INDEX = 15. Choice = 1 (Draw 2)

    start = time.time()
    for _ in range(n_iterations):
        out_cptr[0] = 0
        resolve_bytecode(
            bc_select,
            flat_ctx,
            global_ctx,
            0,
            p_hand,
            p_deck,
            p_stage,
            p_energy_vec,
            p_energy_count,
            p_cont_vec,
            out_cptr,
            p_tapped,
            p_live,
            opp_tapped,
            b_map,
            b_idx,
            out_bonus,
        )
    end = time.time()
    select_time = end - start
    print(f"O_SELECT_MODE: {n_iterations / select_time:.2f} ops/sec")

    # 3. TRIGGER_REMOTE (Recursion)
    bc_remote = np.array(
        [
            [O_TRIGGER_REMOTE, 0, 0, 0],  # Trigger Slot 0
            [O_RETURN, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    start = time.time()
    for _ in range(n_iterations):
        out_cptr[0] = 0
        resolve_bytecode(
            bc_remote,
            flat_ctx,
            global_ctx,
            0,
            p_hand,
            p_deck,
            p_stage,
            p_energy_vec,
            p_energy_count,
            p_cont_vec,
            out_cptr,
            p_tapped,
            p_live,
            opp_tapped,
            b_map,
            b_idx,
            out_bonus,
        )
    end = time.time()
    remote_time = end - start
    print(f"O_TRIGGER_REMOTE: {n_iterations / remote_time:.2f} ops/sec")

    # 4. SEARCH_DECK (Scan)
    bc_search = np.array(
        [
            [O_SEARCH_DECK, 0, 0, -1],  # Search any
            [O_RETURN, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    start = time.time()
    for _ in range(n_iterations // 50):  # Search is slower, fewer iters
        out_cptr[0] = 0
        global_ctx[6] = 60  # Reset deck size
        resolve_bytecode(
            bc_search,
            flat_ctx,
            global_ctx,
            0,
            p_hand,
            p_deck,
            p_stage,
            p_energy_vec,
            p_energy_count,
            p_cont_vec,
            out_cptr,
            p_tapped,
            p_live,
            opp_tapped,
            b_map,
            b_idx,
            out_bonus,
        )
    end = time.time()
    search_time = end - start
    print(f"O_SEARCH_DECK: {(n_iterations // 50) / search_time:.2f} ops/sec")


def benchmark_python_comparison(n_iterations=5000):
    gs = GameState()
    gs.verbose = False

    # Mocking a basic effect resolution path
    effect = Effect(EffectType.DRAW, value=1)
    resolving_effect = ResolvingEffect(effect, -1, 1, 1)

    print(f"\nBenchmarking Python GameState ({n_iterations} iterations)...")
    start = time.time()
    for _ in range(n_iterations):
        gs.pending_effects = [resolving_effect]
        gs._resolve_pending_effect(0)
    end = time.time()
    py_ops = n_iterations / (end - start)
    print(f"Python GameState Resolve: {py_ops:.2f} ops/sec")

    # Comparison
    state = setup_vm_state()
    (
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
        b_map,
        b_idx,
    ) = state
    out_cptr = np.zeros(1, dtype=np.int32)
    out_bonus = np.zeros(1, dtype=np.int32)
    bc_draw = np.array([[O_DRAW, 1, 0, 0], [O_RETURN, 0, 0, 0]], dtype=np.int32)

    start = time.time()
    for _ in range(100000):
        out_cptr[0] = 0
        resolve_bytecode(
            bc_draw,
            flat_ctx,
            global_ctx,
            0,
            p_hand,
            p_deck,
            p_stage,
            p_energy_vec,
            p_energy_count,
            p_cont_vec,
            out_cptr,
            p_tapped,
            p_live,
            opp_tapped,
            b_map,
            b_idx,
            out_bonus,
        )
    end = time.time()
    vm_ops = 100000 / (end - start)

    print(f"\nSpeedup (VM Draw vs Python Resolve): {vm_ops / py_ops:.2f}x")


if __name__ == "__main__":
    benchmark_vm_opcodes()
    benchmark_python_comparison()
