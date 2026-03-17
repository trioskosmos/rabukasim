import os
import sys
import time

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from engine.game.fast_logic import resolve_opcode
from engine.game.game_state import GameState
from engine.models.ability import Effect, EffectType, ResolvingEffect, TargetType
from engine.models.opcodes import Opcode


def benchmark_python_engine(iterations=1000):
    gs = GameState()
    gs.verbose = False
    p = gs.active_player

    # Simple effect: ADD_BLADES
    effect = Effect(EffectType.ADD_BLADES, value=1, target=TargetType.MEMBER_SELF)
    # Note: We use ResolvingEffect to match the actual path taken in _resolve_pending_effect
    resolving_effect = ResolvingEffect(effect, -1, 1, 1)

    start = time.time()
    for _ in range(iterations):
        gs.pending_effects = [resolving_effect]
        gs._resolve_pending_effect(0)
    end = time.time()

    elapsed = end - start
    print(f"Python Engine: {iterations / elapsed:.2f} effects/sec")


def benchmark_numba_engine(iterations=1000000):
    # Setup dummy arrays for Numba
    flat_ctx = np.zeros(64, dtype=np.int32)
    global_ctx = np.zeros(128, dtype=np.int32)
    flat_ctx[1] = 1  # Value
    flat_ctx[3] = 0  # TargetSlot (CTX_TARGET_SLOT)

    p_hand = np.zeros(60, dtype=np.int32)
    p_deck = np.zeros(60, dtype=np.int32)
    p_stage = np.zeros(3, dtype=np.int32)
    p_stage_energy_vec = np.zeros((3, 32), dtype=np.int32)
    p_stage_energy_count = np.zeros(3, dtype=np.int32)
    p_continuous_effects_vec = np.zeros((32, 10), dtype=np.int32)
    p_tapped_members = np.zeros(3, dtype=np.int32)
    p_live_revealed = np.zeros(8, dtype=np.int32)
    opp_tapped_members = np.zeros(3, dtype=np.int32)

    opcode = int(Opcode.ADD_BLADES)
    ptr = 0

    # Warmup
    resolve_opcode(
        opcode,
        flat_ctx,
        global_ctx,
        0,
        p_hand,
        p_deck,
        p_stage,
        p_stage_energy_vec,
        p_stage_energy_count,
        p_continuous_effects_vec,
        ptr,
        p_tapped_members,
        p_live_revealed,
        opp_tapped_members,
    )

    start = time.time()
    for i in range(iterations):
        # We simulate the loop
        _, _, _ = resolve_opcode(
            opcode,
            flat_ctx,
            global_ctx,
            0,
            p_hand,
            p_deck,
            p_stage,
            p_stage_energy_vec,
            p_stage_energy_count,
            p_continuous_effects_vec,
            ptr,
            p_tapped_members,
            p_live_revealed,
            opp_tapped_members,
        )
    end = time.time()

    elapsed = end - start
    print(f"Numba Engine (Logic Only): {iterations / elapsed:.2f} effects/sec")


if __name__ == "__main__":
    print("Comparing Python Engine (GameState) vs Numba Fast Logic...")
    try:
        benchmark_python_engine()
    except Exception as e:
        print(f"Python benchmark failed: {e}")

    try:
        benchmark_numba_engine()
    except Exception as e:
        print(f"Numba benchmark failed: {e}")
