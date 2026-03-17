import os
import sys

import numpy as np

# Add current dir to path
sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def analyze_final_rewards():
    env = LoveLiveCardGameEnv(target_cpu_usage=1.0, deck_type="random_verified")

    total_games = 20
    all_game_data = []

    print(f"Analyzing final rebalanced rewards across {total_games} random play games...")

    wins = 0
    losses = 0
    draws = 0

    for i in range(total_games):
        obs, info = env.reset()
        terminated = False
        game_reward = 0
        steps = 0

        while not terminated and steps < 3000:
            masks = env.action_masks()
            legal_indices = np.where(masks)[0]

            if len(legal_indices) == 0:
                break

            action = np.random.choice(legal_indices)
            obs, reward, terminated, truncated, info = env.step(action)

            game_reward += reward
            steps += 1

        winner = env.game.winner
        if winner == 0:
            wins += 1
        elif winner == 1:
            losses += 1
        else:
            draws += 1

        all_game_data.append({"reward": game_reward, "winner": winner, "steps": steps})

    print("\n--- Final Simulation Summary ---")
    print(f"Total Games: {total_games}")
    print(f"Wins: {wins} | Losses: {losses} | Draws/Timeouts: {draws}")

    for i, d in enumerate(all_game_data):
        res = "WIN" if d["winner"] == 0 else "LOSS" if d["winner"] == 1 else "DRAW"
        print(f"Game {i + 1}: {res}, Reward: {d['reward']:.2f}, Steps: {d['steps']}")


if __name__ == "__main__":
    analyze_final_rewards()
