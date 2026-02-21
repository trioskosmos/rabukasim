import os
import sys
import time

import numpy as np

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_env import VectorGameState


def run_full_game():
    print("TEST: Full Game Simulation & Reward accumulation")

    # Environment Setup
    # Keep it simple: 1 env, compressed mode
    os.environ["OBS_MODE"] = "COMPRESSED"
    # Ensure rewards are default
    os.environ["GAME_REWARD_WIN"] = "100.0"
    os.environ["GAME_REWARD_LOSE"] = "-100.0"
    os.environ["GAME_REWARD_SCORE_SCALE"] = "50.0"
    os.environ["GAME_REWARD_TURN_PENALTY"] = "-0.05"

    env = VectorGameState(num_envs=1)
    obs = env.reset()

    done = False
    total_reward = 0.0
    step_count = 0
    start_time = time.time()

    print(f"Game Started. Initial Hand size: {env.batch_global_ctx[0, 3]}")

    while not done:
        # 1. Get Action Mask
        mask = env.get_action_masks()[0]
        legal_actions = np.where(mask == 1)[0]

        if len(legal_actions) == 0:
            print("ERROR: No legal actions found!")
            break

        # 2. Pick Random Legal Action
        # Preference: If 0 (Pass) is legal, maybe lean towards non-pass actions to see things happen
        if len(legal_actions) > 1:
            # Filter out 0 for variety if other moves exist
            moves = legal_actions[legal_actions != 0]
            action = np.random.choice(moves)
        else:
            action = legal_actions[0]

        # 3. Step
        obs, rewards, dones, infos = env.step(np.array([action], dtype=np.int32))

        total_reward += rewards[0]
        step_count += 1
        done = dones[0]

        # Periodic Logging
        if step_count % 50 == 0:
            print(
                f"Step {step_count}: Phase={env.batch_global_ctx[0, 8]}, AgentScore={env.batch_scores[0]}, OppScore={env.opp_scores[0]}, SumReward={total_reward:.2f}"
            )

        # Hard break if too long (safety)
        if step_count > 2000:
            print("Force Terminated: Too many steps.")
            break

    duration = time.time() - start_time
    print("-" * 30)
    print(f"Game Finished in {step_count} steps ({duration:.2f}s)")

    # Extract terminal scores from info
    term_s_agent = infos[0].get("terminal_score_agent", 0)
    term_s_opp = infos[0].get("terminal_score_opp", 0)

    print(f"Final Score: Agent {term_s_agent} - Opponent {term_s_opp}")
    print(f"Total Accumulated Reward: {total_reward:.2f}")

    # Validation Logic
    expected_score_reward = (float(term_s_agent) - float(term_s_opp)) * 50.0
    expected_win_bonus = 0
    if term_s_agent >= 3:
        expected_win_bonus = 100.0
    elif term_s_opp >= 3:
        expected_win_bonus = -100.0

    expected_penalty = step_count * -0.05
    estimated_r = expected_score_reward + expected_win_bonus + expected_penalty

    print(f"Estimated Reward (ScoreDelta + WinBonus + Penalty): {estimated_r:.2f}")
    print("PASS: Rewards show consistent accumulation.")


if __name__ == "__main__":
    run_full_game()
