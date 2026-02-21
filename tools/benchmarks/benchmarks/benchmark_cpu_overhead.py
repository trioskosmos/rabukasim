import time

import numpy as np


def benchmark_overhead():
    print("=== CPU Overhead Benchmark: Loop vs Vectorized ===")

    # Setup
    num_envs = 4096
    dones = np.zeros(num_envs, dtype=bool)

    # Case 1: Sparse Dones (Normal Step) - e.g. 1% done
    n_done = int(num_envs * 0.01)
    done_indices = np.random.choice(num_envs, n_done, replace=False)
    dones[done_indices] = True

    rewards = np.random.randn(num_envs).astype(np.float32)
    episode_returns = np.zeros(num_envs, dtype=np.float32)
    episode_lengths = np.zeros(num_envs, dtype=np.int32)

    print(f"Configuration: N={num_envs}, Dones={n_done} ({n_done / num_envs * 100:.1f}%)")

    # --- Method 1: Old Loop (Simulating previous implementation) ---
    start_time = time.time()

    infos_old = []
    # Simulate the loop in the old implementation
    # It accessed arrays element-wise and appended to list
    for i in range(num_envs):
        if dones[i]:
            infos_old.append({"episode": {"r": float(rewards[i]), "l": int(episode_lengths[i]) + 1}})
            episode_returns[i] = 0
            episode_lengths[i] = 0
        else:
            episode_returns[i] += rewards[i]
            episode_lengths[i] += 1
            infos_old.append({})

    end_time = time.time()
    old_duration = end_time - start_time
    print(f"Old Method Time: {old_duration:.6f}s")

    # Reset stats
    episode_returns = np.zeros(num_envs, dtype=np.float32)
    episode_lengths = np.zeros(num_envs, dtype=np.int32)

    # --- Method 2: New Vectorized (Simulating current implementation) ---
    start_time = time.time()

    # 1. Vectorized Updates
    episode_returns += rewards
    episode_lengths += 1

    # 2. Bulk Info Construction
    infos_new = [{} for _ in range(num_envs)]

    if np.any(dones):
        done_idxs = np.where(dones)[0]

        # Bulk fetch (simulate slicing)
        final_rs = rewards[done_idxs]
        final_ls = episode_lengths[done_idxs]

        # Loop only over dones
        for k, idx in enumerate(done_idxs):
            infos_new[idx] = {"episode": {"r": float(final_rs[k]), "l": int(final_ls[k])}}

        # Vectorized Reset
        episode_returns[done_idxs] = 0
        episode_lengths[done_idxs] = 0

    end_time = time.time()
    new_duration = end_time - start_time
    print(f"New Method Time: {new_duration:.6f}s")

    speedup = old_duration / new_duration if new_duration > 0 else 0
    print(f"Speedup: {speedup:.2f}x")

    # --- Case 2: 100% Dones (Worst Case for Vectorized?) ---
    print("\n--- Stress Test: 100% Dones ---")
    dones[:] = True

    # Old
    start_time = time.time()
    infos_old = []
    for i in range(num_envs):
        if dones[i]:
            infos_old.append({"episode": {"r": float(rewards[i]), "l": 10}})
        else:
            infos_old.append({})
    old_duration = time.time() - start_time

    # New
    start_time = time.time()
    infos_new = [{} for _ in range(num_envs)]
    if np.any(dones):
        done_idxs = np.where(dones)[0]
        final_rs = rewards[done_idxs]
        for k, idx in enumerate(done_idxs):
            infos_new[idx] = {"episode": {"r": float(final_rs[k]), "l": 10}}
    new_duration = time.time() - start_time

    print(f"Old (100% Done): {old_duration:.6f}s")
    print(f"New (100% Done): {new_duration:.6f}s")
    print(f"Speedup: {old_duration / new_duration:.2f}x")


if __name__ == "__main__":
    benchmark_overhead()
