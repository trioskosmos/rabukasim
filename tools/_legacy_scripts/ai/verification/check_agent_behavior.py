import os
import sys

# Force root
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)

import glob
import traceback

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def check_behavior():
    trace_file = os.path.join(root, "game_trace.txt")
    print("--- Long Running Behavior Check (Diagnostic) ---")
    sys.stdout.flush()

    try:
        # 1. Find Latest Model
        checkpoint_dir = os.path.join(root, "checkpoints", "vector")
        list_of_files = glob.glob(os.path.join(checkpoint_dir, "*.zip"))
        if not list_of_files:
            print(f"No checkpoints found in {checkpoint_dir}!")
            return
        latest_file = max(list_of_files, key=os.path.getmtime)
        print(f"Loading Model: {latest_file}")
        sys.stdout.flush()

        try:
            model = MaskablePPO.load(latest_file, device="cpu")
            print("Model loaded as MaskablePPO.")
        except Exception as e:
            print(f"FAILED to load model: {e}")
            raise e
        sys.stdout.flush()

        # 2. Init Env
        print("Initializing Env...")
        sys.stdout.flush()
        env = VectorEnvAdapter(num_envs=1)
        print("Env initialized.")
        sys.stdout.flush()

        print("Resetting Env...")
        obs = env.reset()
        print("Env reset complete.")
        sys.stdout.flush()

        last_reported_turn = -1

        with open(trace_file, "w", encoding="utf-8") as f:
            print(f"Opened {trace_file} for writing.")
            sys.stdout.flush()
            f.write("--- Start of Long Game Trace (SIC 2025 Rules) ---\n")
            f.write(f"Model: {os.path.basename(latest_file)}\n\n")

            for s in range(2000):
                masks = env.game_state.get_action_masks()
                # DEBUG SHAPE
                if s == 0:
                    print(f"DEBUG: Mask Shape: {masks.shape}")
                    # print(f"DEBUG: Obs Shape: {obs.shape}")

                try:
                    # RESTORED PREDICT with Fix: Pass masks (2D)
                    action, _ = model.predict(obs, action_masks=masks, deterministic=True)
                except Exception as e:
                    print(f"CRASH during model.predict at step {s}: {e}")
                    f.write(f"\nCRASH during predict: {e}\n")
                    raise e

                # DEBUG: Print Action
                print(f"DEBUG: Action Selected: {action}")
                sys.stdout.flush()

                # State BEFORE
                ph = env.game_state.batch_global_ctx[0, 8]
                turn = env.game_state.batch_global_ctx[0, 54]
                v2p = {1: "ACTIVE", 2: "ENERGY", 3: "DRAW", 4: "MAIN", 8: "RESULT"}
                ph_str = v2p.get(ph, str(ph))
                ec = env.game_state.batch_global_ctx[0, 50]
                hand = env.game_state.batch_hand[0]
                hand_cards = [int(c) for c in hand if c > 0]
                score_agent = env.game_state.batch_scores[0]
                score_opp = env.game_state.opp_scores[0]

                # Console Summary Every 10 Turns
                if turn % 10 == 0 and turn != last_reported_turn:
                    print(f"[PROGRESS] Turn {turn} | Steps {s} | Score {score_agent}/{score_opp}")
                    sys.stdout.flush()
                    last_reported_turn = turn

                act = int(action[0])
                if act == 0:
                    act_str = "PASS"
                elif 1 <= act <= 180:
                    h_idx = (act - 1) // 3
                    slot = (act - 1) % 3
                    act_str = f"PLAY Member (HIdx {h_idx} -> Slot {slot})"
                elif 200 <= act <= 202:
                    act_str = f"ACTIVATE (S {act - 200})"
                elif 400 <= act <= 459:
                    act_str = f"PLAY LIVE (HIdx {act - 400})"
                else:
                    act_str = f"UNKNOWN ({act})"

                f.write(
                    f"S{s:03d} | T{turn:2d} | P{ph}({ph_str}) | EC{ec:2d} | Sc:{score_agent}/{score_opp} | Action: {act_str}\n"
                )
                f.flush()  # Force write to disk

                obs, rewards, dones, infos = env.step(action)

                # State AFTER
                new_score_agent = env.game_state.batch_scores[0]
                new_score_opp = env.game_state.opp_scores[0]

                if new_score_agent > score_agent or new_score_opp > score_opp:
                    print("\n!!! SUCCESS: SCORE ACHIEVED !!!")
                    print(f"Step {s} | Turn {turn} | Final Score: {new_score_agent}/{new_score_opp}")
                    f.write(f"\n!!! SCORE EVENT !!!\nNew Score: {new_score_agent}/{new_score_opp}\n")
                    f.write("--- Stopping Trace (Requirement Met) ---\n")
                    break

                if dones[0]:
                    print(f"[DONE] Game ended by terminal condition at turn {turn}.")
                    f.write(f"--- Episode Done at Step {s}. Info: {infos[0]}\n")
                    break

        print(f"Done. Trace produced in {trace_file}")

    except Exception:
        print("\n!!! CRASH DETECTED !!!")
        traceback.print_exc()


if __name__ == "__main__":
    check_behavior()
