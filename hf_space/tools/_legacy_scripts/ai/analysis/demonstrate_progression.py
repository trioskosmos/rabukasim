import os
import sys

import numpy as np

# Add current dir to path
sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def demonstrate_progression():
    # Use 1.0 usage to avoid sleeps
    env = LoveLiveCardGameEnv(target_cpu_usage=1.0, deck_type="random_verified")

    print("--- PROOF: Game Progression and Rewards ---")

    for game_idx in range(3):
        print(f"\n--- Game {game_idx + 1} ---")
        obs, info = env.reset()

        terminated = False
        steps = 0
        last_phase = None

        print(f"Start: Turn {env.game.turn_number}, Phase {env.game.phase.name}")

        while not terminated and steps < 1000:
            current_phase = env.game.phase.name
            if current_phase != last_phase:
                print(f"[{steps}] Phase Transition: {last_phase} -> {current_phase}")
                last_phase = current_phase

            masks = env.action_masks()
            legal_indices = np.where(masks)[0]

            if len(legal_indices) == 0:
                print(f"[{steps}] No legal actions. Breaking.")
                break

            action = np.random.choice(legal_indices)
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1

            if reward != -0.01:  # Show non-standard step rewards
                print(f"[{steps}] Step Reward: {reward:+.2f} (Action {action})")

        print(f"End: Result Winner={env.game.winner}, Turn={env.game.turn_number}, Phase={env.game.phase.name}")
        print(f"Total Steps (Agent): {steps}")
        print(f"Total Episode Reward: {env.episode_reward:.2f}")


if __name__ == "__main__":
    demonstrate_progression()
