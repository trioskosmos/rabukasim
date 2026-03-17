import os
import sys

import numpy as np

# Ensure path
sys.path.append(os.getcwd())

import ai.vector_env
from ai.vec_env_adapter import VectorEnvAdapter

print(f"DEBUG: Loading ai.vector_env from: {ai.vector_env.__file__}")


def check_adapter():
    print("--- Checking VectorEnvAdapter ---")

    try:
        num_envs = 50
        print(f"Initializing Adapter with {num_envs} envs...")
        env = VectorEnvAdapter(num_envs=num_envs)

        print("Resetting Env...")
        print(f"Game State Keys: {[k for k in dir(env.game_state) if 'opp' in k]}")
        obs = env.reset()
        print(f"Obs Shape: {obs.shape}")

        print("Getting Action Masks...")
        masks = env.action_masks()
        print(f"Masks Shape: {masks.shape}")

        # Test Step with Real Action for all
        env.game_state.batch_hand[:, 0] = 586
        env.game_state.batch_global_ctx[:, 3] = 1  # HD
        actions = np.full(num_envs, 586, dtype=np.int32)
        print(f"Stepping with Actions: {actions[:5]}...")
        obs, rewards, dones, infos = env.step(actions)

        print("Step Success!")
        print(f"Reward: {rewards}")
        print(f"Done: {dones}")
        print(f"Info: {infos}")

    except Exception as e:
        print(f"CRASH DETECTED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_adapter()
