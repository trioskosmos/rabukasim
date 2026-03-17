import os
import sys

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from ai.gym_env import LoveLiveCardGameEnv


def print_separator():
    print("-" * 60)


def decode_observation(obs):
    """Decode key parts of the IMAX Pro observation."""
    universe = []
    base = 100
    stride = 80

    locations = {1.0: "HAND", 2.0: "STG1", 2.1: "STG2", 2.2: "STG3", 4.0: "TRASH", 5.0: "LIVE", 6.0: "WON"}

    for i in range(80):
        idx = base + i * stride
        presence = obs[idx]
        if presence > 0.5:
            cid_norm = obs[idx + 1]
            cid = int(round(cid_norm * 2000))

            loc_val = obs[idx + 79]
            loc_str = "UNK"
            # Fuzzy match
            best_diff = 1.0
            for k, v in locations.items():
                diff = abs(loc_val - k)
                if diff < 0.05:
                    loc_str = v
                    break

            universe.append(f"Slot {i:02d}: ID {cid:04d} @ {loc_str:<5}")

    return universe


def main():
    print("Initializing Game Environment...")
    env = LoveLiveCardGameEnv(target_cpu_usage=1.0)

    obs, info = env.reset()
    game = env.game

    print_separator()
    print("GAME START - FULL SIMULATION")
    print(f"Player ID: {env.agent_player_id}")
    print(f"Deck Size: {len(game.players[0].main_deck)}")
    print(f"Hand Size: {len(game.players[0].hand)}")
    print_separator()

    step = 0
    while True:
        step += 1

        # 1. Show Game State (Truth)
        p = game.players[0]
        hand_ids = [int(c.card_id) if hasattr(c, "card_id") else int(c) for c in p.hand]
        stage_ids = [int(c) if c != -1 else -1 for c in p.stage]

        # 2. Decode Vision periodically
        if step % 5 == 1 or step == 1:
            print(f"\n[STEP {step}]")
            print("Engine State:")
            print(f"  Hand:  {hand_ids}")
            print(f"  Stage: {stage_ids}")
            print(f"  Lives: {len(p.success_lives)}")
            print(f"  Phase: {game.phase}")

            vision = decode_observation(obs)
            print("AI Vision (Sample):")
            for v in vision[:5]:  # Show first 5 slots
                print(f"  {v}")

            d_count = obs[7800 + 6] * 50
            print(f"  > Deck Count (Obs): {int(d_count)}")

        # 3. Action
        masks = env.action_masks()
        legal = np.where(masks)[0]
        play_candidates = [a for a in legal if a > 0]

        if play_candidates:
            # Pick valid card
            action = int(play_candidates[0])
            if step % 5 == 1:
                print(f"Action: PLAY_CARD {action}")
        else:
            action = 0
            if step % 5 == 1:
                print("Action: PASS")

        obs, reward, terminated, truncated, info = env.step(action)

        if terminated:
            print_separator()
            print(f"GAME OVER at Step {step}")
            print(f"Winner: {game.winner} Reward: {reward}")
            p = game.players[0]
            print(f"Final Lives: {len(p.success_lives)}")
            print(f"Opponent Lives: {len(game.players[1].success_lives)}")
            break

        # time.sleep(0.01) # fast

    print("\nFull Game Complete.")


if __name__ == "__main__":
    main()
