import os
import sys

import torch

# Fix path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def trace_model():
    model_path = "checkpoints/vector/interrupted_model.zip"
    if not os.path.exists(model_path):
        print(f"Model {model_path} not found.")
        return

    print(f"Loading model: {model_path}")
    env = VectorEnvAdapter(num_envs=1)  # Just 1 env for tracing
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = MaskablePPO.load(model_path, env=env, device=device)

    print("Starting trace...")
    obs = env.reset()

    trace_file = "model_game_trace.txt"
    with open(trace_file, "w") as f:
        f.write("=== Model Trace Results ===\n")
        f.write(f"Model: {model_path}\n\n")

        for step in range(1000):  # Hard limit
            action_masks = env.action_masks()
            # Predict
            action, _ = model.predict(obs, action_masks=action_masks, deterministic=True)

            # Log current state summary (peek into context)
            ctx = env.game_state.batch_global_ctx[0]
            turn = ctx[54]
            phase = ctx[8]
            score = ctx[0]
            opp_score = env.game_state.opp_scores[0]
            hand_size = ctx[3]
            energy = ctx[5]

            f.write(
                f"Step {step} | Turn {turn} | Phase {phase} | Score {score}-{opp_score} | Hand {hand_size} | Energy {energy}\n"
            )
            f.write(f"  Action Selected: {action[0]}\n")

            # Step
            obs, rewards, dones, infos = env.step(action)

            f.write(f"  -> Reward: {rewards[0]:.2f}\n")

            if dones[0]:
                f.write("\n=== GAME OVER ===\n")
                f.write(
                    f"Final Score: Agent {infos[0].get('terminal_score_agent')} - {infos[0].get('terminal_score_opp')} Opponent\n"
                )
                break

    print(f"Trace saved to {trace_file}")


if __name__ == "__main__":
    trace_model()
