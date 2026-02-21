import os
import sys

import numpy as np
from sb3_contrib import MaskablePPO

# Ensure we can import from project root
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def debug_numba_match(model_path):
    print("--- Debug Numba Match ---")
    print(f"Model: {model_path}")

    # 1. Load Model
    try:
        model = MaskablePPO.load(model_path, device="cpu")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # 2. Init Env (Batch Size 1)
    env = VectorGameState(1)
    env.reset()

    print("State initialized. Starting debugging loop...")
    print("Log format: [Turn] Phase | Hand | Action -> Mask | Reward | Score")

    # 3. Step Loop
    done = False
    turn = 1
    max_turns = 100

    # Log file
    with open("debug_match.log", "w", encoding="utf-8") as f:
        f.write("--- Debug Numba Match ---\n")

        while not done and turn <= max_turns:
            env.get_observations()
            obs = env.obs_buffer  # (1, 8192)
            masks = env.get_action_masks()  # (1, 2000)

            # Predict
            action_idx_raw, _ = model.predict(obs, action_masks=masks, deterministic=True)
            action_idx = action_idx_raw.astype(np.int32)
            action = action_idx[0]

            # Debug: Check dtype
            # print(f"Action Dtype: {action_idx_raw.dtype} -> {action_idx.dtype}")

            # Get State Info for Logging
            hand = env.batch_hand[0]
            valid_hand = hand[hand > 0]

            # Infer Phase from Mask
            phase_str = "UNKNOWN"
            if masks[0, 1:181].any():
                phase_str = "MAIN"  # Playing members
            elif masks[0, 400:460].any():
                phase_str = "LIVE_SET"
            elif masks[0, 1000:].any():
                phase_str = "PERFORMANCE"
            elif masks[0, 0] and not masks[0, 1:].any():
                phase_str = "FORCED_PASS"

            # Step
            # Note: VectorGameState doesn't return reward/done directly in step usually?
            # We have to calculate reward manually to see what it *would* be,
            # OR wrap it. But VectorGameState is raw.
            # Let's check scores before/after.

            score_before = env.batch_scores[0]
            env.step(action_idx)
            score_after = env.batch_scores[0]

            # Log
            log_line = f"T{turn:<3} | {phase_str:<10} | Hand: {len(valid_hand)} | Action: {action:<4} | Score: {score_before}->{score_after}"
            print(log_line)
            f.write(log_line + "\n")
            f.write(f"    Hand IDs: {valid_hand.tolist()}\n")

            if action == 0 and phase_str == "MAIN":
                f.write("    [!] Passed in MAIN phase. (Possibly no playable cards?)\n")

            # Win Check
            if score_after >= 3:
                print("VICTORY!")
                f.write("VICTORY!\n")
                done = True
            elif env.opp_scores[0] >= 3:
                print("DEFEAT!")
                f.write("DEFEAT!\n")
                done = True

            turn += 1

            # Optional: Slow down for viewing
            # time.sleep(0.1)


if __name__ == "__main__":
    import glob

    vector_dir = "checkpoints/vector"
    files = glob.glob(os.path.join(vector_dir, "*.zip"))
    latest = max(files, key=os.path.getmtime) if files else None

    if latest:
        debug_numba_match(latest)
    else:
        print("No checkpoints found.")
