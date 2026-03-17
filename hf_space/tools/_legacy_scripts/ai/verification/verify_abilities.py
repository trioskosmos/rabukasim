import json

import numpy as np
from ai.vector_env import VectorGameState

from engine.game.enums import Phase
from engine.game.game_state import GameState
from engine.models.card import LiveCard, MemberCard


def verify_abilities():
    print("--- Starting Ability Verification ---")

    # 1. Load Data
    with open("verified_card_pool.json", "r", encoding="utf-8") as f:
        verified_codes = json.load(f)["verified_abilities"]

    compiled_data = None
    if not GameState.member_db:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            compiled_data = json.load(f)
            m_stats = {int(k): MemberCard(**v) for k, v in compiled_data["member_db"].items()}
            l_stats = {int(k): LiveCard(**v) for k, v in compiled_data["live_db"].items()}
            GameState.initialize_class_db(m_stats, l_stats)

    # Create Map: CardNo -> ID
    if compiled_data is None:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            compiled_data = json.load(f)

    code_to_id = {}
    for k, v in compiled_data["member_db"].items():
        if "card_no" in v:
            code_to_id[v["card_no"]] = int(k)

    test_ids = []
    for code in verified_codes:
        if code in code_to_id:
            test_ids.append(code_to_id[code])
        else:
            print(f"Warning: Verified code {code} not found in DB.")

    # 2. Init Environments
    py_env = GameState()
    vec_env = VectorGameState(num_envs=1)

    # Filter for Member cards only for "On Play" tests
    test_ids = [cid for cid in test_ids if cid in GameState.member_db]

    print(f"Testing {len(test_ids)} verified member cards...")

    failures = []

    for card_id in test_ids:
        card = GameState.member_db[card_id]

        # SKIP CONDITIONS:
        if not card.abilities:
            continue
        # Check first ability trigger
        ab = card.abilities[0]
        if ab.trigger != 1:
            # print(f"Skipping {card_id}: Trigger {ab.trigger} != 1")
            continue

        print(f"[Test] Card {card_id} ({card.name})...")

        # RESET
        vec_env.reset()
        py_env = GameState()  # Re-init to be safe/clean
        py_env.players[0].energy_zone = [2000] * 12  # Infinite Energy
        py_env.players[0].energy_deck = [2000] * 10
        py_env.phase = Phase.MAIN

        # SYNC INITIAL STATE
        # 1. Put card in hand
        py_env.players[0].hand = [card_id, 2000, 2000]  # Target + dummies
        py_env.player_id = 0
        py_env.current_player = 0

        # 2. Sync Numba
        vec_env.batch_global_ctx[0, 8] = 4  # MAIN
        vec_env.batch_global_ctx[0, 5] = 12  # Energy
        vec_env.batch_hand[0].fill(0)
        vec_env.batch_hand[0, 0] = card_id
        vec_env.batch_hand[0, 1] = 2000
        vec_env.batch_hand[0, 2] = 2000
        vec_env.batch_global_ctx[0, 3] = 3  # Hand Size

        # 3. ACTION: Play Card (Slot 0)
        # Python
        try:
            # We must manually pay cost or ensure cheat mode.
            # We set energy to 12 above.
            # Perform "Play" action logically:
            py_env.step(1)  # Play card at index 0 to slot 0?
            # Action logic: 1-180 -> HandIdx * 3 + Slot + 1
            # Index 0, Slot 0 -> 0 * 3 + 0 + 1 = 1
        except Exception as e:
            print(f"  [Py] Error: {e}")
            failures.append(f"{card_id}: Py Crash")
            continue

        # Numba
        try:
            vec_env.step(np.array([1], dtype=np.int32))
        except Exception as e:
            print(f"  [Vec] Error: {e}")
            failures.append(f"{card_id}: Vec Crash")
            continue

        # 4. COMPARE
        py_p = py_env.players[0]
        py_score = py_p.score

        vec_score = int(vec_env.batch_scores[0])

        # Simple Score Check
        if py_score != vec_score:
            print(f"  [Failure] Score Mismatch: Py={py_score}, Vec={vec_score}")
            failures.append(f"{card_id}: Score {py_score} vs {vec_score}")
        else:
            print(f"  [Success] Score Parity: {py_score}")

    print("\n--- Summary ---")
    if failures:
        print(f"Failures ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
    else:
        print("All tested cards passed!")


if __name__ == "__main__":
    verify_abilities()
