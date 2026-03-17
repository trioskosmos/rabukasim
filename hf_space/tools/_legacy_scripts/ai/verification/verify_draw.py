import os
import sys

import numpy as np

sys.path.append(os.getcwd())

from engine.game.fast_logic import resolve_bytecode, resolve_opcode
from engine.models.opcodes import Opcode

# Numba-safe constants for ContextIndex
CTX_VALUE = 1
G_P_HAND_SIZE = 3
G_P_DECK_SIZE = 6


def verify_draw():
    print("Verifying DRAW opcode...")

    # Mock Data
    flat_ctx = np.zeros(64, dtype=np.int32)
    global_ctx = np.zeros(128, dtype=np.int32)
    p_stage = np.full(3, -1, dtype=np.int32)
    p_deck = np.zeros(10, dtype=np.int32)
    p_hand = np.zeros(10, dtype=np.int32)
    p_stage_energy_vec = np.zeros((3, 32), dtype=np.int32)
    p_stage_energy_count = np.zeros(3, dtype=np.int32)
    p_continuous_effects_vec = np.zeros((32, 10), dtype=np.int32)
    p_tapped_members = np.zeros(3, dtype=np.int32)
    p_live_revealed = np.zeros(3, dtype=np.int32)
    opp_tapped_members = np.zeros(3, dtype=np.int32)

    # Setup
    global_ctx[G_P_DECK_SIZE] = 10
    global_ctx[G_P_HAND_SIZE] = 0
    flat_ctx[CTX_VALUE] = 2  # Draw 2

    print("Calling resolve_opcode(DRAW)...")
    resolve_opcode(
        int(Opcode.DRAW),
        flat_ctx,
        global_ctx,
        0,
        p_hand,
        p_deck,
        p_stage,
        p_stage_energy_vec,
        p_stage_energy_count,
        p_continuous_effects_vec,
        0,
        p_tapped_members,
        p_live_revealed,
        opp_tapped_members,
    )

    print(f"Hand: {global_ctx[G_P_HAND_SIZE]}")
    print(f"Deck: {global_ctx[G_P_DECK_SIZE]}")

    print("Calling resolve_bytecode(DRAW)...")
    bytecode = np.array([[int(Opcode.DRAW), 2, 0, 0]], dtype=np.int32)

    # Reset
    global_ctx[G_P_DECK_SIZE] = 10
    global_ctx[G_P_HAND_SIZE] = 0

    resolve_bytecode(
        bytecode,
        flat_ctx,
        global_ctx,
        0,
        p_hand,
        p_deck,
        p_stage,
        p_stage_energy_vec,
        p_stage_energy_count,
        p_continuous_effects_vec,
        0,
        p_tapped_members,
        p_live_revealed,
        opp_tapped_members,
    )
    print(f"Bytecode Hand: {global_ctx[G_P_HAND_SIZE]}")

    print("Verifying Done.")


if __name__ == "__main__":
    verify_draw()
