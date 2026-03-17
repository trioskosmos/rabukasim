import argparse
import os
import sys
import time

import numpy as np

# Ensure root is in path
sys.path.append(os.getcwd())

from ai.vector_env_gpu import VectorEnvGPU

try:
    import cupy as cp
except ImportError:
    cp = None


def mine_scenarios(num_scenarios=10000, batch_size=4096, max_steps=100, output_file="data/scenarios_large.npz"):
    """
    Mines game states from the GPU environment by running simulations and capturing
    interesting mid-game states.
    """
    print("=== GPU Scenario Miner ===")
    print(f"Target: {num_scenarios} scenarios")
    print(f"Batch Size: {batch_size}")

    # Force GPU mode
    os.environ["USE_GPU_ENV"] = "1"

    # Initialize Env
    # Use Heuristic Opponent (mode 0) to get realistic board states
    env = VectorEnvGPU(num_envs=batch_size, opp_mode=0)
    env.reset()

    # Storage for collected scenarios
    collected_count = 0
    buffer = {
        "batch_hand": [],
        "batch_deck": [],
        "batch_stage": [],
        "batch_energy_vec": [],
        "batch_energy_count": [],
        "batch_continuous_vec": [],
        "batch_continuous_ptr": [],
        "batch_tapped": [],
        "batch_live": [],
        "batch_scores": [],
        "batch_flat_ctx": [],
        "batch_global_ctx": [],
        "opp_hand": [],
        "opp_deck": [],
        "opp_stage": [],
        "opp_energy_vec": [],
        "opp_energy_count": [],
        "opp_tapped": [],
        "opp_live": [],
        "opp_scores": [],
        "opp_global_ctx": [],
    }

    start_time = time.time()
    total_sim_steps = 0

    # Action buffer (all zeros = Pass, but we want random/heuristic actions?)
    # VectorEnvGPU takes actions. If we pass 0, the agent just passes.
    # We want the AGENT to play too, so we get mid-game states where the agent has stuff.
    # We don't have a Heuristic Agent policy implemented for GPU easily accessible here?
    # Actually, VectorEnvGPU assumes external actions.
    # IF we just pass 0, the agent will die/lose.
    # We need a random policy at least.

    print("Starting mining loop...")

    for step in range(max_steps):
        # Generate Random Actions
        # Action space: 0 (Pass), 1-180 (Play), 181-183 (Ability), 184-243 (Live)
        # Simple random policy:
        actions = np.random.randint(0, 244, size=batch_size, dtype=np.int32)

        # Step
        obs, rewards, dones, infos = env.step(actions)
        total_sim_steps += batch_size

        # Analyze States
        # We need to look at global_ctx to find interesting states.
        # global_ctx shape: (N, 128)
        # Indices:
        #   54: Turn Number
        #   0: Agent Score (Lives) ? No, Agent Score is in batch_scores
        #   1: Opp Score ? No

        # Let's pull relevant data to CPU for filtering
        if cp:
            # Check turn numbers
            # batch_global_ctx is int32
            # We want Turn > 2 and Turn < 10 (mid game)
            # We want Scores to be close.

            # Transfer small metadata to CPU
            turns = cp.asnumpy(env.batch_global_ctx[:, 54])
            p_scores = cp.asnumpy(env.batch_scores)
            o_scores = cp.asnumpy(env.opp_scores)

            # Criteria:
            # 1. Turn >= 3
            # 2. Both players have at least 1 Live (Score >= 1) OR Score Diff is small
            # 3. Not Game Over (dones is False)

            # Create mask
            mask = (turns >= 3) & (turns < 20) & (p_scores + o_scores >= 1) & (np.abs(p_scores - o_scores) <= 1)

            # Apply mask
            indices = np.where(mask)[0]

            if len(indices) > 0:
                # Limit collection rate
                # If we take too many from one step, they are correlated.
                # Take a random subsample (e.g. 10%)
                if len(indices) > 100:
                    indices = np.random.choice(indices, size=int(len(indices) * 0.1), replace=False)

                # Copy data for these indices
                def copy_field(name, source_gpu):
                    data = cp.asnumpy(source_gpu[indices])
                    buffer[name].append(data)

                copy_field("batch_hand", env.batch_hand)
                copy_field("batch_deck", env.batch_deck)
                copy_field("batch_stage", env.batch_stage)
                copy_field("batch_energy_vec", env.batch_energy_vec)
                copy_field("batch_energy_count", env.batch_energy_count)
                copy_field("batch_continuous_vec", env.batch_continuous_vec)
                copy_field("batch_continuous_ptr", env.batch_continuous_ptr)
                copy_field("batch_tapped", env.batch_tapped)
                copy_field("batch_live", env.batch_live)
                copy_field("batch_scores", env.batch_scores)
                copy_field("batch_flat_ctx", env.batch_flat_ctx)
                copy_field("batch_global_ctx", env.batch_global_ctx)

                copy_field("opp_hand", env.opp_hand)
                copy_field("opp_deck", env.opp_deck)
                copy_field("opp_stage", env.opp_stage)
                copy_field("opp_energy_vec", env.opp_energy_vec)
                copy_field("opp_energy_count", env.opp_energy_count)
                copy_field("opp_tapped", env.opp_tapped)
                copy_field("opp_live", env.opp_live)
                copy_field("opp_scores", env.opp_scores)
                copy_field("opp_global_ctx", env.opp_global_ctx)

                collected_count += len(indices)
                print(f"  Step {step}: Collected {len(indices)} states. Total: {collected_count}/{num_scenarios}")

        if collected_count >= num_scenarios:
            break

        # Reset completed envs automatically handled by VectorEnvGPU?
        # Yes, auto-reset is built-in.

    print(f"Finished mining. Total collected: {collected_count}")
    print("Processing and saving...")

    # Concatenate and Save
    final_data = {}
    for k, v in buffer.items():
        if v:
            final_data[k] = np.concatenate(v, axis=0)
            # Trim to requested number
            if len(final_data[k]) > num_scenarios:
                final_data[k] = final_data[k][:num_scenarios]
        else:
            final_data[k] = np.array([])

    np.savez_compressed(output_file, **final_data)

    duration = time.time() - start_time
    print(f"Saved {len(final_data['batch_hand'])} scenarios to {output_file}")
    print(f"Time: {duration:.2f}s")
    print(f"Rate: {collected_count / duration:.0f} scenarios/sec")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=10000)
    parser.add_argument("--out", type=str, default="data/scenarios_large.npz")
    args = parser.parse_args()

    mine_scenarios(num_scenarios=args.num, output_file=args.out)
