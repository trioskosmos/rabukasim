import random

import numpy as np
from ai.vector_env import VectorGameState

from engine.game.enums import Phase
from engine.game.game_state import GameState
from engine.models.card import LiveCard, MemberCard


def verify_lockstep():
    # 1. Setup Data
    if not GameState.member_db:
        import json

        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # Keys in cards_compiled.json are actually member_db and live_db
            m_stats = {}
            for k, v in data["member_db"].items():
                m_stats[int(k)] = MemberCard(**v)
            l_stats = {}
            for k, v in data["live_db"].items():
                l_stats[int(k)] = LiveCard(**v)
            GameState.initialize_class_db(m_stats, l_stats)

    members = GameState.member_db
    lives = GameState.live_db

    # 2. Initialize Environments
    py_env = GameState()
    vec_env = VectorGameState(num_envs=1)
    vec_env.reset()

    # 3. Synchronize Initial State
    verified_cards = list(members.keys())
    random.seed(42)
    random.shuffle(verified_cards)

    # Sync Decks
    deck_list = list(verified_cards[:60])
    py_env.players[0].main_deck = deck_list
    py_env.players[1].main_deck = [2000] * 60

    # 4. Initial Draw 6 (Before Mulligan)
    py_env.players[0].hand = []
    py_env._draw_cards(py_env.players[0], 6)

    # Sync Numba Hand
    vec_env.batch_hand[0].fill(0)
    for k, cid in enumerate(py_env.players[0].hand):
        vec_env.batch_hand[0, k] = cid

    # Sync Numba Deck (Remaining)
    np_deck = np.zeros(60, dtype=np.int32)
    py_deck_remaining = py_env.players[0].main_deck
    np_deck[: len(py_deck_remaining)] = py_deck_remaining
    vec_env.batch_deck[0] = np_deck

    vec_env.batch_global_ctx[0, 3] = len(py_env.players[0].hand)  # HD size
    vec_env.batch_global_ctx[0, 6] = len(py_env.players[0].main_deck)  # DK size

    # 5. Set Starting Phase to Mulligan
    py_env.phase = Phase.MULLIGAN_P1
    py_env.current_player = 0
    # Init Energy Deck for Python so it can draw energy
    py_env.players[0].energy_deck = [2000] * 10
    py_env.players[1].energy_deck = [2000] * 10
    # Match Start Energy (Rule 6.2.1.2) - Numba does this by default
    py_env.players[0].energy_zone = [2000] * 3
    py_env.players[1].energy_zone = [2000] * 3

    # Phase Map
    PHASE_MAP = {
        -1: "MULLIGAN_P1",
        0: "MULLIGAN_P2",
        1: "ACTIVE",
        2: "ENERGY",
        3: "DRAW",
        4: "MAIN",
        5: "LIVE_SET",
        6: "PERFORMANCE_P1",
        7: "PERFORMANCE_P2",
        8: "LIVE_RESULT",
    }

    print(f"Mulligan Initialized. Py Hand={py_env.players[0].hand}, Deck={len(py_env.players[0].main_deck)}")
    print(
        f"                    Vec Hand={[c for c in vec_env.batch_hand[0] if c > 0]}, Deck={vec_env.batch_global_ctx[0, 6]}"
    )

    discrepancies = 0
    with open("verify_log.txt", "w") as f:
        f.write("--- Starting Lockstep Verification ---\n")

    num_steps = 20
    for step in range(num_steps):
        # 0. Sync check: Explicitly ignore energy mismatch if it's just due to Numba starting at 3 vs Py at 0 (fixed above)

        # 1. Catch-up Numba if lagging (due to Granular Phases)
        loop_guard = 0
        while int(vec_env.batch_global_ctx[0, 8]) < int(py_env.phase) and int(py_env.phase) <= 4:
            v_ph = int(vec_env.batch_global_ctx[0, 8])
            # Only catch up if valid phase positive (don't skip mulligan -1->0 check manually here, handle in loop)
            # AND strictly if Numba is behind.
            if v_ph > 0 and v_ph < 4:
                msg = f"  [Catch-Up] Vec Phase {PHASE_MAP.get(v_ph, v_ph)} < Py {PHASE_MAP.get(int(py_env.phase), int(py_env.phase))}. Stepping 0 (Pass).\n"
                print(msg.strip(), flush=True)
                with open("verify_log.txt", "a") as f:
                    f.write(msg)
                vec_env.step(np.array([0], dtype=np.int32))
                loop_guard += 1
                if loop_guard > 5:
                    break
            else:
                break

        # 2. Pick an action
        py_mask = py_env.get_legal_actions()
        vec_mask = vec_env.get_action_masks()[0]

        # Check Mask Parity
        if not np.array_equal(py_mask, vec_mask):
            msg = f"[!] Mask Mismatch at Step {step} (Phase {PHASE_MAP.get(int(py_env.phase), int(py_env.phase))})\n"
            py_indices = np.where(py_mask)[0]
            vec_indices = np.where(vec_mask)[0]
            msg += f"    Py Legal:  {len(py_indices)} -> {py_indices[:15]}...\n"
            msg += f"    Vec Legal: {len(vec_indices)} -> {vec_indices[:15]}...\n"
            print(msg, flush=True)
            with open("verify_log.txt", "a") as f:
                f.write(msg)

            common_indices = np.intersect1d(py_indices, vec_indices)
            if len(common_indices) == 0:
                print("    CRITICAL: No common legal actions! Aborting.", flush=True)
                break
            action = int(common_indices[0])
        else:
            legal_indices = np.where(py_mask)[0]
            action = int(legal_indices[0]) if len(legal_indices) > 0 else 0

        py_ph_name = PHASE_MAP.get(int(py_env.phase), str(py_env.phase))
        print(f"--- Step {step} Start --- (Action {action}, Phase {py_ph_name})", flush=True)

        # 3. Step Both
        py_env.step(action, in_place=True)
        vec_env.step(np.array([action], dtype=np.int32))

        # 4. Compare State
        py_p = py_env.players[0]
        vec_h = vec_env.batch_hand[0]
        vec_ctx = vec_env.batch_global_ctx[0]
        vec_s = vec_env.batch_stage[0]
        vec_scores = vec_env.batch_scores[0]

        # Hand
        py_hand_sorted = sorted([int(c) for c in py_p.hand])
        vec_hand_sorted = sorted([int(c) for c in vec_h if c > 0])
        # Phase
        py_ph = int(py_env.phase)
        vec_ph = int(vec_ctx[8])
        # Deck Size
        py_dk = len(py_p.main_deck)
        vec_dk = int(vec_ctx[6])
        # Stage
        py_stage = [int(c) for c in py_p.stage]
        vec_stage = [int(c) for c in vec_s]
        # Energy
        py_en = py_p.count_untapped_energy()
        vec_en = int(vec_ctx[5])
        # Score
        py_score = py_p.score
        vec_score = int(vec_scores)

        matched = True
        log_msgs = []

        if py_hand_sorted != vec_hand_sorted:
            log_msgs.append(f"    [!] HAND: Py={py_hand_sorted}, Vec={vec_hand_sorted}")
            discrepancies += 1
            matched = False

        if py_ph != vec_ph:
            # Ignore phase mismatch if Python is P2 (Phases 1-4 for P2) or Battle (5-8) and Vec is waiting (2 or 4)
            # But here we flag it for the user log
            log_msgs.append(f"    [!] PHASE: Py={PHASE_MAP.get(py_ph, py_ph)}, Vec={PHASE_MAP.get(vec_ph, vec_ph)}")
            if py_ph != vec_ph:
                matched = False

        if py_dk != vec_dk:
            log_msgs.append(f"    [!] DECK: Py={py_dk}, Vec={vec_dk}")
            discrepancies += 1
            matched = False

        if py_stage != vec_stage:
            log_msgs.append(f"    [!] STAGE: Py={py_stage}, Vec={vec_stage}")
            discrepancies += 1
            matched = False

        if py_en != vec_en:
            log_msgs.append(f"    [!] ENERGY: Py={py_en}, Vec={vec_en}")
            discrepancies += 1
            matched = False

        if py_score != vec_score:
            log_msgs.append(f"    [!] SCORE: Py={py_score}, Vec={vec_score}")
            discrepancies += 1
            matched = False

        if not matched:
            msg = f"  Step {step} DESYNC:\n"
            for m in log_msgs:
                msg += m + "\n"
            print(msg, flush=True)
            with open("verify_log.txt", "a") as f:
                f.write(msg)
        else:
            msg = f"  Step {step} MATCH:\n"
            msg += f"    Py: Ph={PHASE_MAP.get(py_ph, py_ph)}, En={py_en}, Dk={py_dk}, Hand={len(py_hand_sorted)}\n"
            msg += (
                f"    Vec: Ph={PHASE_MAP.get(vec_ph, vec_ph)}, En={vec_en}, Dk={vec_dk}, Hand={len(vec_hand_sorted)}\n"
            )
            print(msg, flush=True)
            with open("verify_log.txt", "a") as f:
                f.write(msg)

        # Fast-Forward Python through Battle Phases (5+) AND Opponent Turn (P2)
        # Check if Python is P2 (current_player == 1) OR Phase > 4
        while int(py_env.phase) > 4 or py_env.current_player == 1:
            curr_p = py_env.current_player
            curr_ph = int(py_env.phase)
            msg = f"  [Fast-Forward] Py P{curr_p} Phase {PHASE_MAP.get(curr_ph, curr_ph)} -> Stepping 0...\n"
            print(msg.strip(), flush=True)
            with open("verify_log.txt", "a") as f:
                f.write(msg)

            py_env.step(0, in_place=True)

            # Stop if we return to P1 and Phase <= 4 (e.g. Active/Energy/Draw/Main)
            if py_env.current_player == 0 and int(py_env.phase) <= 4:
                msg = f"  [Fast-Forward] Reached P1 {PHASE_MAP.get(int(py_env.phase), int(py_env.phase))}\n"
                print(msg.strip(), flush=True)
                with open("verify_log.txt", "a") as f:
                    f.write(msg)

        if discrepancies > 15:
            print("Too many discrepancies. Stop.", flush=True)
            break

    print(f"--- Verification Ended. Total Discrepancies: {discrepancies} ---", flush=True)


if __name__ == "__main__":
    verify_lockstep()
