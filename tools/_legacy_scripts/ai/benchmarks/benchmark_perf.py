import os
import sys
import time
from functools import partial

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def create_env(rank, usage=0.5):
    env = LoveLiveCardGameEnv(target_cpu_usage=usage, deck_type="training")
    # Reset to init
    env.reset(seed=42 + rank)
    return env


def run_benchmark():
    num_cpu = 1
    usage = 0.5
    duration = 10.0

    print(f"Benchmarking (Single Core Safe Mode): {num_cpu} cores @ {usage * 100}% usage for {duration} seconds...")

    # Create envs
    env_fns = [partial(create_env, rank=i, usage=usage) for i in range(num_cpu)]
    vec_env = DummyVecEnv(env_fns)

    print("Environments initialized (DummyVecEnv). Starting benchmark...")

    obs = vec_env.reset()
    start_time = time.time()
    steps = 0
    max_reward = -float("inf")

    # Run for up to 30 seconds or until positive reward
    while time.time() - start_time < 30.0:
        # Get legal masks
        masks = vec_env.env_method("action_masks")
        actions = []
        for mask in masks:
            legal_indices = np.where(mask)[0]
            if len(legal_indices) > 0:
                actions.append(np.random.choice(legal_indices))
            else:
                actions.append(0)

        obs, rewards, dones, infos = vec_env.step(actions)
        steps += num_cpu

        if dones[0]:
            print(f"\n[Bench] Game Finished at step {steps}. Reward: {rewards[0]}")
            # Reset max_reward for new game if we want to see per-game peaks,
            # but keeping global peak is fine for "did we ever score?"

        current_reward = rewards[0]
        if current_reward > max_reward:
            max_reward = current_reward
            if max_reward > 0.05:
                print(f"\nSUCCESS: Reward {max_reward:.4f} achieved at step {steps}!")
                break

        if steps % 1000 == 0:
            print(f"\rSteps: {steps}, Max Reward: {max_reward:.4f}", end="")

    print("\n" + "-" * 40)
    print(f"Total Steps: {steps}")
    print(f"Max Reward Encountered: {max_reward:.4f}")

    elapsed = time.time() - start_time
    sps = steps / elapsed

    print("-" * 40)
    print(f"Total Steps: {steps}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Throughput: {sps:.2f} Steps/Second")
    print(f"Per Core: {sps / num_cpu:.2f} Steps/Second")
    print("-" * 40)

    vec_env.close()


if __name__ == "__main__":
    run_benchmark()
