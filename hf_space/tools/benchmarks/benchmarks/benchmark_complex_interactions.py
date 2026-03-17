import os
import sys
import time

import numpy as np

# Add local directory to path
sys.path.append(os.getcwd())

from engine.game.fast_logic import resolve_bytecode
from engine.game.game_state import GameState
from engine.models.ability import Ability, Condition, ConditionType, Effect, EffectType, TriggerType


def benchmark_complex_ability(n_iterations=10000):
    gs = GameState()
    gs.fast_mode = True
    p = gs.active_player
    opp = gs.players[1 - gs.current_player]

    # Define a complex ability:
    # Conditions: TURN_1
    # Effects: BOOST_SCORE(10), ADD_HEARTS(2, RED)

    # 1. Compilation
    ability = Ability(
        raw_text="[登場時] ターン1: スコアを+10し、レッドのハートを2枚増やす。",
        trigger=TriggerType.ON_PLAY,
        conditions=[Condition(ConditionType.TURN_1)],
        effects=[
            Effect(EffectType.BOOST_SCORE, value=10),
            Effect(EffectType.ADD_HEARTS, value=2, params={"color": 1}),  # Red
        ],
    )
    bytecode_list = ability.compile()
    bytecode = np.array(bytecode_list, dtype=np.int32).reshape(-1, 4)

    print(f"Bytecode shape: {bytecode.shape}")

    # 2. Python Baseline
    print(f"Benchmarking Complex Interaction (Python Objects) ({n_iterations} iterations)...")
    start_time = time.time()
    for _ in range(n_iterations):
        ability.resolved_count = 0
        for eff in ability.effects:
            gs.pending_effects = [eff]
            # Use skip_jit=True or just ensure we don't return early to measure object overhead
            gs._resolve_pending_effect(0)
    end_time = time.time()
    python_time = end_time - start_time
    print(f"Python (Objects): {n_iterations / python_time:.2f} abilities/sec")

    # 3. JIT Accelerated (Unified VM)
    print(f"Benchmarking Complex Interaction (JIT VM) ({n_iterations} iterations)...")

    flat_ctx = np.zeros(64, dtype=np.int32)
    g_ctx = np.zeros(128, dtype=np.int32)
    g_ctx[2] = 1  # Turn 1

    dummy_hand = np.zeros(1, dtype=np.int32)
    dummy_deck = np.zeros(1, dtype=np.int32)

    # Warmup
    _, _, _ = resolve_bytecode(
        bytecode,
        flat_ctx,
        g_ctx,
        p.player_id,
        dummy_hand,
        dummy_deck,
        p.stage,
        p.stage_energy_vec,
        p.stage_energy_count,
        p.continuous_effects_vec,
        p.continuous_effects_ptr,
        p.tapped_members,
        gs._jit_dummy_array,
        opp.tapped_members,
    )

    start_time = time.time()
    for _ in range(n_iterations):
        _, _, _ = resolve_bytecode(
            bytecode,
            flat_ctx,
            g_ctx,
            p.player_id,
            dummy_hand,
            dummy_deck,
            p.stage,
            p.stage_energy_vec,
            p.stage_energy_count,
            p.continuous_effects_vec,
            p.continuous_effects_ptr,
            p.tapped_members,
            gs._jit_dummy_array,
            opp.tapped_members,
        )
    end_time = time.time()
    jit_time = end_time - start_time
    print(f"JIT (Unified VM): {n_iterations / jit_time:.2f} abilities/sec")

    print("-" * 30)
    speedup = (n_iterations / jit_time) / (n_iterations / python_time)
    print(f"Complex Interaction Speedup: {speedup:.2f}x")


if __name__ == "__main__":
    benchmark_complex_ability()
