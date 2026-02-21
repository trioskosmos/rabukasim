import argparse
import os
import sys
import time

import numpy as np
import torch

# Add project root to path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def benchmark_model(model_path, duration_sec=30):
    print(f"Loading Model from: {model_path}")

    # Check if model exists
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return

    # Initialize Environment
    print("Initializing Environment...")
    os.environ["OBS_MODE"] = "COMPRESSED"  # Ensure matches training
    num_envs = 100  # High throughput for benchmarking
    env = VectorEnvAdapter(num_envs=num_envs)

    # Load Model
    # We might need custom_objects if python versions mismatch, but usually fine same-machine
    try:
        model = MaskablePPO.load(model_path, device="cuda" if torch.cuda.is_available() else "cpu")
        print(f"Model Loaded. Device: {model.device}")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print("Compiling (Warmup)... This might take ~60s.")
    obs = env.reset()
    # Dummy step to force compilation
    # We need valid actions though?
    # Just allow the model to predict once.
    action_masks = env.action_masks()
    actions, _ = model.predict(obs, action_masks=action_masks, deterministic=True)
    env.step(actions)

    print(f"Compilation Complete! Starting {duration_sec}s Benchmark...")
    print("Using Deterministic Mode for Evaluation.")

    start_time = time.time()
    steps = 0

    # Stats Tracking
    total_episodes = 0
    wins = 0
    rewards_list = []
    lengths_list = []
    agent_scores_list = []
    opp_scores_list = []

    # Per-episode accumulators
    current_rewards = np.zeros(num_envs)
    current_lengths = np.zeros(num_envs)

    obs = env.reset()

    while time.time() - start_time < duration_sec:
        action_masks = env.action_masks()

        # MODEL PREDICTION
        actions, _ = model.predict(obs, action_masks=action_masks, deterministic=True)

        obs, rewards, dones, infos = env.step(actions)
        steps += num_envs

        current_rewards += rewards
        current_lengths += 1

        # Process completions
        for i in range(num_envs):
            if dones[i]:
                total_episodes += 1

                info = infos[i]
                agent_score = info.get("terminal_score_agent", 0)
                opp_score = info.get("terminal_score_opp", 0)

                rewards_list.append(current_rewards[i])
                lengths_list.append(current_lengths[i])
                agent_scores_list.append(agent_score)
                opp_scores_list.append(opp_score)

                if agent_score > opp_score:
                    wins += 1

                # Reset accumulators for this env
                current_rewards[i] = 0
                current_lengths[i] = 0

    duration = time.time() - start_time

    print("\n" + "=" * 40)
    print(" BENCHMARK RESULTS (PPO Model)")
    print("=" * 40)
    print(f"Model:          {os.path.basename(model_path)}")
    print(f"Duration:       {duration:.2f} s")
    print(f"Total Steps:    {steps}")
    print(f"Throughput:     {steps / duration:.2f} steps/sec")
    print(f"Total Episodes: {total_episodes}")

    if total_episodes > 0:
        avg_rew = sum(rewards_list) / len(rewards_list)
        avg_len = sum(lengths_list) / len(lengths_list)
        avg_score_ag = sum(agent_scores_list) / len(agent_scores_list)
        avg_score_opp = sum(opp_scores_list) / len(opp_scores_list)
        win_rate = (wins / total_episodes) * 100.0

        print(f"Win Rate:       {win_rate:.2f}%")
        print(f"Avg Reward:     {avg_rew:.2f}")
        print(f"Avg Length:     {avg_len:.2f} steps")
        print(f"Avg Score (Ag): {avg_score_ag:.2f}")
        print(f"Avg Score (Op): {avg_score_opp:.2f}")
    else:
        print("No episodes completed.")
    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path", type=str, help="Path to model.zip")
    parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    args = parser.parse_args()

    benchmark_model(args.model_path, args.duration)
