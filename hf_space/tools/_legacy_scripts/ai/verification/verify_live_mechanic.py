import numpy as np
from ai.vector_env import VectorGameState

from engine.game.fast_logic import resolve_live_single


def verify_numba_live_mechanics():
    print("Initializing VectorEnv...")
    env = VectorGameState(num_envs=1)
    env.reset()

    # 1. Test Placement and Draw (Action 400)
    print("Testing Placement and Draw (Action 400)...")

    # Force a card into hand slot 0
    # p_h is [num_envs, 60]
    p_h = env.batch_hand
    p_h[0, 0] = 50  # Member ID 50
    env.batch_global_ctx[0, 3] = 1  # Update Hand Count
    env.batch_global_ctx[0, 6] = 40  # Ensure deck has cards
    env.batch_deck[0, 0] = 60  # Known card in deck

    initial_hand_count = env.batch_global_ctx[0, 3]
    initial_deck_count = env.batch_global_ctx[0, 6]

    # Apply Action 400 (Set Hand[0] to Live)
    actions = np.array([400], dtype=np.int32)

    print(f"Hand Row 0 before step: {env.batch_hand[0, :5]}")
    print(f"Action: {actions}")

    # We need to call step, but step does many things.
    # Let's call step(400)
    obs, rewards, dones, infos = env.step(actions)

    # Verify:
    # 1. Card 50 in Live Zone
    live_zone = env.batch_live[0]
    print(f"Live Zone: {live_zone}")
    assert 50 in live_zone, "Member card 50 not found in Live Zone!"

    # 2. Hand count should be same (1 used, 1 drawn)
    current_hand_count = env.batch_global_ctx[0, 3]
    print(f"Hand Count: {initial_hand_count} -> {current_hand_count}")
    assert current_hand_count == initial_hand_count, "Hand count check failed! (Should draw 1)"

    # 3. Deck count decreased
    current_deck_count = env.batch_global_ctx[0, 6]
    print(f"Deck Count: {initial_deck_count} -> {current_deck_count}")
    assert current_deck_count < initial_deck_count, "Deck count check failed! (Should decrease)"

    print("Placement Check Passed!")

    # 2. Test Cleanup in resolve_live_single
    print("\nTesting Cleanup of Member Card...")

    # Card 50 is in live zone from previous step.
    # Calling resolve_live_single on ID 50 should clear it.

    # We need to set up minimal args for resolve_live_single
    # It takes (i, live_id, batch_stage, batch_live, ...)

    # We can invoke it by triggering a PASS (Action 0) which calls resolve_live_single for all lives
    # game phase is implicitly handled by step, might need to force state.

    # But let's restart env to separate test

    # Manually setup for resolve_live_single
    # Use the arrays from env
    env.batch_live[0, 0] = 50  # Ensure 50 is there

    # Call directly
    # Note: We need card_stats. VectorEnv has it at self.card_stats

    resolve_live_single(
        0,
        50,
        env.batch_stage,
        env.batch_live,
        np.zeros(1, dtype=np.int32),
        env.batch_global_ctx,
        env.batch_deck,
        env.batch_hand,
        env.batch_trash,
        env.card_stats,
    )

    print(f"Live Zone after cleanup: {env.batch_live[0]}")
    assert env.batch_live[0, 0] == 0, "Member card 50 was NOT cleaned up!"

    # Verify it went to trash
    # Iterate trash to find 50
    trash_has_50 = False
    for k in range(env.batch_trash.shape[1]):
        if env.batch_trash[0, k] == 50:
            trash_has_50 = True
            break
    print(f"Trash has 50: {trash_has_50}")
    assert trash_has_50, "Member card 50 not found in Trash!"

    print("Cleanup Check Passed!")
    print("\nAll Numba Logic Verified.")


if __name__ == "__main__":
    verify_numba_live_mechanics()
