import os
import sys
import time

import numpy as np

# Add project root to sys.path
sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def benchmark_live_capture():
    print("Benchmarking Live Capture...")
    env = LoveLiveCardGameEnv()

    total_steps = 0
    total_games = 0
    start_time = time.time()

    captured = False
    max_games = 1000

    while not captured and total_games < max_games:
        total_games += 1
        env.reset()
        game_steps = 0

        while True:
            game_steps += 1
            total_steps += 1

            masks = env.action_masks()
            legal_indices = np.where(masks)[0]

            if len(legal_indices) == 0:
                break

            action = np.random.choice(legal_indices)
            obs, reward, terminated, truncated, info = env.step(action)

            # Check for live capture
            p0_lives = len(env.game.players[0].success_lives)
            p1_lives = len(env.game.players[1].success_lives)

            if p0_lives > 0 or p1_lives > 0:
                print(f"\n[SUCCESS] Live captured in Game {total_games} at Step {game_steps}!")
                print(f"P0 Lives: {p0_lives}, P1 Lives: {p1_lives}")
                captured = True
                break

            if terminated or truncated:
                break

        if total_games % 10 == 0:
            print(f"Completed {total_games} games, {total_steps} total steps...")

    duration = time.time() - start_time
    print("\nFinal Stats:")
    print(f"Total Games Played: {total_games}")
    print(f"Total Steps Executed: {total_steps}")
    print(f"Time Taken: {duration:.2f} seconds")
    print(f"Throughput: {total_steps / duration:.2f} steps/sec")

    if not captured:
        print("Failed to capture a live within the game limit.")


if __name__ == "__main__":
    benchmark_live_capture()
