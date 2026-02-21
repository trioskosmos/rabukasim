import glob
import os
import sys

import numpy as np
from sb3_contrib import MaskablePPO

# Ensure project root is in path
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def run_self_play():
    print("--- PPO Self-Play Verification ---")

    # 1. Config
    USE_LATEST = True
    MODEL_PATH = "checkpoints/vector/interrupted_model.zip"
    BATCH_SIZE = 50
    N_GAMES = 100

    if USE_LATEST:
        list_of_files = glob.glob("checkpoints/vector/*.zip")
        if list_of_files:
            MODEL_PATH = max(list_of_files, key=os.path.getmtime)
            print(f"Model: {MODEL_PATH}")

    # 2. Load Model
    print("Loading PPO Model...")
    model = MaskablePPO.load(MODEL_PATH, device="cpu")

    # 3. Init Raw VectorGameState (No Adapter, manually stepping for self-play)
    print(f"Initializing {BATCH_SIZE} environments...")
    env = VectorGameState(num_envs=BATCH_SIZE)
    env.reset()

    total_wins_p0 = 0
    total_wins_p1 = 0
    total_draws = 0
    games_played = 0

    num_batches = (N_GAMES + BATCH_SIZE - 1) // BATCH_SIZE

    for b in range(num_batches):
        env.reset()
        active = np.ones(BATCH_SIZE, dtype=bool)

        # Track if game ended in this batch loop
        batch_wins_p0 = np.zeros(BATCH_SIZE, dtype=bool)
        batch_wins_p1 = np.zeros(BATCH_SIZE, dtype=bool)
        batch_draws = np.zeros(BATCH_SIZE, dtype=bool)

        step_count = 0
        while np.any(active) and step_count < 150:  # Slightly longer for self-play
            # Player 0 Turn (Perspective 0)
            obs0 = env.get_observations(player_id=0)
            masks0 = env.get_action_masks(player_id=0)
            num_legal = np.sum(masks0[0])
            if step_count == 0:
                print(f"  Step {step_count}: {num_legal} legal actions.")

            act0_raw, _ = model.predict(obs0, action_masks=masks0, deterministic=True)
            act0 = act0_raw.astype(np.int32)

            # Player 1 Turn (Perspective 1)
            obs1 = env.get_observations(player_id=1)
            masks1 = env.get_action_masks(player_id=1)
            act1_raw, _ = model.predict(obs1, action_masks=masks1, deterministic=True)
            act1 = act1_raw.astype(np.int32)

            # Step both!
            env.step(act0, opp_actions=act1)

            # Detailed Logging for Turn 1-5
            if step_count < 5:
                # Get more context for P0
                stg0 = env.batch_stage[0]
                sc0 = env.batch_scores[0]
                ph0 = env.batch_global_ctx[0, 8]
                print(f"  T{step_count + 1} | P0 Act: {act0[0]} | Stage: {stg0} | Score: {sc0} | Ph: {ph0}")

            # Check for dones (Custom logic since no adapter)
            for i in range(BATCH_SIZE):
                if active[i]:
                    sc0 = env.batch_scores[i]
                    sc1 = env.opp_scores[i]

                    is_done = False
                    if sc0 >= 3 or sc1 >= 3:
                        is_done = True
                    elif env.turn >= 50:  # Shorten for speed in debug
                        is_done = True

                    if is_done:
                        active[i] = False
                        if sc0 >= 3 and sc0 > sc1:
                            batch_wins_p0[i] = True
                        elif sc1 >= 3 and sc1 > sc0:
                            batch_wins_p1[i] = True
                        else:
                            batch_draws[i] = True

            step_count += 1

        total_wins_p0 += np.sum(batch_wins_p0)
        total_wins_p1 += np.sum(batch_wins_p1)
        total_draws += np.sum(batch_draws)
        games_played += BATCH_SIZE
        print(f"Batch {b + 1} done. P0 Wins: {total_wins_p0}, P1 Wins: {total_wins_p1}, Draws: {total_draws}")

    with open("benchmarks/self_play_results.txt", "w") as f:
        f.write("\n--- Final Self-Play Results ---\n")
        f.write(f"Total Games: {games_played}\n")
        f.write(f"Player 0 Wins: {total_wins_p0}\n")
        f.write(f"Player 1 Wins: {total_wins_p1}\n")
        f.write(f"Draws: {total_draws}\n")

        # Analyze
        if total_wins_p0 + total_wins_p1 > 0:
            f.write("RESULT: Agent CAN win games when playing against itself.\n")
        else:
            f.write("RESULT: Agent fails to win even in self-play. Policy likely broken.\n")

    print("Results saved to benchmarks/self_play_results.txt")


if __name__ == "__main__":
    run_self_play()
