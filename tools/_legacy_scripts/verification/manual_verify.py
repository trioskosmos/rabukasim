import os
import sys

# Add local directory to path to find engine
sys.path.append(os.getcwd())

import numpy as np

from engine.game.game_state import GameState
from engine.models.card import LiveCard


def run_test():
    print("Initializing GameState...")
    gs = GameState()

    # Mock Live Cards
    l1 = LiveCard(card_id=1001, name="Live 1", score=1, required_hearts=np.zeros(7, dtype=np.int32), card_no="L1")
    l2 = LiveCard(card_id=1002, name="Live 2", score=2, required_hearts=np.zeros(7, dtype=np.int32), card_no="L2")
    GameState.live_db = {1001: l1, 1002: l2}
    GameState.member_db = {}

    print("--- Test 1: Tie with 1 card each ---")
    gs.players[0].passed_lives = [1001]
    gs.players[1].passed_lives = [1001]
    gs.players[0].live_score_bonus = 0
    gs.players[1].live_score_bonus = 0

    gs._do_live_result()

    print(f"P0 Score: {gs.players[0].score} (Expected 1)")
    print(f"P1 Score: {gs.players[1].score} (Expected 1)")
    if gs.players[0].score != 1 or gs.players[1].score != 1:
        print("FAIL Test 1")
    else:
        print("PASS Test 1")

    print("\n--- Test 2: Tie with 2 cards vs 1 card (Penalty Check) ---")
    gs = GameState()  # Reset
    gs.players[0].passed_lives = [1001, 1001]  # Score 2
    gs.players[1].passed_lives = [1002]  # Score 2

    gs._do_live_result()

    print(f"P0 Score: {gs.players[0].score} (Expected 0 - Penalty)")
    print(f"P1 Score: {gs.players[1].score} (Expected 1)")

    if gs.players[0].score != 0 or gs.players[1].score != 1:
        print("FAIL Test 2")
    else:
        print("PASS Test 2")

    print("\n--- Test 3: Win with multiple cards (Selection Check) ---")
    gs = GameState()
    gs.players[0].passed_lives = [1001, 1001]  # Score 2
    gs.players[1].passed_lives = [1001]  # Score 1

    gs._do_live_result()

    if len(gs.pending_choices) != 1:
        print(f"FAIL Test 3: Expected 1 pending choice, got {len(gs.pending_choices)}")
    else:
        print(f"Pending Choice: {gs.pending_choices[0][0]}")
        # Manually resolve
        print("Executing _handle_choice(600)...")
        gs._handle_choice(600)
        # Manually finish because _do_live_result returned early
        gs._finish_live_result()

        print(f"P0 Score: {gs.players[0].score} (Expected 1)")
        print(f"P1 Score: {gs.players[1].score} (Expected 0)")

        if gs.players[0].score != 1:
            print("FAIL Test 3")
        else:
            print("PASS Test 3")


run_test()
