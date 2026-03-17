import os
import sys

import numpy as np

# Ensure path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


def verify_gameplay():
    print("=== VERIFYING GAMEPLAY LOGIC ===")

    # 1. Initialize
    num_envs = 10
    print(f"Initializing {num_envs} environments...")
    env = VectorEnvAdapter(num_envs=num_envs)

    print("Resetting...")
    env.reset()

    # Trackers for Env 0
    g_ctx = env.game_state.batch_global_ctx
    scores = env.game_state.batch_scores

    last_turn = g_ctx[0, 54]
    last_score = scores[0]
    last_phase = g_ctx[0, 8]

    print(f"Start: Turn {last_turn}, Score {last_score}, Phase {last_phase}")

    # 2. Loop
    print("\nRunning simulated steps...")

    steps = 200
    for i in range(steps):
        # Random valid actions
        # 0 = Pass
        # 1..180 = Play Member
        # 200..202 = Activate Ability
        actions = np.random.randint(0, 203, size=num_envs, dtype=np.int32)

        # Force some passes to advance phases
        if i % 5 == 0:
            actions[:] = 0

        obs, rewards, dones, infos = env.step(actions)

        # Check Env 0 changes
        curr_turn = g_ctx[0, 54]
        curr_score = scores[0]
        curr_phase = g_ctx[0, 8]

        if curr_turn != last_turn:
            print(f" [Step {i}] Turn Advanced: {last_turn} -> {curr_turn}")
            last_turn = curr_turn

        if curr_score != last_score:
            print(f" [Step {i}] Score Changed: {last_score} -> {curr_score}")
            last_score = curr_score

        if curr_phase != last_phase:
            print(f" [Step {i}] Phase Changed: {last_phase} -> {curr_phase} (Action: {actions[0]})")
            last_phase = curr_phase

        if dones[0]:
            print(f" [Step {i}] Env 0 DONE! Reward: {rewards[0]}")

    print("\nGameplay Verification Completed.")
    print(f"Final State Env 0: Turn {curr_turn}, Score {curr_score}")


if __name__ == "__main__":
    verify_gameplay()
