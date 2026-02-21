import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())

from ai.fast_mcts import run_mcts_search


def benchmark_jit_mcts():
    print("Benchmarking JIT MCTS...")

    # Setup dummy data for JIT function
    # These mimic the flattened arrays in GameState
    root_stage = np.full(3, -1, dtype=np.int32)
    root_energy_vec = np.zeros((3, 32), dtype=np.int32)
    root_energy_count = np.zeros(3, dtype=np.int32)
    root_continuous_vec = np.zeros((32, 10), dtype=np.int32)
    root_continuous_ptr = 0
    root_tapped = np.zeros(3, dtype=np.bool)  # Warning: check if bool/int mismatch
    # fast_logic uses bool/int? Let's use int32 for safety with Numba if bool issues arise,
    # but verify fast_logic signature.
    # fast_logic signature says: p_tapped_members: np.ndarray # (3,) bool/int
    root_tapped = root_tapped.astype(np.int32)

    root_live_revealed = np.zeros(50, dtype=np.int32)

    # Tree pools
    MAX_NODES = 100000
    MAX_ACTIONS = 64
    NODE_SIZE = 6  # [visit, value, prior, parent, expanded, state_idx]

    node_pool = np.zeros((MAX_NODES, NODE_SIZE), dtype=np.float32)
    # Warning: node_pool stores mix of float/int.
    # In fast_mcts we treat it as float32 array, casting indices to int.

    children_pool = np.full((MAX_NODES, MAX_ACTIONS), -1, dtype=np.int32)
    policy_pool = np.zeros((MAX_NODES, MAX_ACTIONS), dtype=np.float32)

    # State pools
    pool_stage = np.zeros((MAX_NODES, 3), dtype=np.int32)
    pool_energy_vec = np.zeros((MAX_NODES, 3, 32), dtype=np.int32)
    pool_energy_count = np.zeros((MAX_NODES, 3), dtype=np.int32)
    pool_continuous_vec = np.zeros((MAX_NODES, 32, 10), dtype=np.int32)
    pool_tapped = np.zeros((MAX_NODES, 3), dtype=np.int32)
    pool_live_revealed = np.zeros((MAX_NODES, 50), dtype=np.int32)

    # Warmup
    print("Warming up JIT...")
    run_mcts_search(
        root_stage,
        root_energy_vec,
        root_energy_count,
        root_continuous_vec,
        root_continuous_ptr,
        root_tapped,
        root_live_revealed,
        10,
        1.4,  # 10 sims
        node_pool,
        children_pool,
        policy_pool,
        pool_stage,
        pool_energy_vec,
        pool_energy_count,
        pool_continuous_vec,
        pool_tapped,
        pool_live_revealed,
    )

    # Benchmark
    N_SEARCHES = 100
    SIMS_PER_SEARCH = 1000

    print(f"Running {N_SEARCHES} searches with {SIMS_PER_SEARCH} sims each...")
    start = time.time()
    for _ in range(N_SEARCHES):
        # Reset pool for each search (conceptually)
        # We just overwrite root (index 0) and children pointers
        # In real code we'd zero out used nodes or manage a pointer.
        # For bench, simple is fine.
        run_mcts_search(
            root_stage,
            root_energy_vec,
            root_energy_count,
            root_continuous_vec,
            root_continuous_ptr,
            root_tapped,
            root_live_revealed,
            SIMS_PER_SEARCH,
            1.4,
            node_pool,
            children_pool,
            policy_pool,
            pool_stage,
            pool_energy_vec,
            pool_energy_count,
            pool_continuous_vec,
            pool_tapped,
            pool_live_revealed,
        )
    end = time.time()

    total_sims = N_SEARCHES * SIMS_PER_SEARCH
    duration = end - start
    print(f"Total Sims: {total_sims}")
    print(f"Time: {duration:.4f}s")
    print(f"Throughput: {total_sims / duration:.2f} sims/sec")


if __name__ == "__main__":
    benchmark_jit_mcts()
