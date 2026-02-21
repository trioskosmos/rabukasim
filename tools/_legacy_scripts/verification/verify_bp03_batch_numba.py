from ai.vector_env import VectorGameState

from engine.game.fast_logic import resolve_live_single


def verify_bp03_cards_refined():
    print("Loading Card Data...")
    env = VectorGameState(num_envs=1)
    env.reset()
    card_stats = env.card_stats
    b_map = env.bytecode_map
    b_idx = env.bytecode_index

    # 1. Verify PL!-bp3-019-L (1001) - Differential Test
    print("\n--- Verifying PL!-bp3-019-L (1001) ---")

    # Scenario A: NO μ's cards in Live Zone
    env.reset()
    env.batch_live[0, 3] = 1001
    env.batch_stage[0, 0] = 50
    # Use empty deck to avoid volume icons
    env.batch_deck[0].fill(0)
    env.batch_global_ctx[0, 6] = 0  # DK=0

    score_no_muse = resolve_live_single(
        0,
        1001,
        env.batch_stage,
        env.batch_live,
        env.batch_scores,
        env.batch_global_ctx,
        env.batch_deck,
        env.batch_hand,
        env.batch_trash,
        card_stats,
        env.batch_continuous_vec,
        env.batch_continuous_ptr,
        b_map,
        b_idx,
    )

    # Scenario B: 2 μ's cards in Live Zone
    env.reset()
    env.batch_live[0, 3] = 1001
    env.batch_live[0, 4] = 2  # μ's member
    env.batch_live[0, 5] = 3  # μ's member
    env.batch_stage[0, 0] = 50
    env.batch_deck[0].fill(0)
    env.batch_global_ctx[0, 6] = 0

    score_with_muse = resolve_live_single(
        0,
        1001,
        env.batch_stage,
        env.batch_live,
        env.batch_scores,
        env.batch_global_ctx,
        env.batch_deck,
        env.batch_hand,
        env.batch_trash,
        card_stats,
        env.batch_continuous_vec,
        env.batch_continuous_ptr,
        b_map,
        b_idx,
    )

    print(f"Score (No μ's): {score_no_muse}")
    print(f"Score (With 2 μ's): {score_with_muse}")

    if score_with_muse == score_no_muse + 1:
        print("SUCCESS: Ability Triggered and Score Boosted by exactly 1!")
    else:
        print(f"FAILURE: Boost was {score_with_muse - score_no_muse}, expected 1.")

    # 2. Verify PL!-bp3-023-L (1006)
    print("\n--- Verifying PL!-bp3-023-L (1006) ---")
    env.reset()
    env.batch_live[0, 3] = 1006
    env.batch_stage[0].fill(1)  # 5 blades each -> 15 blades

    resolve_live_single(
        0,
        1006,
        env.batch_stage,
        env.batch_live,
        env.batch_scores,
        env.batch_global_ctx,
        env.batch_deck,
        env.batch_hand,
        env.batch_trash,
        card_stats,
        env.batch_continuous_vec,
        env.batch_continuous_ptr,
        b_map,
        b_idx,
    )

    found_effect = False
    for k in range(env.batch_continuous_ptr[0]):
        if env.batch_continuous_vec[0, k, 0] == 48:
            print(f"Found Reduction Effect: Value={env.batch_continuous_vec[0, k, 1]}")
            found_effect = True
            break

    if found_effect:
        print("SUCCESS: Heart Reduction Ability Triggered!")
    else:
        print("FAILURE: Heart Reduction Effect not found.")


if __name__ == "__main__":
    verify_bp03_cards_refined()
