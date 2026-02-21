import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def benchmark_real_logic():
    print("============================================================")
    print(" LovecaSim - BENCHMARK: REAL COMPILED LOGIC (Verified Pool) ")
    print("============================================================")

    # Configuration
    BATCH_SIZE = 4096
    NUM_STEPS = 1000

    print(f" [Init] Creating Environment (Batch={BATCH_SIZE})...")
    vec_env = VectorGameState(BATCH_SIZE)
    vec_env.reset()

    # Verify Map Loaded
    compiled_count = np.sum(vec_env.bytecode_index > 0)
    print(f" [Check] Engine loaded {compiled_count} compiled ability pointers.")
    if compiled_count == 0:
        print(" [ERROR] No bytecodes loaded! Run ai/compile_numba_db.py first.")
        return

    # Generate Random Actions
    # We want to pick actions that correspond to valid compiled cards to test logic speed.
    # Find valid card IDs
    valid_card_ids = np.unique(np.where(vec_env.bytecode_index > 0)[0])
    print(f" [Check] {len(valid_card_ids)} unique cards have compiled logic.")

    # Create a batch of actions where we randomly select from valid cards
    print(" [Init] Generating random action batch (targeting valid cards)...")
    actions = np.zeros(BATCH_SIZE, dtype=np.int32)

    # Fill with random valid IDs
    random_indices = np.random.randint(0, len(valid_card_ids), size=BATCH_SIZE)
    actions[:] = valid_card_ids[random_indices]

    # Warmup
    print(" [Warmup] JIT compiling real logic path...")
    vec_env.step(actions)
    print(" [Warmup] Complete.")

    # Run
    print(f" [Run] Executing {NUM_STEPS} steps...")
    start_time = time.perf_counter()

    for _ in range(NUM_STEPS):
        vec_env.step(actions)

    duration = time.perf_counter() - start_time
    total_ops = NUM_STEPS * BATCH_SIZE
    sps = total_ops / duration

    print("============================================================")
    print(f" Total Operations: {total_ops:,.0f}")
    print(f" Time Taken:       {duration:.4f}s")
    print(f" Throughput:       {sps:,.0f} Steps/Sec")
    print("============================================================")

    # Check if scores changed (proof of work)
    active_scores = np.sum(vec_env.batch_scores > 0)
    print(f" Verified: {active_scores} environments have non-zero score.")


if __name__ == "__main__":
    benchmark_real_logic()
