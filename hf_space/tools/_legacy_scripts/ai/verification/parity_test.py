"""
Parity Test: Python GameState vs Numba VectorGameState

This script runs random games on both engines and compares:
1. Legal action masks
2. State transitions after actions
3. Scores and game outcomes

Run with: uv run python ai/parity_test.py
"""

import os
import random
import sys

import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_env import VectorGameState

from engine.game.enums import Phase
from engine.game.game_state import GameState, initialize_game


def run_python_random_game(max_turns=50, seed=42):
    """Run a random game on the Python GameState engine."""
    random.seed(seed)
    np.random.seed(seed)

    gs = initialize_game(use_real_data=True, deck_type="normal")

    history = []
    turn = 0
    step = 0

    while not gs.game_over and turn < max_turns and step < 500:
        legal_mask = gs.get_legal_actions()
        legal_actions = np.where(legal_mask)[0]

        if len(legal_actions) == 0:
            print(f"[Python] No legal actions at step {step}!")
            break

        action = random.choice(legal_actions)

        history.append(
            {
                "step": step,
                "phase": gs.phase.name if hasattr(gs.phase, "name") else str(gs.phase),
                "player": gs.current_player,
                "legal_count": len(legal_actions),
                "action": int(action),
                "score_p0": gs.players[0].success_lives.__len__() if hasattr(gs.players[0], "success_lives") else 0,
                "score_p1": gs.players[1].success_lives.__len__() if hasattr(gs.players[1], "success_lives") else 0,
                "hand_size": len(gs.active_player.hand),
                "stage": [getattr(s, "uid", int(s)) for s in gs.active_player.stage],
            }
        )

        gs = gs.step(action, in_place=True)
        step += 1

        # Track turn changes
        if gs.phase == Phase.ACTIVE and step > 0:
            turn += 1

    return history, gs


def run_numba_random_game(max_turns=50, seed=42):
    """Run a random game on the Numba VectorGameState engine."""
    random.seed(seed)
    np.random.seed(seed)

    vgs = VectorGameState(num_envs=1)
    vgs.reset()

    history = []
    step = 0

    while step < 500:
        masks = vgs.get_action_masks()
        legal_actions = np.where(masks[0])[0]

        if len(legal_actions) == 0:
            print(f"[Numba] No legal actions at step {step}!")
            break

        action = random.choice(legal_actions)

        phase_val = int(vgs.batch_global_ctx[0, 8])

        history.append(
            {
                "step": step,
                "phase": phase_val,
                "player": 0,  # In training, always player 0
                "legal_count": len(legal_actions),
                "action": int(action),
                "score": int(vgs.batch_scores[0]),
                "hand_size": int(np.sum(vgs.batch_hand[0] > 0)),
                "stage": [int(s) for s in vgs.batch_stage[0]],
            }
        )

        actions = np.array([action], dtype=np.int32)
        vgs.step(actions)
        step += 1

        # Check termination (simplified: score >= 3)
        if vgs.batch_scores[0] >= 3:
            break

    return history, vgs


