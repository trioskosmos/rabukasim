import os
import sys

import numpy as np

# Setup
os.environ["OBS_MODE"] = "ATTENTION"
sys.path.append(os.getcwd())

from ai.vector_env import VectorGameState


def test_parity():
    print("=== Engine Parity Test (Python vs Numba) ===")

    # 1. Initialize Numba Vector Engine
    vgs = VectorGameState(num_envs=1)
    vgs.reset()

    # 2. Extract state to initialize Python Engine
    # Note: We need a way to force Python to match Numba's random deck
    # For now, let's just compare one step of Mulligan.

    def sync_python_to_numba(py_gs, env_idx=0):
        # Sync Hand
        hand_ids = vgs.batch_hand[env_idx]
        py_gs.p1.hand = [cid for cid in hand_ids if cid > 0]
        # Sync Deck
        deck_ids = vgs.batch_deck[env_idx]
        py_gs.p1.deck = [cid for cid in deck_ids if cid > 0]
        # Sync Live
        live_ids = vgs.batch_live[env_idx]
        py_gs.p1.live_zone = [cid for cid in live_ids if cid > 0]
        # Sync Stats
        py_gs.p1.energy = int(vgs.batch_global_ctx[env_idx, 5])
        py_gs.p1.score = int(vgs.batch_scores[env_idx])
        py_gs.phase = int(vgs.batch_global_ctx[env_idx, 8])

    # --- Phase: Mulligan ---
    print(f"\n[Phase {vgs.batch_global_ctx[0, 8]}] Testing Mulligan Toggle...")
    # Act: Select Card 2 for Mulligan (ID 64+2 = 66 in Attention)
    vgs.step(np.array([66]))
    print(f"Numba Flag[2]: {vgs.batch_global_ctx[0, 120 + 2]} (Expected 1)")

    # --- Phase: Main ---
    print("\n[Step] Transitioning to Main Phase...")
    # Pass Mulligan Agent
    vgs.step(np.array([0]))
    # Pass Mulligan Opponent (If exists)
    while vgs.batch_global_ctx[0, 8] < 4:
        vgs.step(np.array([0]))

    print(f"Current Phase: {vgs.batch_global_ctx[0, 8]} | Hand Size: {vgs.batch_global_ctx[0, 3]}")

    # --- Test Hand Shifting ---
    hand_before = vgs.batch_hand[0, :10].copy()
    print(f"Hand Before Play: {hand_before}")

    # Identify a Member card in hand[0] for play
    cid = vgs.batch_hand[0, 0]
    # In Attention mode, Play Member Hand[0] to Slot 0 is ID 1
    # Check if legal
    masks = vgs.get_action_masks()
    if masks[0, 1]:
        print("Executing Play Member (Hand[0] -> Slot 0)...")
        vgs.step(np.array([1]))
        hand_after = vgs.batch_hand[0, :10]
        print(f"Hand After Play:  {hand_after}")
        # Verify Shift: old hand[1] should now be hand[0]
        if hand_after[0] == hand_before[1] and hand_after[0] != 0:
            print("[SUCCESS] Hand Shifting Verified: Card 1 moved to Card 0.")
        else:
            print(f"[FAILURE] Hand Shifting Failed. hand[0] is {hand_after[0]}, expected {hand_before[1]}")
    else:
        print("[SKIP] Play Member Slot 0 not legal (Energy?)")

    # --- Test Set Live ---
    hand_before = vgs.batch_hand[0, :10].copy()
    cid = vgs.batch_hand[0, 0]
    # Set Live Hand[0] is ID 46
    if masks[0, 46]:
        print("\nExecuting Set Live (Hand[0])...")
        vgs.step(np.array([46]))
        hand_after = vgs.batch_hand[0, :10]
        live_after = vgs.batch_live[0, :5]
        print(f"Hand After Set: {hand_after}")
        print(f"Live After Set: {live_after}")
        if cid in live_after:
            print("[SUCCESS] Set Live Verified: Card moved to Live Zone.")
        else:
            print("[FAILURE] Set Live Failed. Card not found in Live Zone.")
    else:
        print("\n[SKIP] Set Live not legal (Zone full?)")


if __name__ == "__main__":
    test_parity()
