import os
import sys

import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.vec_env_adapter import VectorEnvAdapter


def train_verification():
    LOG_FILE = "training_protocol_log.txt"
    NUM_GAMES = 10

    print(f"Starting Verification: {NUM_GAMES} Games...")

    # Initialize VecEnvAdapter (Single Env for clarity)
    env = VectorEnvAdapter(num_envs=1, observation_space_dim=8192)
    obs = env.reset()

    with open(LOG_FILE, "w", encoding="utf-8", buffering=1) as f:
        f.write("# Training Protocol Verification Log\n")
        f.write("# Protocol: 48 Ability Members + 12 Lives. Finite Opponent.\n")
        f.write("=========================================================\n\n")

        # Verify Deck Composition (Inspect internal batch_deck)
        # Check first env
        deck = env.game_state.batch_deck[0]
        f.write("## Deck Composition Check (Game 1)\n")
        f.write(f"Deck IDs: {deck.tolist()}\n")

        # Count stats
        non_zero = np.count_nonzero(deck)
        f.write(f"Total Cards: {non_zero}\n")
        if non_zero != 60:
            f.write("FAIL: Deck size is not 60!\n")
        else:
            f.write("PASS: Deck size is 60.\n")

        # Check Opponent Hand (Finite logic)
        opp_hand = env.game_state.opp_hand[0]
        f.write("\n## Opponent Hand Check (Start)\n")
        f.write(f"Hand IDs: {opp_hand[:10].tolist()} ...\n")
        hand_count = np.count_nonzero(opp_hand)
        f.write(f"Hand Count: {hand_count} (Should be 5)\n\n")
        f.flush()  # Force flush for early visibility

        # Run Episodes
        total_rewards = 0
        total_turns = 0

        for game_idx in range(NUM_GAMES):
            f.write(f"--- Game {game_idx + 1} ---\n")
            game_done = False
            step_count = 0
            episode_reward = 0

            while not game_done:
                # Random Action for testing
                masks = env.game_state.get_action_masks()[0]
                valid_indices = np.where(masks)[0]

                if len(valid_indices) > 0:
                    action = np.random.choice(valid_indices)
                else:
                    action = 0  # Pass

                # Step
                env.step_async(np.array([action]))
                obs, rewards, dones, infos = env.step_wait()

                # Get current stats
                g_ctx = env.game_state.batch_global_ctx[0]
                phase = g_ctx[8]
                hand = env.game_state.batch_hand[0]
                stage = env.game_state.batch_stage[0]

                f.write(f"Step {step_count + 1}: Action {action}, Phase {phase}\n")
                f.write(f"  Ctx[0-9]: {g_ctx[:10].tolist()}\n")
                f.write(f"  Hand: {hand[:10].tolist()} ...\n")
                f.write(f"  Stage: {stage.tolist()}\n")

                r = rewards[0]
                episode_reward += r
                step_count += 1

                if r <= -4.0:
                    f.write(f"Step {step_count}: Turn Penalty Applied! Reward: {r}\n")
                if r >= 50.0:
                    f.write(f"Step {step_count}: LIVE BONUS! Reward: {r}\n")

                if step_count % 10 == 0:
                    f.write(f"Step {step_count}: Reward Sum: {episode_reward:.1f}, Current: {r:.1f}\n")
                    f.write(
                        f"  Agent Score: {env.game_state.batch_scores[0]}, Opp Score: {env.game_state.opp_scores[0]}\n"
                    )
                    f.write(f"  Deck: {env.game_state.batch_global_ctx[0, 6]}, Turn: {env.game_state.turn}\n")
                    f.flush()

                if dones[0]:
                    game_done = True
                    f.write(f"Game Over. Total Reward: {episode_reward}. Steps: {step_count}.\n")

                    # Use terminal scores from infos if available (handling auto-reset)
                    final_agent = env.game_state.batch_scores[0]
                    final_opp = env.game_state.opp_scores[0]

                    if "terminal_score_agent" in infos[0]:
                        final_agent = infos[0]["terminal_score_agent"]
                        final_opp = infos[0]["terminal_score_opp"]

                    f.write(f"Opponent Score: {final_opp}\n")
                    f.write(f"Agent Score: {final_agent}\n\n")

                    # Log Opponent Hand to ensure it changed (Cards played)
                    final_opp_hand = env.game_state.opp_hand[0]
                    f.write(f"Final Opp Hand Count: {np.count_nonzero(final_opp_hand)}\n")
                    f.flush()

            if game_idx < NUM_GAMES - 1:
                # Reset handled by step_wait auto-reset,
                # but for cleanly logging next game start stat:
                pass

    print(f"Done. Log written to {LOG_FILE}")


if __name__ == "__main__":
    train_verification()
