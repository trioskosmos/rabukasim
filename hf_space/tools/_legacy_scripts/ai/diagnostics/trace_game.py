import argparse
import json
import os
import sys

import numpy as np
import torch

# Fix path
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from sb3_contrib import MaskablePPO


def trace_game():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=str, default="checkpoints/vector/numba_ppo_6362624_steps.zip", help="Path to PPO model"
    )
    parser.add_argument("--opponent", type=str, default="random", choices=["random", "heuristic"], help="Opponent type")
    parser.add_argument("--output", type=str, default="game_trace.txt", help="Output file")
    args = parser.parse_args()

    # Load card names
    card_names = {}
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            db = json.load(f)
        for cid, cdata in db.get("member_db", {}).items():
            card_names[int(cid)] = cdata.get("name", "Unknown Member")
        for cid, cdata in db.get("live_db", {}).items():
            card_names[int(cid)] = cdata.get("name", "Unknown Live")
    except:
        print("Warning: Could not load card names.")

    opp_mode = 0 if args.opponent == "heuristic" else 1

    # 1 Environment
    env = VectorEnvAdapter(num_envs=1, opp_mode=opp_mode)

    print(" [Trace] Compiling functions...")
    env.reset()
    env.step(np.zeros(1, dtype=np.int32))
    print(" [Trace] Ready to play.")

    # Load Model
    model = None
    if os.path.exists(args.model):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading PPO model: {args.model} on {device}")
        model = MaskablePPO.load(args.model, env=env, device=device)
    else:
        print(f"Model {args.model} not found. Using Random Agent.")
        model = None

    obs = env.reset()
    done = False
    step = 0

    log_file = open(args.output, "w", encoding="utf-8")

    def log(msg):
        print(msg)
        log_file.write(msg + "\n")

    log(f"--- GAME START: PPO vs {args.opponent.upper()} ---")

    while not done and step < 200:
        step += 1

        # Get State Info
        state = env.game_state
        i = 0

        turn = int(state.batch_global_ctx[i, 54])
        phase = int(state.batch_global_ctx[i, 8])
        energy = state.batch_global_ctx[i, 5]
        score = state.batch_scores[i]
        opp_score = state.opp_scores[i]

        hand = [c for c in state.batch_hand[i] if c > 0]
        hand_n = [card_names.get(c, str(c)) for c in hand]

        stage = [card_names.get(c, "Empty") if c > 0 else "Empty" for c in state.batch_stage[i]]
        lives = [card_names.get(c, "Empty") if c > 0 else "Empty" for c in state.batch_live[i]]

        log(f"\n[STEP {step}] TURN {turn} | PHASE {phase}")
        log(f" SCORE: {score} - {opp_score} (Opp)")
        log(f" ENERGY: {energy}")
        log(f" HAND: {hand_n}")
        log(f" STAGE: {stage}")
        log(f" LIVES: {lives}")

        # Action
        action_masks = env.action_masks()
        if model:
            action, _ = model.predict(obs, action_masks=action_masks, deterministic=True)
        else:
            legal = np.where(action_masks[0])[0]
            action = [np.random.choice(legal)] if len(legal) > 0 else [0]

        act_id = action[0]
        log(f">> ACTION CHOSEN: {act_id}")

        obs, rewards, dones, infos = env.step(action)

        if rewards[0] != 0:
            log(f"   Reward: {rewards[0]:.2f}")

        done = dones[0]

        if done:
            inf = infos[0]
            log("\n--- GAME OVER ---")
            log(f" FINAL SCORE: {inf.get('terminal_score_agent', 0)} - {inf.get('terminal_score_opp', 0)}")
            log(
                f" RESULT: {'WIN' if inf.get('terminal_score_agent', 0) > inf.get('terminal_score_opp', 0) else 'LOSE'}"
            )

    log_file.close()
    print(f"Trace written to {args.output}")


if __name__ == "__main__":
    trace_game()
