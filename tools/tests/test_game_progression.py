import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

import numpy as np
from ai.gym_env import LoveLiveCardGameEnv


def test_game_progression():
    env = LoveLiveCardGameEnv()
    obs, info = env.reset()

    print(f"Game Started. Initial Phase: {env.game.phase.name}")

    done = False
    step_count = 0
    while not done and step_count < 1000:
        step_count += 1

        # Get legal actions
        mask = env.game.get_legal_actions()
        legal_indices = np.where(mask)[0]

        if len(legal_indices) == 0:
            print(f"CRITICAL ERROR: No legal actions in phase {env.game.phase.name}")
            break

        # Pick random action
        action = int(np.random.choice(legal_indices))

        old_phase = env.game.phase
        old_player = env.game.current_player

        obs, reward, done, truncated, info = env.step(action)

        new_phase = env.game.phase
        new_player = env.game.current_player

        print(
            f"Step {step_count}: P{old_player} in {old_phase.name} -> Action {action} -> P{new_player} in {new_phase.name}"
        )

        # Log success lives
        p0_lives = len(env.game.players[0].success_lives)
        p1_lives = len(env.game.players[1].success_lives)
        if p0_lives > 0 or p1_lives > 0:
            print(f"!!! LIVE CAPTURED !!! P0: {p0_lives}, P1: {p1_lives}")
            break

        if env.game.game_over:
            print(f"Game Over. Winner: {env.game.winner}")
            if hasattr(env.game, "rule_log"):
                for entry in env.game.rule_log[-5:]:
                    print(f"  Log: {entry}")
            break


if __name__ == "__main__":
    test_game_progression()
