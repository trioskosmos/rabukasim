import json

import numpy as np
from ai.gym_env import LoveLiveCardGameEnv

from engine.game.game_state import initialize_game


def test_auto_reset_on_opponent_win():
    print("--- Testing Auto-Reset on Opponent Win ---")
    env = LoveLiveCardGameEnv(deck_type="random_verified", opponent_type="random")
    obs, info = env.reset()

    # We want to simulate a situation where an opponent move ends the game.
    # This is hard to force naturally, but we can inspect the code logic or
    # mock the game state if needed.
    # However, we can simply run a few steps and see if any warnings appear.

    warnings_found = False
    import builtins

    original_print = builtins.print

    def mock_print(*args, **kwargs):
        nonlocal warnings_found
        msg = " ".join(map(str, args))
        if "WARNING: Step called after Game Over" in msg:
            warnings_found = True
        original_print(*args, **kwargs)

    builtins.print = mock_print

    try:
        for i in range(100):
            masks = env.action_masks()
            legal_indices = np.where(masks)[0]
            if len(legal_indices) == 0:
                break
            action = np.random.choice(legal_indices)
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated:
                print(f"Game ended at step {i}")
                # The env should have auto-reset, so 'terminated' is true but the next step is fresh.
                break
    finally:
        builtins.print = original_print

    if warnings_found:
        print("FAIL: Found 'Step called after Game Over' warnings!")
    else:
        print("SUCCESS: No warnings found during test run.")


def test_verified_pool_strictness():
    print("\n--- Testing Verified Pool Strictness ---")
    game = initialize_game(deck_type="random_verified")

    pool_path = "verified_card_pool.json"
    with open(pool_path, "r", encoding="utf-8") as f:
        pool = json.load(f)

    verified_nos = set(pool["verified_abilities"] + pool["vanilla_members"])
    verified_lives = set(pool["vanilla_lives"])

    all_fine = True
    for p in game.players:
        for cid in p.main_deck:
            if cid in game.member_db:
                card_no = game.member_db[cid].card_no
                if card_no not in verified_nos:
                    print(f"FAIL: Non-verified member card {card_no} found in deck!")
                    all_fine = False
            elif cid in game.live_db:
                card_no = game.live_db[cid].card_no
                if card_no not in verified_lives:
                    print(f"FAIL: Non-verified live card {card_no} found in deck!")
                    all_fine = False

    if all_fine:
        print("SUCCESS: All cards in 'random_verified' deck are from the verified pool.")


if __name__ == "__main__":
    test_auto_reset_on_opponent_win()
    test_verified_pool_strictness()
