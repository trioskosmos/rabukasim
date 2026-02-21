import os
import sys

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def run_diagnostic_benchmark(model_path="checkpoints/vector/interrupted_model.zip", num_games=50):
    if not os.path.exists(model_path):
        print(f"Error: Model {model_path} not found.")
        return

    print(f"--- Diagnostic Benchmark: {model_path} ---")
    env = VectorEnvAdapter(num_envs=1)  # Run 1 by 1 for detailed logging
    model = MaskablePPO.load(model_path, env=env, device="cpu")

    match_stats = []

    for i in range(num_games):
        obs = env.reset()
        done = False
        turns = 0
        agent_score = 0
        opp_score = 0

        # Capture deck info (peeking into env internal state)
        # Note: Accessing private members for diagnostic purposes
        vgs = env.game_state
        agent_deck_sample = vgs.batch_deck[0, :10].copy()

        while not done:
            action_masks = env.action_masks()
            action, _ = model.predict(obs, action_masks=action_masks, deterministic=True)
            obs, rewards, dones, infos = env.step(action)

            turns += 1
            done = dones[0]
            if done:
                inf = infos[0]
                agent_score = inf.get("terminal_score_agent", 0)
                opp_score = inf.get("terminal_score_opp", 0)

        match_stats.append(
            {"turns": turns, "agent_score": agent_score, "opp_score": opp_score, "deck_sample": agent_deck_sample}
        )

        if (i + 1) % 10 == 0:
            print(f" Completed {i + 1}/{num_games} matches...")

    # Aggregated Results
    avg_turns = np.mean([s["turns"] for s in match_stats])
    avg_agent = np.mean([s["agent_score"] for s in match_stats])
    avg_opp = np.mean([s["opp_score"] for s in match_stats])
    win_rate = np.mean([1 if s["agent_score"] > s["opp_score"] else 0 for s in match_stats]) * 100

    print("\n--- Summary Results ---")
    print(f"Avg Match Length (Turns): {avg_turns:.2f}")
    print(f"Avg Agent Score:         {avg_agent:.2f}")
    print(f"Avg Opponent Score:      {avg_opp:.2f}")
    print(f"Agent Win Rate:          {win_rate:.1f}%")

    print("\n--- Diagnostic Insights ---")
    print("1. 1v1 Parity: Opponent now uses step_player_single and can score points.")
    print("2. Deck Management: High turn counts (>60) indicate successful Deck Refresh logic.")
    print("3. Termination: Matches end when either player hits 3 points.")


if __name__ == "__main__":
    run_diagnostic_benchmark()
