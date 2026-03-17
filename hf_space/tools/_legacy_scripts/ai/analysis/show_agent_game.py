import os
import sys

import numpy as np

# Ensure we can import ai modules
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from stable_baselines3 import MaskablePPO


def show_game():
    print("--- Individual Game Debugger ---")
    model_path = "checkpoints/vector/interrupted_model.zip"

    # Try to find the latest if interrupted doesn't exist, or just use it
    if not os.path.exists(model_path):
        print(f"Warning: {model_path} not found. Configuring for fresh run or check other paths.")
        # Logic to find latest could go here, but let's stick to interrupted for now

    print(f"Loading: {model_path}")

    # Create Env (1 env for visualization)
    env = VectorEnvAdapter(n_envs=1, render_mode="human")

    # Load Model
    try:
        model = MaskablePPO.load(model_path, env=env)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    obs = env.reset()

    # Force Main Phase for start logic if needed, but reset should handle it
    # env.game_state.batch_global_ctx[0, 8] = 3

    print("\nStarting Game Log:")
    print("--------------------------------")

    done = False
    total_reward = 0.0

    while not done:
        # Get Action
        action, _ = model.predict(obs, action_masks=env.action_masks())

        # Log State BEFORE Action
        turn = env.game_state.turn
        score_p0 = env.game_state.batch_scores[0, 0]
        score_p1 = env.game_state.opp_scores[0]  # Opponent score
        phase = env.game_state.batch_global_ctx[0, 8]  # PH

        # Get Hand
        hand = env.game_state.batch_hand[0]
        compact_hand = [f"np.int32({c})" for c in hand if c > 0]

        # Get Legal Actions
        masks = env.action_masks()[0]
        legal_indices = np.where(masks)[0]

        print(f"Turn {turn:2} | Score: {score_p0}-{score_p1} | Phase: {phase} | Action: {action[0]}")
        print(f"   Hand IDs (compact): [{', '.join(compact_hand)}]")
        print(f"   Raw batch_hand: {hand[:20]}...")  # Show first 20 for brevity
        print(f"   Legal Actions ({len(legal_indices)}): {legal_indices}...")
        print(f"   Played: {action[0]}")

        # Step
        obs, reward, done_array, infos = env.step(action)
        reward = reward[0]
        done = done_array[0]

        # Log Result
        new_hand = env.game_state.batch_hand[0]
        # compact_new = [c for c in new_hand if c > 0]
        stage = env.game_state.batch_stage[0]

        print(f"   Hand: [{', '.join([f'np.int32({c})' for c in new_hand if c > 0])}]...")
        print(f"   Stage: {stage}")

        # ALWAYS Show Reward
        print(f"   REWARD: {reward}")

        total_reward += reward

        if done:
            print("--------------------------------")
            print(f"GAME ENDED! Final Score: {env.game_state.batch_scores[0, 0]}-{env.game_state.opp_scores[0]}")
            print(f"Total Reward: {total_reward}")
            print("--------------------------------")
            break


if __name__ == "__main__":
    show_game()
