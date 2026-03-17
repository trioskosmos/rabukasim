import os
import sys

import numpy as np

os.environ["OBS_MODE"] = "ATTENTION"
os.environ["TRAIN_ENVS"] = "4"
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


def main():
    print("DEBUG: Initializing VectorEnvAdapter")
    env = VectorEnvAdapter(num_envs=4)
    print(f"DEBUG: Adapter created, obs_dim={env.observation_space.shape}")

    print("DEBUG: Calling reset()")
    obs = env.reset()
    print(f"DEBUG: reset() returned obs.shape={obs.shape}")

    print("DEBUG: Calling step()")
    actions = np.zeros(4, dtype=np.int32)
    try:
        obs2, rew, done, info = env.step(actions)
        print(f"DEBUG: step() SUCCESS. obs2.shape={obs2.shape}")
    except Exception:
        import traceback

        print("DEBUG: step() FAILED")
        traceback.print_exc()


if __name__ == "__main__":
    main()
