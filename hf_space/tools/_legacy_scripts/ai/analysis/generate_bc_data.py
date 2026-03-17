import argparse
import os
import sys
import time

import numpy as np

# Ensure root is in path
sys.path.append(os.getcwd())

# We need to access the underlying heuristic function from CPU for the Generator
# Since VectorEnvGPU keeps state on GPU, we can't easily call CPU JIT functions on it without transfer.
# Ideally, we should implement a "select_heuristic_action_batch_gpu" kernel.
# BUT, for data generation, we can just use the CPU VectorEnv if speed is acceptable?
# Or, simpler: We transfer observation to CPU, run CPU heuristic JIT, then step GPU env.
# The CPU JIT function `select_heuristic_action` operates on single pointers.
# We need a wrapper to run it on a batch.

from ai.vector_env import VectorGameState  # CPU Env for simpler access to Numba functions
from numba import njit, prange

from engine.game.fast_logic import select_heuristic_action


@njit(parallel=True)
def batch_select_heuristic(
    num_envs,
    batch_hand,
    batch_deck,
    batch_stage,
    batch_energy_vec,
    batch_energy_count,
    batch_tapped,
    batch_live,
    batch_scores,
    batch_global_ctx,
    batch_trash,
    opp_tapped,
    card_stats,
    bytecode_index,
):
    actions = np.zeros(num_envs, dtype=np.int32)
    for i in prange(num_envs):
        actions[i] = select_heuristic_action(
            batch_hand[i],
            batch_deck[i],
            batch_stage[i],
            batch_energy_vec[i],
            batch_energy_count[i],
            batch_tapped[i],
            batch_live[i],
            batch_scores[i : i + 1],
            batch_global_ctx[i],
            batch_trash[i],
            opp_tapped[i],
            card_stats,
            bytecode_index,
        )
    return actions


def generate_bc_data(num_samples=100000, batch_size=1024, output_file="data/bc_dataset.npz"):
    print("=== BC Data Generator ===")
    print(f"Target: {num_samples} samples")

    # We use CPU VectorEnv for generation to ensure compatibility with the CPU JIT heuristic function
    # GPU Env would require porting the heuristic to CUDA kernel which is complex for now.
    # CPU Env 1024 batch is fast enough (e.g. 5000 SPS).

    env = VectorGameState(num_envs=batch_size, opp_mode=0)  # Heuristic Opponent
    env.reset()

    # Buffers
    obs_buffer = []
    act_buffer = []

    total_collected = 0
    start_time = time.time()

    while total_collected < num_samples:
        # 1. Get State
        # We need raw arrays for the heuristic
        # And Observations for the dataset

        # Get Obs
        obs = env.get_observations()  # (N, Dim)

        # 2. Select Heuristic Actions for AGENT (Player 0)
        # Using the CPU JIT wrapper
        agent_actions = batch_select_heuristic(
            batch_size,
            env.batch_hand,
            env.batch_deck,
            env.batch_stage,
            env.batch_energy_vec,
            env.batch_energy_count,
            env.batch_tapped,
            env.batch_live,
            env.batch_scores,
            env.batch_global_ctx,
            env.batch_trash,
            env.opp_tapped,
            env.card_stats,
            env.bytecode_index,
        )

        # 3. Store valid (non-pass) actions?
        # Behavior Cloning on "Pass" is also important (learning when to stop).
        # But we might want to filter out "Boring" passes (e.g. empty hand).
        # Let's keep everything for now, or filter simple passes.

        # Mask: Keep all
        # Optimization: Only save if we haven't reached limit

        # 4. Step Environment
        env.step(agent_actions)

        # 5. Append
        # Copy to CPU (already CPU)
        obs_buffer.append(obs.copy())
        act_buffer.append(agent_actions.copy())

        total_collected += batch_size
        if total_collected % 10000 == 0:
            print(f"Collected {total_collected}/{num_samples} samples...")

    # Concatenate
    print("Concatenating...")
    X = np.concatenate(obs_buffer, axis=0)[:num_samples]
    Y = np.concatenate(act_buffer, axis=0)[:num_samples]

    # Save
    print(f"Saving to {output_file}...")
    np.savez_compressed(output_file, obs=X, actions=Y)

    duration = time.time() - start_time
    print(f"Done in {duration:.2f}s. Rate: {total_collected / duration:.0f} samples/sec")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=100000)
    parser.add_argument("--out", type=str, default="data/bc_dataset.npz")
    args = parser.parse_args()

    generate_bc_data(args.num, 4096, args.out)  # Use larger batch for speed
