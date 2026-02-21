import os
import sys

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from engine.game.game_state import initialize_game


def test_random_verified():
    print("Testing random_verified deck initialization...")
    try:
        game = initialize_game(deck_type="random_verified")
        print("Game initialized successfully.")
        print(f"Phase: {game.phase.name}")
        print(f"P0 Hand size: {len(game.players[0].hand)}")
        print(f"P0 Deck size: {len(game.players[0].main_deck)}")

        # Check if cards are actually from the pool
        import json

        with open("verified_card_pool.json", "r", encoding="utf-8") as f:
            pool = json.load(f)
        verified_nos = set(pool.get("verified_abilities", []) + pool.get("vanilla_members", []))

        p0_hand_nos = [game.member_db[cid].card_no for cid in game.players[0].hand if cid in game.member_db]
        print(f"P0 Hand Card Nos: {p0_hand_nos}")

        all_in_pool = all(c_no in verified_nos for c_no in p0_hand_nos)
        print(f"All hand cards in verified pool: {all_in_pool}")

        # Run 100 random steps to check for hangs
        print("Running 100 random steps...")
        for i in range(100):
            if game.is_terminal():
                print(f"Game ended at step {i}")
                break

            masks = game.get_legal_actions()
            indices = np.where(masks)[0]
            if len(indices) == 0:
                print(f"No legal actions at step {i}")
                break

            action = np.random.choice(indices)
            game.take_action(action)

            if i % 20 == 0:
                print(f"Step {i}: Phase {game.phase}")

        print("Test complete.")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_random_verified()
