import os
import sys

import numpy as np

# Mock ENV
os.environ["OBS_MODE"] = "ATTENTION"
os.environ["TRAIN_ENVS"] = "16"

sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


def main():
    print("Initializing Adapter...")
    try:
        env = VectorEnvAdapter(num_envs=16)
        print("Adapter Created. Resetting...")
        obs = env.reset()
        print(f"Reset Complete. Obs Shape: {obs.shape}")

        print("Stepping...")
        actions = np.zeros(16, dtype=np.int32)
        obs, rew, done, info = env.step(actions)
        print("Step Complete.")

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
