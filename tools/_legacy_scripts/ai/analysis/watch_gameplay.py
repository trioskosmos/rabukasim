import os
import sys

# Ensure path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter


def get_phase_name(ph):
    phases = {0: "START/MULLIGAN", 1: "ACTIVE", 2: "ENERGY", 3: "DRAW", 4: "MAIN", 8: "LIVE_RESULT"}
    return phases.get(ph, f"PHASE_{ph}")


import glob

from ai.train_vectorized import ProgressMaskablePPO  # Ensure we use the custom class for compatibility


def load_latest_model():
    # Check historic first
    checkpoints = glob.glob("historiccheckpoints/*/*model.zip")
    if not checkpoints:
        # Check standard checkpoints
        checkpoints = glob.glob("checkpoints/vector/*.zip")

    if not checkpoints:
        return None

    latest_model = max(checkpoints, key=os.path.getctime)
    return latest_model


def watch_gameplay():
    print("=== WATCHING TRAINED AGENT GAMEPLAY ===")

    # 1. Load Model
    model_path = load_latest_model()
    if not model_path:
        print(" [Error] No checkpoints found!")
        return

    print(f" [Init] Loading Model: {model_path}")
    # Load with CPU to avoid VRAM overhead just for watching
    model = ProgressMaskablePPO.load(model_path, device="cpu")

    # 2. Initialize Env
    num_envs = 1
    # Ensure env matches model observation space?
    # Usually safer to create env same way as training
    env = VectorEnvAdapter(num_envs=num_envs)

    print("Resetting Environment...")
    obs = env.reset()

    # Access internal state for logging
    gs = env.game_state

    step_count = 0
    max_steps = 10000  # Safety break

    log_file = open("gameplay_visual.txt", "w", encoding="utf-8")

    def log(msg):
        print(msg)
        log_file.write(msg + "\n")

    last_score = -1
    last_opp_score = -1
    last_phase = -1

    log("\n--- Game Start ---")

    while step_count < max_steps:
        # Get Action Mask
        masks = env.game_state.get_action_masks()[0]

        # PREDICT ACTION
        action, _states = model.predict(obs, action_masks=masks, deterministic=True)
        # Using deterministic=True for "best" move

        # Execute Step
        obs, rewards, dones, infos = env.step(action)
        action = action[0]  # Unpack from batch

        # State Data
        ph = int(gs.batch_global_ctx[0, 8])
        score = gs.batch_scores[0]
        opp_score = gs.opp_scores[0]
        turn = gs.batch_global_ctx[0, 54]
        hand_count = gs.batch_global_ctx[0, 3]
        energy = gs.batch_global_ctx[0, 5]

        dk = gs.batch_global_ctx[0, 6]
        hd = gs.batch_global_ctx[0, 3]
        ctx_slice = gs.batch_global_ctx[0, :11]

        # Log all first 100 steps or state changes
        if step_count < 100 or action != 0 or ph != last_phase or score != last_score or opp_score != last_opp_score:
            log(
                f"[Step {step_count:3d}] Turn {turn:2d} | {get_phase_name(ph):12s} | Action: {action:3d} | score: {score} vs Opp: {opp_score} | Hand: {hd} | Deck: {dk} | Energy: {energy}"
            )
            # log(f"      Context: SC={ctx_slice[0]}, OS={ctx_slice[1]}, TR={ctx_slice[2]}, HD={ctx_slice[3]}, OH={ctx_slice[4]}, EN={ctx_slice[5]}, DK={ctx_slice[6]}, OT={ctx_slice[7]}, PH={ctx_slice[8]}")

            if dones[0]:
                log(f"      !!! TERMINAL STEP !!! Info: {infos[0]}")

            if action >= 1 and action <= 180:
                slot = (action - 1) % 3
                cid = gs.batch_stage[0, slot]
                log(f"      -> Played Member ID {cid} to Slot {slot}")
            elif action >= 400:
                log("      -> Played LIVE CARD!")

        last_phase = ph
        last_score = score
        last_opp_score = opp_score
        step_count += 1

        if dones[0]:
            log("\n--- GAME OVER ---")
            info = infos[0]
            # Use terminal scores from infos if available (pre-reset state)
            final_agent_score = info.get("terminal_score_agent", score)
            final_opp_score = info.get("terminal_score_opp", opp_score)

            if final_agent_score > final_opp_score:
                log(f"WINNER: AGENT! ({final_agent_score} - {final_opp_score})")
            elif final_opp_score > final_agent_score:
                log(f"WINNER: OPPONENT! ({final_opp_score} - {final_agent_score})")
            else:
                log(f"DRAW! ({final_agent_score} - {final_opp_score})")
            break

    if step_count >= max_steps:
        log("\nReached max steps without completion.")

    log_file.close()


if __name__ == "__main__":
    # Prevent buffer truncation in some shells
    import io
    import sys

    # Ensure UTF-8
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    watch_gameplay()
