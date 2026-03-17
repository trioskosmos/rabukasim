import os
import sys

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

os.environ["USE_FIXED_DECK"] = "ai/vanilla_deck.md"
os.environ["OBS_MODE"] = "COMPRESSED"
os.environ["GAME_REWARD_SCALE"] = "50.0"

import json

from ai.vector_env import VectorGameState


def trace_fixed_game():
    # Load card names for readability
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    card_names = {}
    for cid, cdata in db.get("member_db", {}).items():
        card_names[int(cid)] = cdata.get("name", "Unknown Member")
    for cid, cdata in db.get("live_db", {}).items():
        card_names[int(cid)] = cdata.get("name", "Unknown Live")

    print("=" * 60)
    print(" FIXED DECK TRAINING TRACE (GAME 1) ")
    print("=" * 60)

    env = VectorGameState(num_envs=1)
    env.reset()

    # helper to print state
    def print_state(env, step):
        hand = env.batch_hand[0]
        hand_names = [card_names.get(cid, f"ID:{cid}") for cid in hand if cid > 0]

        opp_hand = env.opp_hand[0]
        opp_hand_names = [card_names.get(cid, f"ID:{cid}") for cid in opp_hand if cid > 0]

        stage = env.batch_stage[0]
        stage_names = [card_names.get(cid, "Empty") for cid in stage]

        opp_stage = env.opp_stage[0]
        opp_stage_names = [card_names.get(cid, "Empty") for cid in opp_stage]

        energy = env.batch_global_ctx[0, 5]
        score = env.batch_scores[0]
        opp_score = env.opp_scores[0]
        phase = int(env.batch_global_ctx[0, 8])
        turns = int(env.batch_global_ctx[0, 54])

        print(f"\n--- STEP {step:02} | TURN {turns} | PHASE {phase} ---")
        print(f" AGENT  | Score: {score} | Energy: {energy} | Stage: {stage_names}")
        print(f"        | Hand: {hand_names}")
        print(f" OPP    | Score: {opp_score} | Stage: {opp_stage_names}")
        print(f"        | Hand count: {len([c for c in opp_hand if c > 0])}")

    print_state(env, 0)

    done = False
    step = 0
    # Increase limit to 500 steps to ensure we see the full game
    while not done and step < 500:
        step += 1
        mask = env.get_action_masks()[0]
        legal = np.where(mask == 1)[0]

        # Simple policy: pick first legal non-pass action if available
        if len(legal) > 1:
            action = legal[legal != 0][0]
        else:
            action = 0

        print(f"\n>> Agent chose action: {action}")
        obs, rewards, dones, infos = env.step(np.array([action], dtype=np.int32))

        print_state(env, step)
        if rewards[0] != 0:
            print(f" *** Reward: {rewards[0]:.2f} ***")

        done = dones[0]

    print("=" * 60)
    print(" TRACE COMPLETE ")
    print("=" * 60)


if __name__ == "__main__":
    trace_fixed_game()
