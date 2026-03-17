import glob
import os
import sys
import time

import numpy as np
from sb3_contrib import MaskablePPO

# Ensure project root is in path
sys.path.append(os.getcwd())

# Use the ADAPTER (Training Logic) instead of raw VectorGameState
from ai.vec_env_adapter import VectorEnvAdapter


def run_numba_tournament():
    print("--- Numba High-Speed Tournament (via Adapter) ---")

    # 1. Config
    USE_LATEST = True
    MODEL_PATH = "checkpoints/vector/final_model.zip"
    N_GAMES = 100
    BATCH_SIZE = 50  # Run 50 parallel games (2 batches for 100 games)

    # 2. Find Latest Model
    if USE_LATEST:
        list_of_files = glob.glob("checkpoints/vector/*.zip")
        if list_of_files:
            latest_file = max(list_of_files, key=os.path.getmtime)
            MODEL_PATH = latest_file
            print(f"Model: {MODEL_PATH}")
        else:
            print("No checkpoints found!")
            return

    # 3. Load Model
    print("Loading PPO Model...")
    try:
        # Load on CPU to avoid CUDA overhead for small batch inference if preferred,
        # or CUDA if available.
        model = MaskablePPO.load(
            MODEL_PATH, device="cuda" if np.mod(1, 1) == 0 else "cpu"
        )  # Logic check: np.mod is dummy
        # Use CPU for safety/simplicity unless heavy
        model = MaskablePPO.load(MODEL_PATH, device="cpu")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # 4. Init Vector Environment ADAPTER
    # This matches training logic exactly
    print(f"Games: {N_GAMES} (Batch Size: {BATCH_SIZE})")
    print("Initializing Vector Environment (Adapter)...")

    env = VectorEnvAdapter(num_envs=BATCH_SIZE)

    # 5. Loop
    total_wins = 0
    total_losses = 0
    total_draws = 0

    games_played = 0
    start_time = time.time()

    # We run (N_GAMES // BATCH_SIZE) iterations
    # If N_GAMES is not divisible, we might run extra.
    # Simple logic: Run whole batches.

    num_batches = (N_GAMES + BATCH_SIZE - 1) // BATCH_SIZE

    print("Starting Matches...")

    try:
        for b in range(num_batches):
            # Reset Adapter
            obs = env.reset()
            active_envs = np.ones(BATCH_SIZE, dtype=bool)
            batch_wins = np.zeros(BATCH_SIZE, dtype=bool)
            batch_losses = np.zeros(BATCH_SIZE, dtype=bool)
            batch_draws = np.zeros(BATCH_SIZE, dtype=bool)

            step_count = 0
            while np.any(active_envs) and step_count < 110:
                masks = env.game_state.get_action_masks()
                action_idxs, _ = model.predict(obs, action_masks=masks, deterministic=True)
                obs, rewards, dones, infos = env.step(action_idxs)

                for i in range(BATCH_SIZE):
                    if active_envs[i] and dones[i]:
                        active_envs[i] = False
                        info = infos[i]
                        if "terminal_score_agent" in info:
                            sc_agent = info["terminal_score_agent"]
                            sc_opp = info["terminal_score_opp"]
                        else:
                            sc_agent = 0
                            sc_opp = 0

                        if sc_agent >= 3 and sc_agent > sc_opp:
                            batch_wins[i] = True
                        elif sc_opp >= 3 and sc_opp > sc_agent:
                            batch_losses[i] = True
                        else:
                            batch_draws[i] = True

                step_count += 1

            total_wins += np.sum(batch_wins)
            total_losses += np.sum(batch_losses)
            total_draws += np.sum(batch_draws)

            games_played += BATCH_SIZE
            elapsed = time.time() - start_time
            fps = games_played / elapsed
            wr = (total_wins / games_played) * 100
            print(f"Completed {games_played}/{N_GAMES} games. (WR: {wr:.1f}%) Speed: {fps:.1f} games/s")
    except Exception as e:
        print(f"Tournament Crash: {e}")
        import traceback

        traceback.print_exc()
        return

    total_time = time.time() - start_time
    print(f"Time: {total_time:.2f}s")

    # Report
    print("==========================")
    print(f"Wins: {total_wins}")
    print(f"Losses: {total_losses}")
    print(f"Draws: {total_draws}")
    win_rate = (total_wins / games_played) * 100
    print(f"Win Rate: {win_rate:.2f}%")
    print("==========================")

    # Save
    with open("benchmarks/numba_tournament_results.txt", "w") as f:
        f.write(f"Model: {MODEL_PATH}\n")
        f.write(f"Wins: {total_wins}\n")
        f.write(f"Losses: {total_losses}\n")
        f.write(f"Draws: {total_draws}\n")
        f.write(f"Win Rate: {win_rate:.2f}%\n")

    # Markdown
    with open("benchmarks/tournament_results_formatted.md", "w") as f:
        f.write("# Tournament Results\n\n")
        f.write(f"**Model**: `{MODEL_PATH}`\n")
        f.write(f"**Wins**: {total_wins}\n")
        f.write(f"**Losses**: {total_losses}\n")
        f.write(f"**Draws**: {total_draws}\n")
        f.write(f"**Win Rate**: {win_rate:.2f}%\n")


if __name__ == "__main__":
    run_numba_tournament()
