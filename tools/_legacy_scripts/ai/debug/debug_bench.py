import os
import sys

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.train_optimized import create_env


def run_benchmark():
    num_cpu = 1
    os.environ["TRAIN_CPUS"] = str(num_cpu)

    print(f"Initializing Dummy Benchmark with {num_cpu} workers...")
    env_fns = [
        partial(create_env, rank=i, usage=1.0, deck_type="random_verified", opponent_type="random")
        for i in range(num_cpu)
    ]
    # Use DummyVecEnv to see errors clearly
    env = DummyVecEnv(env_fns)

    print("Resetting environments...")
    obs = env.reset()

    steps_total = 0
    steps_target = 100

    print(f"Running {steps_target} steps...")

    while steps_total < steps_target:
        # Get random legal actions
        # env_method on DummyVecEnv
        try:
            masks = env.env_method("action_masks")
        except AttributeError:
            print("AttributeError: action_masks not found. Trying unwrapped...")
            masks = [e.unwrapped.action_masks() for e in env.envs]

        actions = []
        for m in masks:
            idx = np.where(m)[0]
            actions.append(np.random.choice(idx) if len(idx) > 0 else 0)

        obs, rews, terms, infos = env.step(np.array(actions))
        steps_total += num_cpu

    print(f"\nSuccess! Completed {steps_total} steps in Dummy mode.")
    env.close()


from functools import partial

if __name__ == "__main__":
    run_benchmark()