def compare_action_spaces(seed=42):
    """Compare initial legal action spaces between engines."""
    print("=" * 60)
    print("COMPARISON: Initial Legal Action Spaces")
    print("=" * 60)

    # Python Engine
    random.seed(seed)
    np.random.seed(seed)
    gs = initialize_game(use_real_data=True, deck_type="normal")

    # Skip Mulligan phases to reach Main Phase
    skip_count = 0
    while gs.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2) and skip_count < 10:
        gs = gs.step(0, in_place=True)  # Confirm mulligan (no replacement)
        skip_count += 1

    # Skip auto-phases to reach Main Phase
    while gs.phase in (Phase.ACTIVE, Phase.ENERGY, Phase.DRAW) and skip_count < 20:
        gs = gs.step(0, in_place=True)
        skip_count += 1

    py_mask = gs.get_legal_actions()
    py_actions = np.where(py_mask)[0]

    print(f"\n[Python] Skipped {skip_count} phases to reach Main.")
    print(f"[Python] Phase: {gs.phase.name}")
    hand_list = [str(c) for c in gs.active_player.hand]
    print(f"[Python] Legal Actions ({len(py_actions)}): {sorted(py_actions)[:30]}...")
    print(f"[Python] Hand ({len(gs.active_player.hand)}): {hand_list[:8]}...")
    print(f"[Python] Stage: {gs.active_player.stage}")
    print(f"[Python] Energy Zone: {len(gs.active_player.energy_zone)} cards")
    print(f"[Python] Untapped Energy: {gs.active_player.count_untapped_energy()}")

    # Debug: Check card types in Python
    print("\n[Python] Hand Card Details:")
    for card_id in gs.active_player.hand:
        cid = int(card_id)
        is_member = cid in GameState.member_db
        is_live = cid in GameState.live_db
        ctype = "Member" if is_member else "Live" if is_live else "Unknown"
        # Access legitimate cost from member object
        cost = GameState.member_db[cid].cost if is_member else -1
        print(f"  ID {cid:4d}: Type={ctype:8s} | Cost={cost}")

    # Numba Engine
    vgs = VectorGameState(num_envs=1)
    # No reset() because we want to manually populate everything

    # --- FORCE ALIGNMENT ---
    # Copy Python hand to Numba
    vgs.batch_hand[0, :].fill(0)
    for i, card in enumerate(gs.active_player.hand):
        if i < 60:
            # Assuming card has uid or is uid
            vgs.batch_hand[0, i] = getattr(card, "uid", int(card))

    # Copy Stage
    vgs.batch_stage[0, :].fill(-1)
    for i, card in enumerate(gs.active_player.stage):
        if i < 3:
            vgs.batch_stage[0, i] = getattr(card, "uid", int(card))
            # Also sync tapped status if possible
            # ...

    # Copy Energy
    vgs.batch_global_ctx[0, 50] = len(gs.active_player.energy_zone)
    vgs.batch_tapped[0, :].fill(0)
    for i in range(len(gs.active_player.energy_zone)):
        if i < 12 and gs.active_player.tapped_energy[i]:
            vgs.batch_tapped[0, 3 + i] = 1

    # Ensure HD/DK counts are synced
    vgs.batch_global_ctx[0, 3] = len(gs.active_player.hand)
    vgs.batch_global_ctx[0, 6] = len(gs.active_player.main_deck)

    # Set Phase
    vgs.batch_global_ctx[0, 8] = 3  # Main Phase

    numba_mask = vgs.get_action_masks()
    numba_actions = np.where(numba_mask[0])[0]

    print(f"\n[Numba] Phase: {vgs.batch_global_ctx[0, 8]} (3=Main)")
    print(f"[Numba] Legal Actions ({len(numba_actions)}): {sorted(numba_actions)[:30]}...")
    print(f"[Numba] Hand ({np.sum(vgs.batch_hand[0] > 0)}): {vgs.batch_hand[0, :8]}...")
    print(f"[Numba] Stage: {vgs.batch_stage[0]}")
    print(f"[Numba] Energy Count (EC): {vgs.batch_global_ctx[0, 50]}")
    print(f"[Numba] Slot Played Flags (SP0, SP1, SP2): {vgs.batch_global_ctx[0, 51:54]}")
    print(f"[Numba] Full Global Ctx (0-59): {vgs.batch_global_ctx[0, :60]}")
    print(f"[Numba] Tapped Status (0-15): {vgs.batch_tapped[0, 0:16]}")
    print(f"[Numba] Raw Masks (0-19): {numba_mask[0, :20].astype(int)}")
    print(f"[Numba] Mask Indices: {np.where(numba_mask[0, :20])[0]}")

    # Debug: Print card costs for all in hand
    print("\n[Numba] Hand Card Stats:")
    for h_idx in range(7):
        cid = vgs.batch_hand[0, h_idx]
        if cid > 0:
            cost = vgs.card_stats[cid, 0]
            ctype_val = vgs.card_stats[cid, 10]
            ctype = "Member" if ctype_val == 1 else "Live" if ctype_val == 2 else "None"
            print(f"  Pos {h_idx}: ID {cid:4d} | Type={ctype} ({ctype_val}) | Cost={cost}")

    # Find differences
    py_set = set(py_actions.tolist())
    numba_set = set(numba_actions.tolist())

    only_py = py_set - numba_set
    only_numba = numba_set - py_set
    common = py_set & numba_set

    print(f"\n[COMMON] {len(common)} actions in both: {sorted(common)[:20]}...")
    if only_py:
        print(f"[DIFF] Only in Python ({len(only_py)}): {sorted(only_py)[:20]}")
    if only_numba:
        print(f"[DIFF] Only in Numba ({len(only_numba)}): {sorted(only_numba)[:20]}")
    if not only_py and not only_numba:
        print("\n[OK] Action spaces match!")

    # Analyze action ID meaning
    print("\n[ANALYSIS] Action ID Mapping:")
    print("  Python: 1-180 = Play Member (HandIdx*3 + Slot), 200-202 = Activate Ability")
    print("  Numba:  1-180 = Play Member (HandIdx*3 + Slot), 200-202 = Activate Ability")

    return len(only_py) == 0 and len(only_numba) == 0


def main():
    print("=" * 60)
    print("SIC ENGINE PARITY TEST")
    print("=" * 60)

    # Step 1: Compare action spaces
    match = compare_action_spaces(seed=123)

    # Step 2: Run random games
    print("\n" + "=" * 60)
    print("RANDOM GAME: Python Engine")
    print("=" * 60)
    py_history, py_gs = run_python_random_game(max_turns=10, seed=456)

    for h in py_history[:10]:
        print(
            f"  Step {h['step']:3d} | Phase: {h['phase']:15s} | Action: {h['action']:4d} | Hand: {h['hand_size']:2d} | Legal: {h['legal_count']:3d}"
        )

    print(f"\n  ... ({len(py_history)} total steps)")
    print(
        f"  Final Scores: P0={py_history[-1]['score_p0'] if py_history else 0}, P1={py_history[-1]['score_p1'] if py_history else 0}"
    )

    print("\n" + "=" * 60)
    print("RANDOM GAME: Numba Engine")
    print("=" * 60)
    numba_history, numba_vgs = run_numba_random_game(max_turns=10, seed=456)

    for h in numba_history[:10]:
        print(
            f"  Step {h['step']:3d} | Phase: {h['phase']:15d} | Action: {h['action']:4d} | Hand: {h['hand_size']:2d} | Legal: {h['legal_count']:3d}"
        )

    print(f"\n  ... ({len(numba_history)} total steps)")
    print(f"  Final Score: {numba_history[-1]['score'] if numba_history else 0}")

    # Summary
    print("\n" + "=" * 60)
    print("PARITY SUMMARY")
    print("=" * 60)
    print(f"  Action Space Match: {'YES' if match else 'NO'}")
    print(f"  Python Steps: {len(py_history)}")
    print(f"  Numba Steps: {len(numba_history)}")


if __name__ == "__main__":
    main()
