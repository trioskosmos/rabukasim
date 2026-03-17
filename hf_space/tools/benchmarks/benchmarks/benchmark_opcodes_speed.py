import os
import sys
import time

import numpy as np

# Add local directory to path
sys.path.append(os.getcwd())

from engine.game.game_state import GameState
from engine.models.ability import Effect, EffectType, ResolvingEffect, TargetType
from engine.models.context_indices import ContextIndex
from engine.models.opcodes import Opcode


def benchmark_resolution(n_iterations=10000):
    gs = GameState()
    gs.verbose = False
    p = gs.active_player
    p.main_deck = [i for i in range(1000000)]  # Large deck to avoid refresh logic

    # 1. Benchmark Legacy Object-based resolution
    print(f"Benchmarking Legacy Object resolution ({n_iterations} iterations)...")
    effect = Effect(EffectType.ADD_BLADES, value=1, target=TargetType.MEMBER_SELF)
    effect.params["until"] = "TURN_END"
    resolving_effect = ResolvingEffect(effect, -1, 1, 1)

    start_time = time.time()
    for _ in range(n_iterations):
        gs.pending_effects = [resolving_effect]
        gs._resolve_pending_effect(0)
    end_time = time.time()
    legacy_time = end_time - start_time
    legacy_ops = n_iterations / legacy_time
    print(f"Legacy: {legacy_ops:.2f} ops/sec")

    # 2. Benchmark Opcode + Legacy Context
    print(f"Benchmarking Opcode + Dict Context ({n_iterations} iterations)...")
    context_dict = {"value": 1}
    start_time = time.time()
    for _ in range(n_iterations):
        gs.pending_effects = [int(Opcode.ADD_BLADES)]
        gs._resolve_pending_effect(0, context=context_dict)
    end_time = time.time()
    opcode_dict_time = end_time - start_time
    opcode_dict_ops = n_iterations / opcode_dict_time
    print(f"Opcode+Dict: {opcode_dict_ops:.2f} ops/sec")

    # 3. Benchmark Opcode + Flat NumPy Context
    print(f"Benchmarking Opcode + Flat Context ({n_iterations} iterations)...")
    flat_ctx = np.zeros(64, dtype=np.int32)
    flat_ctx[ContextIndex.VALUE] = 1
    flat_ctx[ContextIndex.TARGET_ZONE_IDX] = 0  # Slot 0
    start_time = time.time()
    for _ in range(n_iterations):
        gs.pending_effects = [int(Opcode.ADD_BLADES)]
        gs._resolve_pending_effect(0, context=flat_ctx)
    end_time = time.time()
    opcode_flat_time = end_time - start_time
    opcode_flat_ops = n_iterations / opcode_flat_time
    print(f"Opcode+Flat: {opcode_flat_ops:.2f} ops/sec")

    print("-" * 30)
    print(f"Resolution Speedup (Opcode+Flat vs Legacy): {opcode_flat_ops / legacy_ops:.2f}x")


def benchmark_cloning(n_iterations=10000):
    gs = GameState()
    gs.verbose = False

    # Populate some state
    for i in range(10):
        gs._push_pending_choice(("TARGET_MEMBER", {"player_id": 0, "source_card_id": i}))

    # 1. Benchmark Legacy Cloning
    gs.fast_mode = False
    print(f"Benchmarking Cloning - Legacy ({n_iterations} iterations)...")
    start_time = time.time()
    for _ in range(n_iterations):
        _ = gs.copy()
    end_time = time.time()
    legacy_time = end_time - start_time
    legacy_clones = n_iterations / legacy_time
    print(f"Legacy: {legacy_clones:.2f} clones/sec")

    # 2. Benchmark Fast Cloning
    gs.fast_mode = True
    print(f"Benchmarking Cloning - Fast ({n_iterations} iterations)...")
    start_time = time.time()
    for _ in range(n_iterations):
        _ = gs.copy()
    end_time = time.time()
    fast_time = end_time - start_time
    fast_clones = n_iterations / fast_time
    print(f"Fast: {fast_clones:.2f} clones/sec")

    print("-" * 30)
    print(f"Cloning Speedup: {fast_clones / legacy_clones:.2f}x")


if __name__ == "__main__":
    benchmark_resolution()
    print("\n")
    benchmark_cloning()
