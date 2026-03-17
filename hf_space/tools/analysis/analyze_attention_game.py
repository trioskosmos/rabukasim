import os
import sys

# Setup environment for ATTENTION mode
os.environ["OBS_MODE"] = "ATTENTION"
sys.path.append(os.getcwd())

from ai.loveca_features_extractor import LovecaFeaturesExtractor
from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def get_action_name(act_id):
    if act_id == 0:
        return "Pass"
    if 1 <= act_id <= 45:
        h_idx = (act_id - 1) // 3
        slot = (act_id - 1) % 3
        return f"Play Member (Hand[{h_idx}] -> Slot {slot})"
    if 46 <= act_id <= 60:
        h_idx = act_id - 46
        return f"Set Live (Hand[{h_idx}])"
    if 61 <= act_id <= 63:
        slot = act_id - 61
        return f"Activate Ability (Slot {slot})"
    if 64 <= act_id <= 69:
        idx = act_id - 64
        return f"Mulligan Toggle (Card {idx})"
    return f"Unknown Action ({act_id})"


def main():
    print("Initializing Environment...")
    env = VectorEnvAdapter(num_envs=1)

    checkpoint_path = "./checkpoints/vector/interrupted_model.zip"
    if not os.path.exists(checkpoint_path):
        # Try emergency crash checkpoint if interrupted is missing
        checkpoint_path = "./checkpoints/vector/crash_emergency.zip"
        if not os.path.exists(checkpoint_path):
            print("Error: No checkpoint found to verify.")
            return

    print(f"Loading Model from {checkpoint_path}...")
    custom_objects = {
        "features_extractor_class": LovecaFeaturesExtractor,
        "features_extractor_kwargs": dict(features_dim=256),
    }

    model = MaskablePPO.load(checkpoint_path, env=env, custom_objects=custom_objects)

    obs = env.reset()
    done = [False]
    step_count = 0
    total_reward = 0

    print("Running game simulation with detailed logging...")
    log_path = "attention_game_analysis.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("LovecaSim Attention Model - Complete Game Analysis\n")
        f.write("===============================================\n\n")

        while not done[0] and step_count < 200:
            # Get State Info from VectorGameState internal for better logging
            vgs = env.game_state
            phase_int = int(vgs.batch_global_ctx[0, 8])
            energy = int(vgs.batch_global_ctx[0, 5])
            score = int(vgs.batch_scores[0])
            opp_score = int(vgs.opp_scores[0])
            hand_size = int(vgs.batch_global_ctx[0, 3])

            # Predict action
            action_masks = env.action_masks()
            action, _states = model.predict(obs, action_masks=action_masks, deterministic=True)
            act_id = int(action[0])
            act_name = get_action_name(act_id)

            # Log State before Action
            f.write(f"--- Step {step_count:3} ---\n")
            f.write(f"Phase: {phase_int} | Score: {score}-{opp_score} | Energy: {energy} | Hand: {hand_size}\n")
            f.write(f"Action: {act_name}\n")

            # Step environment
            obs, reward, done, infos = env.step(action)

            f.write(f"Result: Reward {reward[0]:.4f}\n\n")

            total_reward += reward[0]
            step_count += 1

            # If we detect a loop (e.g. toggling mulligan), we'll eventually hit the limit.
            if done[0]:
                f.write(f"GAME OVER at Step {step_count}. Total Reward: {total_reward:.2f}\n")
                break

    print(f"Analysis complete. Log saved to {log_path}")


if __name__ == "__main__":
    main()
