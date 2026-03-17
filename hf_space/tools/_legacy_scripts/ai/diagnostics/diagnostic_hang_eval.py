import os
import sys
import time

import numpy as np

sys.path.append(os.getcwd())
from ai.vec_env_adapter import VectorEnvAdapter


def diagnostic():
    print("Testing VectorEnvAdapter initialization...")
    start = time.time()
    # Set OBS_MODE to COMPRESSED to match the model we are testing
    os.environ["OBS_MODE"] = "COMPRESSED"
    env = VectorEnvAdapter(num_envs=4)  # Small count for fast check
    print(f"Init done in {time.time() - start:.2f}s")

    print("Testing env.reset()...")
    start = time.time()
    obs = env.reset()
    print(f"Reset done in {time.time() - start:.2f}s (Obs Shape: {obs.shape})")

    print("Testing env.action_masks() + env.step(random) 10 times...")
    durations = []
    for i in range(10):
        start = time.time()
        masks = env.action_masks()

        # Simple random action selection based on masks
        actions = np.zeros(4, dtype=np.int32)
        for env_idx in range(4):
            valid_indices = np.where(masks[env_idx])[0]
            if len(valid_indices) > 0:
                actions[env_idx] = np.random.choice(valid_indices)

        obs, rewards, dones, infos = env.step(actions)
        dur = time.time() - start
        durations.append(dur)
        print(f" Step {i + 1}: {dur:.4f}s")

    avg_dur = sum(durations) / len(durations)
    print(f"Average Step time: {avg_dur:.4f}s")
    print(f"Max Step time: {max(durations):.4f}s")
    print(f"Min Step time: {min(durations):.4f}s")

    print("Diagnostic Complete.")


if __name__ == "__main__":
    diagnostic()
