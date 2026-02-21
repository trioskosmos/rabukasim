import argparse
import os
import sys
import time

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


def benchmark_random(duration_sec=15):
    print(f"Starting Random Agent Benchmark for {duration_sec}s...")

    # Initialize Environment
    os.environ["OBS_MODE"] = "COMPRESSED"
    num_envs = 100
    env = VectorEnvAdapter(num_envs=num_envs)

    print("Compiling (Warmup)...")
    env.reset()
    # Dummy step
    dummy_actions = np.zeros(num_envs, dtype=np.int32)
    env.step(dummy_actions)

    print("Benchmark Started...")
    start_time = time.time()
    steps = 0
    total_episodes = 0
    wins = 0
    max_score = 0
    agent_scores_list = []

    env.reset()

    while time.time() - start_time < duration_sec:
        action_masks = env.action_masks()

        # RANDOM POLICY
        actions = np.zeros(num_envs, dtype=np.int32)
        for i in range(num_envs):
            legal_actions = np.where(action_masks[i])[0]
            # Heuristic: Avoid passing (0) if other moves are possible to see board activity
            if len(legal_actions) > 1:
                actions[i] = np.random.choice(legal_actions[legal_actions != 0])
            else:
                actions[i] = 0

        obs, rewards, dones, infos = env.step(actions)
        steps += num_envs

        # Process completions
        for i in range(num_envs):
            if dones[i]:
                total_episodes += 1
                info = infos[i]
                agent_score = info.get("terminal_score_agent", 0)
                opp_score = info.get("terminal_score_opp", 0)

                agent_scores_list.append(agent_score)
                if agent_score > max_score:
                    max_score = agent_score

                if agent_score > opp_score:
                    wins += 1

    duration = time.time() - start_time

    print("\n" + "=" * 40)
    print(" RANDOM AGENT BENCHMARK RESULTS")
    print("=" * 40)
    print(f"Duration:       {duration:.2f} s")
    print(f"Total Steps:    {steps}")
    print(f"Episodes:       {total_episodes}")
    print(f"Throughput:     {steps / duration:.2f} steps/sec")

    if total_episodes > 0:
        win_rate = (wins / total_episodes) * 100.0
        avg_score = sum(agent_scores_list) / len(agent_scores_list)

        print(f"Win Rate:       {win_rate:.2f}%")
        print(f"Avg Score:      {avg_score:.2f}")
        print(f"Max Score:      {max_score}")
    else:
        print("No episodes completed.")
    print("=" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=15, help="Duration in seconds")
    args = parser.parse_args()
    benchmark_random(args.duration)
