import os
import sys

# Ensure we can import ai modules
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from ai.vector_env import resolve_live_performance, step_opponent_vectorized, step_vectorized
from sb3_contrib import MaskablePPO


def manual_resolve_phases_logging(env):
    """
    Python version of resolve_auto_phases with Logging.
    Advances ONE phase step if possible, or loops until Main/End?
    Actually, let's step through it until Main Phase 3.
    """
    g_ctx = env.game_state.batch_global_ctx
    hand = env.game_state.batch_hand
    deck = env.game_state.batch_deck
    tapped = env.game_state.batch_tapped

    i = 0  # Env 0

    # We loop until we hit Phase 3 (Main) or Turn Limit triggers (handled elsewhere)
    # or we break to let agent act

    max_loops = 10
    loops = 0

    while loops < max_loops:
        ph = int(g_ctx[i, 8])

        if ph == 3:
            print("   [Phase Logic] In Main Phase (3). Waiting for Agent.")
            return  # Ready for agent

        print(f"   [Phase Logic] Processing Phase {ph}...")

        # End (0) -> Start (1)
        if ph == 0 or ph >= 4:
            print("   -> Transition: End Turn (0) -> Start Phase (1)")
            g_ctx[i, 8] = 1
            loops += 1
            continue

        # Start (1) -> Draw (2) + Un-tap
        if ph == 1:
            print("   -> Transition: Start Phase (1) -> Draw Phase (2) (Untapping Members)")
            tapped[i].fill(0)
            g_ctx[i, 8] = 2
            loops += 1
            continue

        # Draw (2) -> Main (3) + Draw Card
        if ph == 2:
            # Draw Logic
            top_card = 0
            deck_idx = -1
            # Find top card
            for d_idx in range(60):
                if deck[i, d_idx] > 0:
                    top_card = deck[i, d_idx]
                    deck_idx = d_idx
                    break

            if top_card > 0:
                print(f"   -> Draw Action: Drawing Card ID {top_card}")
                drawn = False
                for h_idx in range(60):
                    if hand[i, h_idx] == 0:
                        hand[i, h_idx] = top_card
                        deck[i, deck_idx] = 0

                        # Update Hand Count
                        hc = 0
                        for k in range(60):
                            if hand[i, k] > 0:
                                hc += 1
                        g_ctx[i, 3] = hc

                        # Update Deck Count
                        g_ctx[i, 6] -= 1
                        drawn = True
                        break
                if not drawn:
                    print("   -> Draw Failed: Hand Full!")
            else:
                print("   -> Draw Failed: Deck Empty!")

            print("   -> Transition: Draw Phase (2) -> Main Phase (3)")
            g_ctx[i, 8] = 3
            loops += 1
            continue

        loops += 1


def show_phases():
    print("--- Detailed Phase Debugger ---")
    model_path = "checkpoints/vector/interrupted_model.zip"

    print(f"Loading: {model_path}")
    env = VectorEnvAdapter(num_envs=1)

    try:
        model = MaskablePPO.load(model_path, env=env)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print("Resetting Environment...")
    env.reset()

    # Force Auto-Phase to get to Start for first turn if needed,
    # but let's just run our manual logic
    manual_resolve_phases_logging(env)

    print("\nStarting Interactive Game Logic:")
    print("--------------------------------")

    for step_num in range(100):  # Limit steps
        # 1. Agent Decision (Main Phase)
        # We need to compute masks ourselves because env.action_masks() uses current state
        masks = env.game_state.get_action_masks()
        obs = env.game_state.get_observations()  # Get current obs

        action, _ = model.predict(obs, action_masks=masks)
        action_id = action[0]

        # Log Pre-Action
        turn = env.game_state.turn
        score_before = env.game_state.batch_scores[0]
        hand = env.game_state.batch_hand[0]
        compact_hand = [c for c in hand if c > 0]

        print(f"\n[Turn {turn}] Phase 3 | Score: {score_before} | Action: {action_id}")
        print(f"   Hand: {compact_hand}")
        print(f"   Stage: {env.game_state.batch_stage[0]}")

        # 2. Apply Action (Vectorized)
        print(f"   -> Applying Action {action_id}...")
        step_vectorized(
            action,
            env.game_state.batch_stage,
            env.game_state.batch_energy_vec,
            env.game_state.batch_energy_count,
            env.game_state.batch_continuous_vec,
            env.game_state.batch_continuous_ptr,
            env.game_state.batch_tapped,
            env.game_state.batch_live,
            env.game_state.opp_tapped,
            env.game_state.batch_scores,
            env.game_state.batch_flat_ctx,
            env.game_state.batch_global_ctx,
            env.game_state.batch_hand,
            env.game_state.batch_deck,
            env.game_state.bytecode_map,
            env.game_state.bytecode_index,
        )

        # 2b. Opponent Step
        # print("   -> Opponent Step...")
        step_opponent_vectorized(
            env.game_state.opp_hand,
            env.game_state.opp_deck,
            env.game_state.opp_stage,
            env.game_state.opp_energy_vec,
            env.game_state.opp_energy_count,
            env.game_state.opp_tapped,
            env.game_state.opp_scores,
            env.game_state.batch_tapped,
            env.game_state.opp_global_ctx,
            env.game_state.bytecode_map,
            env.game_state.bytecode_index,
        )

        # 2c. Resolve Live Performance (Scoring)
        resolve_live_performance(
            env.game_state.num_envs,
            action,
            env.game_state.batch_stage,
            env.game_state.batch_live,
            env.game_state.batch_scores,
            env.game_state.batch_global_ctx,
            env.game_state.card_stats,
        )

        # Calculate Reward
        score_after = env.game_state.batch_scores[0]
        reward_calc = (score_after - score_before) * 50.0 - 5.0
        print(f"   Reward (Calc): {reward_calc}")

        # Check for Phase Wrap (0 -> End Turn)
        ph = env.game_state.batch_global_ctx[0, 8]
        if ph == 0:
            print("   -> Phase became 0 (End Turn).")
            # Handle Turn Increment logic from Env
            env.game_state.turn += 1

        # 3. Manual Phase Progression
        manual_resolve_phases_logging(env)

        # Check Done
        if score_after >= 3 or step_num >= 98:
            print("GAME OVER")
            break


if __name__ == "__main__":
    show_phases()
