import os
import sys
from collections import Counter

import numpy as np

# Add current dir to path
sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def analyze_phases():
    env = LoveLiveCardGameEnv(target_cpu_usage=1.0, deck_type="random_verified")

    total_games = 10
    phase_counter = Counter()
    total_actions = 0

    print(f"Analyzing phase distribution across {total_games} random play games...")

    for i in range(total_games):
        obs, info = env.reset()
        terminated = False
        steps = 0

        while not terminated and steps < 2000:
            phase_name = env.game.phase.name if hasattr(env.game.phase, "name") else str(env.game.phase)
            phase_counter[phase_name] += 1

            masks = env.action_masks()
            legal_indices = np.where(masks)[0]

            if len(legal_indices) == 0:
                break

            action = np.random.choice(legal_indices)
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            total_actions += 1

        print(f"Game {i + 1}: Result: {env.game.winner}, Steps: {steps}, Turns: {env.game.turn_number}")

    print("\n--- Phase Distribution ---")
    for phase, count in phase_counter.items():
        print(f"{phase}: {count} ({count / total_actions * 100:.1f}%)")

    print(f"\nTotal Actions: {total_actions}")
    print(f"Average Actions per Game: {total_actions / total_games:.1f}")


if __name__ == "__main__":
    analyze_phases()
