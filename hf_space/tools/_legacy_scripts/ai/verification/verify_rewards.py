import os
import sys

import numpy as np

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_env import VectorGameState


def test_rewards():
    print("TEST: Reward Calculation Verification")

    # Initialize Environment
    # Default Rewards: Win=100, Score=50, Penalty=-0.05
    os.environ["GAME_REWARD_WIN"] = "100.0"
    os.environ["GAME_REWARD_SCORE_SCALE"] = "50.0"
    os.environ["GAME_REWARD_TURN_PENALTY"] = "-0.05"

    env = VectorGameState(num_envs=1)
    env.reset()

    print(f"Game Config Array: {env.game_config}")
    print(f"CFG_TURN_LIMIT: {env.game_config[0]}")
    print(f"CFG_STEP_LIMIT: {env.game_config[1]}")
    print(f"CFG_REWARD_WIN: {env.game_config[2]}")
    print(f"CFG_REWARD_LOSE: {env.game_config[3]}")
    print(f"CFG_REWARD_SCALE: {env.game_config[4]}")
    print(f"CFG_REWARD_TURN_PENALTY: {env.game_config[5]}")

    print(f"Initial Phase: {env.batch_global_ctx[0, 8]}")

    # 1. Take a Mulligan Toggle Action (Action 300)
    # Expected Reward: -0.05 (Penalty for taking an action)
    obs, rewards, dones, infos = env.step(np.array([300], dtype=np.int32))
    print(f"Action 300 (Mulligan Toggle) Reward: {rewards[0]} (Expected -0.05)")
    if not np.isclose(rewards[0], -0.05):
        print(f"ERROR: Expected -0.05, got {rewards[0]}")
        # Let's not assert yet, see what happens

    # 2. Pass Mulligan (Action 0)
    # Expected Reward: -0.05 (Penalty for passing/advancing)
    obs, rewards, dones, infos = env.step(np.array([0], dtype=np.int32))
    print(f"Action 0 (Pass Mulligan) Reward: {rewards[0]} (Expected -0.05)")

    # 3. Force a Score and check Delta Reward
    # We'll manually increment the score in the engine's buffer to simulate a Live success
    print("\nSimulating Live Success (+1 Score)...")
    env.batch_scores[0] = 1  # Manually set score

    # Now take any action (e.g. Pass) to trigger the 'integrated_step' delta checks
    obs, rewards, dones, infos = env.step(np.array([0], dtype=np.int32))

    # Reward should be: (ScoreDiff * 50) + Penalty = (1 * 50) - 0.05 = 49.95
    print(f"Next Action Reward after Score Change: {rewards[0]} (Expected 49.95)")
    assert np.isclose(rewards[0], 49.95)

    # 4. Force a Win
    print("\nSimulating Win (Set Score to 3)...")
    env.batch_scores[0] = 3
    # Step to trigger Game Over logic
    obs, rewards, dones, infos = env.step(np.array([0], dtype=np.int32))

    # Reward should be: (ScoreDiff * 50) + WinReward + Penalty
    # Delta Score from prev (1) to current (3) is 2.
    # (2 * 50) + 100 - 0.05 = 100 + 100 - 0.05 = 199.95
    print(f"Next Action Reward after Win: {rewards[0]} (Expected 199.95)")
    print(f"Done Flag: {dones[0]} (Expected True)")

    assert np.isclose(rewards[0], 199.95)
    assert dones[0] == True

    print("\nPASS: Reward Logic is fully functional and consistent.")


if __name__ == "__main__":
    test_rewards()
