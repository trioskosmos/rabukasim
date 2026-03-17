import os
import sys

import numpy as np

# Ensure path is correct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.vector_env import VectorGameState

from engine.game.game_state import GameState
from engine.game.player_state import PlayerState


def verify_setup_parity():
    """Verify both engines initialize with 2 Live Cards and 6 Hand Cards."""
    print("TEST: Initial Setup Parity - START")

    # Python Engine Setup
    py_game = GameState()
    # Inject a known deck so start_game works
    # Members (1001-1048), Lives (2001-2012)
    deck_ids = list(range(1001, 1049)) + list(range(2001, 2013))

    # We must manually setup because Python GameState expects 'start_game' flow usually
    # handled by the Server or Test cases.
    # Emulate internal flow:
    from engine.models.card import LiveCard, MemberCard

    # Setup P1
    py_game.p1 = PlayerState(0)
    for cid in deck_ids:
        # Minimal mock cards
        if cid < 2000:
            c = MemberCard(
                card_id=cid,
                card_no="001",
                name="M",
                cost=1,
                hearts=np.zeros(7, dtype=np.int32),
                blade_hearts=np.zeros(7, dtype=np.int32),
                blades=1,
                groups=[],
                units=[],
                abilities=[],
                img_path="dummy.png",
                rare="C",
            )
            py_game.member_db[cid] = c
        else:
            c = LiveCard(
                card_id=cid,
                card_no="001",
                name="L",
                score=1,
                required_hearts=np.zeros(7, dtype=np.int32),
                abilities=[],
                groups=[],
                units=[],
                img_path="dummy.png",
                rare="C",
            )
            py_game.live_db[cid] = c

    import random

    py_game.p1.deck = list(deck_ids)
    random.shuffle(py_game.p1.deck)

    # Run Setup Rule manually for verification as reset_game doesn't exist publicly like this
    # 1. Place 2 Lives
    py_game.p1.live_zone.append(py_game.p1.deck.pop(0))
    py_game.p1.live_zone.append(py_game.p1.deck.pop(0))

    # 2. Draw 6
    for _ in range(6):
        py_game.p1.hand.append(py_game.p1.deck.pop(0))

    # Numba Engine
    # obs_mode is set via env var OBS_MODE
    print("Numba Engine: Initializing VectorGameState... (This may take a moment for JIT compilation)")
    numba_env = VectorGameState(num_envs=1)
    print("Numba Engine: Initialized. Resetting...")
    numba_env.reset()
    print("Numba Engine: Reset complete.")

    # Checks
    # 1. Live Cards
    py_p1_lives = [c for c in py_game.p1.live_zone if c]
    numba_p1_lives = numba_env.batch_live[0][:2]

    print(f"Python P1 Lives Count: {len(py_p1_lives)}")
    print(f"Numba P1 Lives Count: {np.count_nonzero(numba_env.batch_live[0])}")

    assert len(py_p1_lives) == 2, "Python failed to setup 2 Lives"
    assert np.count_nonzero(numba_env.batch_live[0]) == 2, "Numba failed to setup 2 Lives"

    # 2. Hand Size
    print(f"Python P1 Hand Size: {len(py_game.p1.hand)}")
    print(f"Numba P1 Hand Size: {np.count_nonzero(numba_env.batch_hand[0])}")

    assert len(py_game.p1.hand) == 6, "Python failed to setup 6 Hand Cards"
    assert np.count_nonzero(numba_env.batch_hand[0]) == 6, "Numba failed to setup 6 Hand Cards"

    print("PASS: Setup Parity\n")


def verify_mulligan_parity():
    """Verify Mulligan Phase transitions and Card Drawing."""
    print("TEST: Mulligan Phase Parity - START")

    # Numba Setup
    print("Numba Setup: Initializing VectorGameState...")
    env = VectorGameState(num_envs=1)
    print("Numba Setup: Resetting...")
    env.reset()

    # Check Phase is -1
    ph = int(env.batch_global_ctx[0, 8])
    print(f"Numba Initial Phase: {ph} (Expected -1)")
    assert ph == -1

    # Action: Toggle Card 0 (Action 300)
    # Should stay in Phase -1
    obs, rewards, dones, infos = env.step(np.array([300], dtype=np.int32))

    ph_after = int(env.batch_global_ctx[0, 8])
    flag = env.batch_global_ctx[0, 120]
    print(f"Numba Phase after Toggle: {ph_after} (Expected -1)")
    print(f"Numba Flag 0: {flag} (Expected 1)")

    assert ph_after == -1
    assert flag == 1

    # Action: Pass (Action 0)
    # Should Advance to Phase 0 (Opponent Mulligan)
    obs, rewards, dones, infos = env.step(np.array([0], dtype=np.int32))

    ph_next = int(env.batch_global_ctx[0, 8])
    print(f"Numba Phase after Pass: {ph_next} (Expected 0)")
    assert ph_next == 0

    print("PASS: Mulligan Parity\n")


if __name__ == "__main__":
    verify_setup_parity()
    verify_mulligan_parity()
