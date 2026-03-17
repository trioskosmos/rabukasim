import os
import sys

import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.vec_env_adapter import VectorEnvAdapter


def test_pass_only():
    NUM_GAMES = 1
    MAX_STEPS = 1000
    env = VectorEnvAdapter(num_envs=1, observation_space_dim=8192)
    obs = env.reset()

    print(f"Starting Pass-Only Test for {NUM_GAMES} Games (Max {MAX_STEPS} steps per game)...")

    for game_idx in range(NUM_GAMES):
        print(f"\n--- Game {game_idx + 1} ---")
        game_done = False
        step_count = 0
        episode_reward = 0

        while not game_done and step_count < MAX_STEPS:
            # Action 0 = Pass
            action = 0

            env.step_async(np.array([action]))
            obs, rewards, dones, infos = env.step_wait()

            r = rewards[0]
            episode_reward += r
            step_count += 1

            if step_count % 10 == 0:
                print(f"Step {step_count}: Total Reward: {episode_reward:.1f}, Current Reward: {r:.1f}")
                print(f"  Agent Score: {env.game_state.batch_scores[0]}, Opp Score: {env.game_state.opp_scores[0]}")
                print(f"  Deck: {env.game_state.batch_global_ctx[0, 6]}, Turn: {env.game_state.turn}")

            if dones[0]:
                game_done = True
                print(f"Game Over naturally at step {step_count}.")
                print(f"Final Reward: {episode_reward}")

        if not game_done:
            print(f"Game reached MAX_STEPS ({MAX_STEPS}) without finishing.")
            print(f"Final Agent Score: {env.game_state.batch_scores[0]}, Opp Score: {env.game_state.opp_scores[0]}")


if __name__ == "__main__":
    import traceback

    try:
        test_pass_only()
    except Exception:
        print("\n!!! TEST CRASHED !!!")
        traceback.print_exc()
        sys.exit(1)
