import numpy as np
from numba import njit, prange

from engine.game.fast_logic import (
    get_base_id,
    move_to_trash,
    resolve_bytecode,
    resolve_live_single,
    run_opponent_turn_loop,
    run_random_turn_loop,
)

# Global Context Indices
SC = 0
OS = 1
TR = 2
HD = 3
DI = 4
EN = 5
DK = 6
OT = 7
PH = 8
OD = 9
PV = 60


@njit(cache=True, parallel=True, fastmath=True)
def encode_observations_attention(
    num_envs,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    opp_global_ctx,
    turn_number,
    observations,
):
    for i in prange(num_envs):
        encode_observation_attention_single(
            i,
            batch_hand,
            batch_stage,
            batch_energy_count,
            batch_tapped,
            batch_scores,
            opp_scores,
            opp_stage,
            opp_tapped,
            card_stats,
            batch_global_ctx,
            batch_live,
            batch_opp_history,
            opp_global_ctx,
            turn_number,
            observations,
        )
    return observations
    """
    Attention-Based Observation Encoding (2240-dim).
    64-dim feature vector per card slot.
    """
    # Clear buffer
    observations.fill(0.0)

    # Constants
    FEAT = 64
    MAX_HAND = 15

    # Offsets (must match LovecaFeaturesExtractor slicing)
    HAND_START = 0  # 0 - 1024 (16 cards * 64)
    STAGE_START = 1024  # 1024 - 1216 (3 cards * 64)
    LIVE_START = 1216  # 1216 - 1600 (6 cards * 64)
    OPP_STAGE_START = 1600  # 1600 - 1792 (3 cards * 64)
    OPP_HIST_START = 1792  # 1792 - 2176 (6 cards * 64)
    GLOBAL_START = 2176  # 2176 - 2240 (64 scalars)

    for i in range(num_envs):
        # --- A. HAND (16 slots: 15 primary + 1 overflow) ---
        hand_count = 0
        for j in range(60):
            cid = batch_hand[i, j]
            if cid >= 0:
                bid = get_base_id(cid)
                if bid < card_stats.shape[0]:
                    base = HAND_START + hand_count * FEAT

                    # Encode card features
                    observations[i, base + 0] = 1.0  # Presence
                    observations[i, base + 1] = card_stats[bid, 10] / 2.0  # Type
                    observations[i, base + 2] = card_stats[bid, 0] / 10.0  # Cost
                    observations[i, base + 3] = card_stats[bid, 1] / 5.0  # Blades
                    observations[i, base + 6] = 1.0 / 5.0  # Location: Hand

                    # Hearts (indices 8-14)
                    for k in range(7):
                        if 12 + k < card_stats.shape[1]:
                            observations[i, base + 8 + k] = card_stats[bid, 12 + k] / 5.0

                    # Group (index 22-28)
                    raw_group = card_stats[bid, 11] if card_stats.shape[1] > 11 else 0
                    observations[i, base + 22 + (raw_group % 7)] = 1.0

                    # Abilities (indices 46-52)
                    for ab_offset in (20, 36, 48, 60):
                        if ab_offset < card_stats.shape[1]:
                            trig = card_stats[bid, ab_offset]
                            if trig == 7:
                                observations[i, base + 46] = 1.0  # Active
                            elif trig == 1 or trig == 2:
                                observations[i, base + 48] = 1.0  # Start
                            elif trig > 0:
                                observations[i, base + 47] = 1.0  # Auto

                    # Context
                    observations[i, base + 58] = hand_count / 10.0  # Position
                    observations[i, base + 59] = 1.0  # Mine

                    hand_count += 1

        # --- B. MY STAGE (3 slots) ---
        for slot in range(3):
            cid = batch_stage[i, slot]
            if cid >= 0:
                bid = get_base_id(cid)
                if bid < card_stats.shape[0]:
                    base = STAGE_START + slot * FEAT

                    observations[i, base + 0] = 1.0  # Presence
                    observations[i, base + 1] = card_stats[bid, 10] / 2.0  # Type
                    observations[i, base + 2] = card_stats[bid, 0] / 10.0  # Cost
                    observations[i, base + 3] = card_stats[bid, 1] / 5.0  # Blades
                    observations[i, base + 4] = 1.0 if batch_tapped[i, slot] > 0 else 0.0  # Tapped
                    observations[i, base + 6] = 2.0 / 5.0  # Location: Stage

                    for k in range(7):
                        if 12 + k < card_stats.shape[1]:
                            observations[i, base + 8 + k] = card_stats[bid, 12 + k] / 5.0

                    raw_group = card_stats[bid, 11] if card_stats.shape[1] > 11 else 0
                    observations[i, base + 22 + (raw_group % 7)] = 1.0

                observations[i, base + 58] = slot / 10.0
                observations[i, base + 59] = 1.0

        # --- C. LIVE ZONE (6 slots) ---
        # 0-2: Successful Lives, 3-5: Pending Lives
        for j in range(6):
            cid = batch_live[i, j]
            if cid >= 0:
                bid = get_base_id(cid)
                if bid < card_stats.shape[0]:
                    base = LIVE_START + j * FEAT

                    observations[i, base + 0] = 1.0
                    observations[i, base + 1] = card_stats[bid, 10] / 2.0
                    observations[i, base + 2] = card_stats[bid, 0] / 10.0
                    observations[i, base + 5] = bid / 2000.0
                    observations[i, base + 6] = (3.5 if j < 3 else 3.0) / 5.0  # Location: 3.5=Won, 3.0=Pending

                    for k in range(7):
                        if 12 + k < card_stats.shape[1]:
                            observations[i, base + 8 + k] = card_stats[bid, 12 + k] / 5.0

                observations[i, base + 58] = j / 10.0
                observations[i, base + 59] = 1.0

        # --- D. OPPONENT STAGE (3 slots) ---
        for slot in range(3):
            cid = opp_stage[i, slot]
            if cid >= 0:
                bid = get_base_id(cid)
                if bid < card_stats.shape[0]:
                    base = OPP_STAGE_START + slot * FEAT

                    observations[i, base + 0] = 1.0
                    observations[i, base + 1] = card_stats[bid, 10] / 2.0
                    observations[i, base + 2] = card_stats[bid, 0] / 10.0
                    observations[i, base + 3] = card_stats[bid, 1] / 5.0
                    observations[i, base + 4] = 1.0 if opp_tapped[i, slot] > 0 else 0.0
                    observations[i, base + 6] = 4.0 / 5.0  # Location: Opp Stage

                    for k in range(7):
                        if 12 + k < card_stats.shape[1]:
                            observations[i, base + 8 + k] = card_stats[bid, 12 + k] / 5.0

                observations[i, base + 58] = slot / 10.0
                observations[i, base + 59] = -1.0  # Opponent

        # --- E. OPPONENT HISTORY (6 slots) ---
        for h in range(6):
            cid = batch_opp_history[i, h]
            if cid >= 0:
                bid = get_base_id(cid)
                if bid < card_stats.shape[0]:
                    base = OPP_HIST_START + h * FEAT

                    observations[i, base + 0] = 1.0
                    observations[i, base + 1] = card_stats[bid, 10] / 2.0
                    observations[i, base + 2] = card_stats[bid, 0] / 10.0
                    observations[i, base + 6] = 5.0 / 5.0  # Location: History

                observations[i, base + 58] = h / 10.0
                observations[i, base + 59] = -1.0

        # --- F. GLOBAL SCALARS (64 dims) ---
        observations[i, GLOBAL_START + 0] = batch_scores[i] / 10.0  # My Score
        observations[i, GLOBAL_START + 1] = opp_scores[i] / 10.0  # Opp Score
        observations[i, GLOBAL_START + 2] = turn_number / 20.0  # Turn
        observations[i, GLOBAL_START + 3] = batch_global_ctx[i, 8] / 10.0  # Phase
        observations[i, GLOBAL_START + 4] = batch_global_ctx[i, 5] / 10.0  # Energy
        observations[i, GLOBAL_START + 5] = batch_global_ctx[i, 6] / 40.0  # Deck Size
        observations[i, GLOBAL_START + 6] = hand_count / 15.0  # Hand Size

        # Mulligan Choice Flags (Indices 120-125) -> Map to 50-55
        for k in range(6):
            observations[i, GLOBAL_START + 50 + k] = batch_global_ctx[i, 120 + k]

    return observations


@njit(cache=True, fastmath=True)
def encode_observation_attention_single(
    i,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    opp_global_ctx,
    turn_number,
    observations,
):
    """
    Attention-Based Encoding for Single Environment (Step Kernel).
    """
    # Clear buffer
    observations[i].fill(0.0)

    # Constants
    FEAT = 64
    MAX_HAND = 15

    # Offsets
    HAND_START = 0
    HAND_OVER_START = HAND_START + (MAX_HAND * FEAT)  # 960
    STAGE_START = HAND_OVER_START + FEAT  # 1024
    LIVE_START = STAGE_START + (3 * FEAT)  # 1216
    LIVE_SUCC_START = LIVE_START + (3 * FEAT)  # 1408
    OPP_STAGE_START = LIVE_SUCC_START + (3 * FEAT)  # 1600
    OPP_HIST_START = OPP_STAGE_START + (3 * FEAT)  # 1792
    GLOBAL_START = OPP_HIST_START + (6 * FEAT)  # 2176

    # --- A. HAND (16 slots: 15 primary + 1 overflow) ---
    hand_count = 0
    for j in range(60):
        cid = batch_hand[i, j]
        if cid > 0 and cid < card_stats.shape[0]:
            if hand_count < 16:  # 15 primary + 1 overflow
                base = HAND_START + hand_count * FEAT

                # Encode card features
                observations[i, base + 0] = 1.0  # Presence
                observations[i, base + 1] = card_stats[cid, 10] / 2.0  # Type
                observations[i, base + 2] = card_stats[cid, 0] / 10.0  # Cost
                observations[i, base + 3] = card_stats[cid, 1] / 5.0  # Blades
                observations[i, base + 5] = cid / 2000.0  # Card ID (New)
                observations[i, base + 6] = 1.0 / 5.0  # Location: Hand

                # Hearts (indices 8-14)
                for k in range(7):
                    if 12 + k < card_stats.shape[1]:
                        observations[i, base + 8 + k] = card_stats[cid, 12 + k] / 5.0

                # Group (index 22-28)
                raw_group = card_stats[cid, 11] if card_stats.shape[1] > 11 else 0
                observations[i, base + 22 + (raw_group % 7)] = 1.0

                # Abilities (indices 46-52)
                for ab_offset in (20, 36, 48, 60):
                    if ab_offset < card_stats.shape[1]:
                        trig = card_stats[cid, ab_offset]
                        if trig == 7:
                            observations[i, base + 46] = 1.0  # Active
                        elif trig == 1 or trig == 2:
                            observations[i, base + 48] = 1.0  # Start
                        elif trig > 0:
                            observations[i, base + 47] = 1.0  # Auto

                # Context
                observations[i, base + 58] = hand_count / 10.0  # Position
                observations[i, base + 59] = 1.0  # Mine

                hand_count += 1

    # --- B. MY STAGE (3 slots) ---
    for slot in range(3):
        cid = batch_stage[i, slot]
        if cid > 0 and cid < card_stats.shape[0]:
            base = STAGE_START + slot * FEAT

            observations[i, base + 0] = 1.0  # Presence
            observations[i, base + 1] = card_stats[cid, 10] / 2.0  # Type
            observations[i, base + 2] = card_stats[cid, 0] / 10.0  # Cost
            observations[i, base + 3] = card_stats[cid, 1] / 5.0  # Blades
            observations[i, base + 4] = 1.0 if batch_tapped[i, slot] > 0 else 0.0  # Tapped
            observations[i, base + 5] = cid / 2000.0  # Card ID (New)
            observations[i, base + 6] = 2.0 / 5.0  # Location: Stage

            for k in range(7):
                if 12 + k < card_stats.shape[1]:
                    observations[i, base + 8 + k] = card_stats[cid, 12 + k] / 5.0

            raw_group = card_stats[cid, 11] if card_stats.shape[1] > 11 else 0
            observations[i, base + 22 + (raw_group % 7)] = 1.0

            observations[i, base + 58] = slot / 10.0
            observations[i, base + 59] = 1.0

    # --- C. LIVE ZONE (6 slots) ---
    # 0-2: Successful Lives, 3-5: Pending Lives
    for j in range(6):
        cid = batch_live[i, j]
        if cid > 0 and cid < card_stats.shape[0]:
            base = LIVE_START + j * FEAT

            observations[i, base + 0] = 1.0
            observations[i, base + 1] = card_stats[cid, 10] / 2.0
            observations[i, base + 2] = card_stats[cid, 0] / 10.0
            observations[i, base + 5] = cid / 2000.0
            observations[i, base + 6] = (3.5 if j < 3 else 3.0) / 5.0  # Location: 3.5=Won, 3.0=Pending

            for k in range(7):
                if 12 + k < card_stats.shape[1]:
                    observations[i, base + 8 + k] = card_stats[cid, 12 + k] / 5.0

            observations[i, base + 58] = j / 10.0
            observations[i, base + 59] = 1.0

    # --- D. OPPONENT STAGE (3 slots) ---
    for slot in range(3):
        cid = opp_stage[i, slot]
        if cid > 0 and cid < card_stats.shape[0]:
            base = OPP_STAGE_START + slot * FEAT

            observations[i, base + 0] = 1.0
            observations[i, base + 1] = card_stats[cid, 10] / 2.0
            observations[i, base + 2] = card_stats[cid, 0] / 10.0
            observations[i, base + 3] = card_stats[cid, 1] / 5.0
            observations[i, base + 4] = 1.0 if opp_tapped[i, slot] > 0 else 0.0
            observations[i, base + 5] = cid / 2000.0  # Card ID (New)
            observations[i, base + 6] = 4.0 / 5.0  # Location: Opp Stage

            for k in range(7):
                if 12 + k < card_stats.shape[1]:
                    observations[i, base + 8 + k] = card_stats[cid, 12 + k] / 5.0

            observations[i, base + 58] = slot / 10.0
            observations[i, base + 59] = -1.0  # Opponent

    # --- E. OPPONENT HISTORY (6 slots) ---
    for h in range(6):
        cid = batch_opp_history[i, h]
        if cid > 0 and cid < card_stats.shape[0]:
            base = OPP_HIST_START + h * FEAT

            observations[i, base + 0] = 1.0
            observations[i, base + 1] = card_stats[cid, 10] / 2.0
            observations[i, base + 2] = card_stats[cid, 0] / 10.0
            observations[i, base + 5] = cid / 2000.0  # Card ID (New)
            observations[i, base + 6] = 5.0 / 5.0  # Location: History

            observations[i, base + 58] = h / 10.0
            observations[i, base + 59] = -1.0

    # --- F. GLOBAL SCALARS (64 dims) ---
    observations[i, GLOBAL_START + 0] = batch_scores[i] / 10.0  # My Score
    observations[i, GLOBAL_START + 1] = opp_scores[i] / 10.0  # Opp Score
    observations[i, GLOBAL_START + 2] = turn_number / 20.0  # Turn
    observations[i, GLOBAL_START + 3] = batch_global_ctx[i, 8] / 10.0  # Phase
    observations[i, GLOBAL_START + 4] = batch_global_ctx[i, 5] / 10.0  # Energy
    observations[i, GLOBAL_START + 5] = batch_global_ctx[i, 6] / 40.0  # Deck Size
    observations[i, GLOBAL_START + 6] = hand_count / 15.0  # Hand Size

    # Opponent Resources (New - Parity)
    observations[i, GLOBAL_START + 7] = opp_global_ctx[i, 5] / 10.0  # Opp Energy
    observations[i, GLOBAL_START + 8] = batch_global_ctx[i, 4] / 10.0  # Opp Hand (sync at idx 4)
    observations[i, GLOBAL_START + 9] = batch_global_ctx[i, 9] / 40.0  # Opp Deck (sync at idx 9)
    observations[i, GLOBAL_START + 10] = batch_global_ctx[i, 7] / 10.0  # Opp Trash (sync at idx 7)

    # Mulligan Choice Flags (Indices 120-125) -> Map to 50-55
    for k in range(6):
        observations[i, GLOBAL_START + 50 + k] = batch_global_ctx[i, 120 + k]

    return observations

    """
    IMAX Observation Encoding (Original 8192-dim).
    Zero-compromise perception.
    """


@njit(cache=True, fastmath=True)
def encode_observation_imax_single(
    i,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    turn_number,
    observations,
):
    """
    IMAX Observation Encoding (Original 8192-dim).
    Zero-compromise perception.
    """
    max_id_val = 2000.0
    STRIDE = 80
    TRAIT_SCALE = 2097152.0

    MY_UNIVERSE_START = 100
    OPP_START = 6500
    OPP_HISTORY_START = 6740
    VOLUMES_START = 7800
    SCORE_START = 8000

    observations[i].fill(0.0)

    # --- 1. METADATA ---
    ph = int(batch_global_ctx[i, 8])
    if ph == -1:
        observations[i, 3] = 1.0  # New index for -1? No, let's keep it simple.
        # Let's map -1 to index 4, 0-6 to 5-11
        observations[i, 4] = 1.0
    elif 0 <= ph <= 6:
        observations[i, 5 + ph] = 1.0

    observations[i, 6] = min(turn_number / 20.0, 1.0)

    # IS_SECOND Flag (Index 15)
    observations[i, 15] = batch_global_ctx[i, 10]
    observations[i, 16] = 1.0

    # Mulligan Selection Flags (120-125) -> Map to some unused space (e.g. 50-55)
    for k in range(6):
        observations[i, 50 + k] = batch_global_ctx[i, 120 + k]

    # --- 2. MY UNIVERSE ---
    u_idx = 0
    MAX_UNIVERSE = 80

    # A. HAND (Full 60)
    for j in range(60):
        cid = batch_hand[i, j]
        if cid > 0 and u_idx < MAX_UNIVERSE:
            base = MY_UNIVERSE_START + u_idx * STRIDE
            bid = get_base_id(cid)
            if bid < card_stats.shape[0]:
                for k in range(79):
                    observations[i, base + k] = card_stats[bid, k] / (50.0 if card_stats[bid, k] > 50 else 20.0)
                observations[i, base + 3] = card_stats[bid, 0] / 10.0
                observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE
            observations[i, base] = 1.0
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 79] = 1.0
            u_idx += 1

    # B. STAGE (3)
    for slot in range(3):
        cid = batch_stage[i, slot]
        if cid >= 0 and u_idx < MAX_UNIVERSE:
            base = MY_UNIVERSE_START + u_idx * STRIDE
            bid = get_base_id(cid)
            if bid < card_stats.shape[0]:
                for k in range(79):
                    observations[i, base + k] = card_stats[bid, k] / (50.0 if card_stats[bid, k] > 50 else 20.0)
                observations[i, base + 3] = card_stats[bid, 0] / 10.0
                observations[i, base + 4] = card_stats[bid, 1] / 5.0
                observations[i, base + 5] = card_stats[bid, 2] / 5.0
                observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE
            observations[i, base] = 1.0
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 2] = 1.0 if batch_tapped[i, slot] else 0.0
            observations[i, base + 14] = min(batch_energy_count[i, slot] / 5.0, 1.0)
            observations[i, base + 79] = 2.0 + (slot * 0.1)
            u_idx += 1

    # D. LIVE ZONE (5 slots in IMAX)
    for k in range(5):
        cid = batch_live[i, k]
        if cid > 0 and u_idx < MAX_UNIVERSE:
            base = MY_UNIVERSE_START + u_idx * STRIDE
            bid = get_base_id(cid)
            if bid < card_stats.shape[0]:
                for x in range(79):
                    observations[i, base + x] = card_stats[bid, x] / (50.0 if card_stats[bid, x] > 50 else 20.0)
                observations[i, base + 3] = card_stats[bid, 0] / 10.0
                observations[i, base + 5] = card_stats[bid, 2] / 5.0
                observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE
            observations[i, base] = 1.0
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 79] = 5.0
            u_idx += 1

    # --- 3. OPPONENT STAGE --- (3 slots at 6500)
    for slot in range(3):
        cid = opp_stage[i, slot]
        base = OPP_START + slot * STRIDE
        if cid >= 0:
            observations[i, base] = 1.0
            bid = get_base_id(cid)
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 2] = 1.0 if opp_tapped[i, slot] else 0.0
            if bid < card_stats.shape[0]:
                observations[i, base + 3] = card_stats[bid, 0] / 10.0
                observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE
            observations[i, base + 79] = 3.0 + (slot * 0.1)

    # --- 4. OPPONENT HISTORY --- (Full 12 at 6740)
    for k in range(12):
        cid = batch_opp_history[i, k]
        if cid > 0:
            base = OPP_HISTORY_START + k * STRIDE
            observations[i, base] = 1.0
            bid = get_base_id(cid)
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 79] = 4.0
            if bid < card_stats.shape[0]:
                for x in range(79):
                    observations[i, base + x] = card_stats[bid, x] / (50.0 if card_stats[bid, x] > 50 else 20.0)

    # --- 5. VOLUMES ---
    observations[i, VOLUMES_START] = batch_global_ctx[i, 6] / 50.0
    observations[i, VOLUMES_START + 1] = batch_global_ctx[i, 9] / 50.0
    observations[i, SCORE_START] = min(batch_scores[i] / 9.0, 1.0)
    observations[i, SCORE_START + 1] = min(opp_scores[i] / 9.0, 1.0)


@njit(parallel=True, cache=True, fastmath=True)
def encode_observations(
    num_envs,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    turn_number,
    observations,
):
    # Dispatch based on observation shape
    obs_dim = observations.shape[1]

    if obs_dim == 2240:
        encode_observations_attention(
            num_envs,
            batch_hand,
            batch_stage,
            batch_energy_count,
            batch_tapped,
            batch_scores,
            opp_scores,
            opp_stage,
            opp_tapped,
            card_stats,
            batch_global_ctx,
            batch_live,
            batch_opp_history,
            turn_number,
            observations,
        )
        return observations

    for i in range(num_envs):
        encode_observation_imax_single(
            i,
            batch_hand,
            batch_stage,
            batch_energy_count,
            batch_tapped,
            batch_scores,
            opp_scores,
            opp_stage,
            opp_tapped,
            card_stats,
            batch_global_ctx,
            batch_live,
            batch_opp_history,
            turn_number,
            observations,
        )
    return observations


@njit(cache=True, fastmath=True)
def encode_observation_standard_single(
    i,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    turn_number,
    observations,
):
    max_id_val = 2000.0
    STRIDE = 80
    TRAIT_SCALE = 2097152.0

    # New Layout for 2304-dim (Middle Ground) [Adjusted: 3 Live]
    # Metadata: 0-20
    MY_UNIVERSE_START = 100
    # Hand (12 * 80) = 960 -> End 1060
    # Stage (3 * 80) = 240 -> End 1300
    # Live (3 * 80) = 240 -> End 1540  <-- REDUCED TO 3
    OPP_START = 1540
    # Opp Stage (3 * 80) = 240 -> End 1780
    OPP_HISTORY_START = 1780
    # Opp History (5 * 80) = 400 -> End 2180

    # Offsets in array must match
    VOLUMES_START = 60

    # Reset buffer for this env
    observations[i].fill(0.0)

    # --- 1. METADATA ---
    observations[i, 5] = 1.0  # Phase (Main)
    observations[i, 6] = min(turn_number / 20.0, 1.0)

    # IS_SECOND Flag (Index 15)
    observations[i, 15] = batch_global_ctx[i, 10]
    observations[i, 16] = 1.0

    # --- 2. MY UNIVERSE ---

    # A. HAND (Limit to 12)
    current_hand_idx = 0
    hand_limit = 12
    for j in range(60):
        cid = batch_hand[i, j]
        if cid > 0:
            if current_hand_idx < hand_limit:
                base = MY_UNIVERSE_START + current_hand_idx * STRIDE

                # Flag as present
                bid = get_base_id(cid)
                observations[i, base] = 1.0
                observations[i, base + 1] = bid / max_id_val
                observations[i, base + 79] = 1.0  # Loc: Hand

                if bid < card_stats.shape[0]:
                    # Load Stats
                    for k in range(79):
                        observations[i, base + k] = card_stats[bid, k] / (50.0 if card_stats[bid, k] > 50 else 20.0)
                    observations[i, base + 3] = card_stats[bid, 0] / 10.0  # Cost
                    observations[i, base + 1] = bid / max_id_val
                    observations[i, base + 2] = 0.0
                    observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE

                current_hand_idx += 1
            else:
                pass

    # B. STAGE (3 slots)
    stage_base_start = 1060  # 100 + 12*80 = 1060
    for slot in range(3):
        cid = batch_stage[i, slot]
        base = stage_base_start + slot * STRIDE
        if cid >= 0:
            bid = get_base_id(cid)
            observations[i, base] = 1.0
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 2] = 1.0 if batch_tapped[i, slot] else 0.0
            observations[i, base + 14] = min(batch_energy_count[i, slot] / 5.0, 1.0)
            observations[i, base + 79] = 2.0 + (slot * 0.1)  # Loc: Stage

            if bid < card_stats.shape[0]:
                for k in range(79):
                    observations[i, base + k] = card_stats[bid, k] / (50.0 if card_stats[bid, k] > 50 else 20.0)
                observations[i, base + 3] = card_stats[bid, 0] / 10.0
                observations[i, base + 4] = card_stats[bid, 1] / 5.0
                observations[i, base + 5] = card_stats[bid, 2] / 5.0
                observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE

    # D. LIVE ZONE (3 slots)
    live_base_start = 1300  # 1060 + 3*80 = 1300
    for k in range(3):
        cid = batch_live[i, k]
        if cid > 0:
            base = live_base_start + k * STRIDE
            bid = get_base_id(cid)
            observations[i, base] = 1.0
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 79] = 5.0  # Loc: Live

            if bid < card_stats.shape[0]:
                for x in range(79):
                    observations[i, base + x] = card_stats[bid, x] / (50.0 if card_stats[bid, x] > 50 else 20.0)
                observations[i, base + 3] = card_stats[bid, 0] / 10.0
                observations[i, base + 5] = card_stats[bid, 2] / 5.0
                observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE

    # --- 3. OPPONENT STAGE --- (3 slots at 1540)
    # OPP_START = 1540
    for slot in range(3):
        cid = opp_stage[i, slot]
        base = OPP_START + slot * STRIDE
        if cid >= 0:
            observations[i, base] = 1.0
            bid = get_base_id(cid)
            observations[i, base + 1] = bid / max_id_val
            observations[i, base + 2] = 1.0 if opp_tapped[i, slot] else 0.0
            observations[i, base + 79] = 3.0 + (slot * 0.1)

            if bid < card_stats.shape[0]:
                observations[i, base + 3] = card_stats[bid, 0] / 10.0
                observations[i, base + 11] = card_stats[bid, 11] / TRAIT_SCALE
                for k in range(20, 36):
                    val = card_stats[bid, k]
                    scale = 50.0 if val > 50 else 10.0
                    observations[i, base + k] = val / scale

    # --- 4. OPPONENT HISTORY --- (Limit to 5)
    # OPP_HISTORY_START = 1780
    hist_limit = 5
    for k in range(12):  # Buffer has 12, but we only show 5
        if k >= hist_limit:
            break

        cid = batch_opp_history[i, k]
        if cid > 0:
            base = OPP_HISTORY_START + k * STRIDE
            observations[i, base] = 1.0
            observations[i, base + 1] = cid / max_id_val
            observations[i, base + 79] = 4.0

            if cid < card_stats.shape[0]:
                for x in range(79):
                    observations[i, base + x] = card_stats[cid, x] / (50.0 if card_stats[cid, x] > 50 else 20.0)
                observations[i, base + 3] = card_stats[cid, 0] / 10.0
                observations[i, base + 5] = card_stats[cid, 2] / 5.0
                observations[i, base + 11] = card_stats[cid, 11] / TRAIT_SCALE

    # --- 5. VOLUMES --- (Put at 60-70 range in Metadata or at end?)
    # We have empty space at 20-50...
    observations[i, 40] = batch_global_ctx[i, 6] / 50.0  # My Deck
    observations[i, 41] = batch_global_ctx[i, 9] / 50.0  # Opp Deck
    observations[i, 42] = batch_global_ctx[i, 3] / 20.0  # My Hand
    observations[i, 43] = batch_global_ctx[i, 2] / 50.0  # My Trash
    observations[i, 44] = batch_global_ctx[i, 4] / 20.0  # Opp Hand
    observations[i, 45] = batch_global_ctx[i, 7] / 50.0  # Opp Trash

    # --- 6. ONE-HOT PHASE ---
    ph = int(batch_global_ctx[i, 8])
    if ph == -1:
        observations[i, 19] = 1.0  # Index for -1
    elif 0 <= ph <= 6:
        observations[i, 20 + ph] = 1.0

    # Mulligan Selection Flags (120-125) -> Map to 50-55
    for k in range(6):
        observations[i, 50 + k] = batch_global_ctx[i, 120 + k]

    # --- 7. SCORES ---
    observations[i, 30] = min(batch_scores[i] / 9.0, 1.0)
    observations[i, 31] = min(opp_scores[i] / 9.0, 1.0)


@njit(cache=True, fastmath=True)
def encode_observation_compressed_single(
    i,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    turn_number,
    observations,
):
    # Compressed Layout (Stride 10)
    # 0. Cost (Normalized)
    # 1. Color (1-6) / 6.0
    # 2. Main Value / 50.0
    # 3. Sec Value / 50.0
    # 4. Target / 20.0
    # 5. Traits (Bitmask / 1M)
    # 6. Type (Unit/Group/Live)
    # 7. Tapped (1.0/0.0)
    # 8. Location ID (1=Hand, 2=Stage, 3=OppStage, 4=History)
    # 9. ID (Normalized)

    STRIDE = 10
    MY_UNIVERSE_START = 20

    # Hand (10 cards max) -> 100 dims
    # Stage (3 cards) -> 30 dims
    # Live (3 cards) -> 30 dims
    # Opp Stage (3 cards) -> 30 dims
    # Opp History (5 cards) -> 50 dims
    # Total Universe = ~240 dims.
    # Metadata = 20 dims.
    # Total ~260-300 dims. Padding to 512.

    observations[i].fill(0.0)

    # Metadata
    observations[i, 0] = min(turn_number / 20.0, 1.0)
    observations[i, 1] = min(batch_scores[i] / 9.0, 1.0)
    observations[i, 2] = min(opp_scores[i] / 9.0, 1.0)

    # IS_SECOND Flag (Index 9 - Replacing PH=5 slot)
    observations[i, 9] = batch_global_ctx[i, 10]
    # Let's put it at index 3 instead of PH -1 flag?
    # If PH=-1, we know based on Turn=1 and Phase=0 encoding?
    # Let's use Index 9. If PH=5, map it to 8?
    # Let's just squeeze it into the normalized floats.
    # Index 15 is unused in Compressed? 14-19 are Mull flags.
    # Let's use Index 19. (Assume 5 mull flags enough? No need 6).
    # Let's use Index 46 (Opp Trash Volume is in standard).
    # Compressed METADATA is only 0-19.
    # Let's encode it as sign of Turn Number? No.
    # Let's put it at index 0 (Turn Number).
    # If Second, Turn Number is negative? (min(turn/20, 1.0) * -1).
    # Easier: Use Index 3. If Phase is -1, set Index 3 = 1.0.
    # If Phase != -1, Index 3 can be IS_SECOND?
    # No that's confusing.

    # DECISION: Reuse Index 18 (5th Mull Flag).
    # 6th mull flag (idx 125) is rarely used?
    # Better: Steal Index 13 (Opp Hand Volume). Opp Hand Volume is less critical than Order?
    # No, Opp Hand Volume is critical for timing.
    # Let's use Index 9 (PH=5). PH=5 is rarely reached in training (usually play main 4).
    observations[i, 9] = batch_global_ctx[i, 10]

    # Phase One-Hot
    ph = int(batch_global_ctx[i, 8])
    if ph == -1:
        observations[i, 3] = 1.0
    elif 0 <= ph <= 6:
        observations[i, 4 + ph] = 1.0

    # Mulligan Flags (120-125) -> Map to 14-19 (unused)
    for k in range(6):
        observations[i, 14 + k] = batch_global_ctx[i, 120 + k]

    # Volumes
    observations[i, 10] = batch_global_ctx[i, 6] / 50.0  # My Deck
    observations[i, 11] = batch_global_ctx[i, 9] / 50.0  # Opp Deck
    observations[i, 12] = batch_global_ctx[i, 3] / 20.0  # My Hand
    observations[i, 13] = batch_global_ctx[i, 4] / 20.0  # Opp Hand

    # --- UNIVERSE ---
    ptr = MY_UNIVERSE_START

    # Helper for Stat Packing
    # We can't use inner function in numba njit easily if it relies on closures?
    # Just inline or straightforward loop.

    # A. HAND (10 Max)
    limit = 10
    count = 0
    for j in range(60):
        if count >= limit:
            break
        cid = batch_hand[i, j]
        if cid > 0:
            base = ptr + count * STRIDE
            observations[i, base + 9] = cid / 2000.0
            observations[i, base + 8] = 1.0  # Hand
            if cid < card_stats.shape[0]:
                observations[i, base + 0] = card_stats[cid, 0] / 10.0  # Cost
                observations[i, base + 1] = card_stats[cid, 3] / 6.0  # Color
                # Use ability block 1 for main val
                observations[i, base + 2] = card_stats[cid, 21] / 50.0  # Trig/Type? No, raw stats
                # Let's map Blade/Hearts
                observations[i, base + 2] = card_stats[cid, 1] / 5.0  # Blades
                observations[i, base + 3] = card_stats[cid, 2] / 5.0  # Hearts
                observations[i, base + 5] = card_stats[cid, 11] / 2097152.0
            count += 1

    ptr += limit * STRIDE  # +100

    # B. STAGE (3)
    for slot in range(3):
        cid = batch_stage[i, slot]
        base = ptr + slot * STRIDE
        if cid >= 0:
            observations[i, base + 9] = cid / 2000.0
            observations[i, base + 8] = 2.0  # Stage
            observations[i, base + 7] = 1.0 if batch_tapped[i, slot] else 0.0
            if cid < card_stats.shape[0]:
                observations[i, base + 0] = card_stats[cid, 0] / 10.0
                observations[i, base + 2] = card_stats[cid, 1] / 5.0
                observations[i, base + 3] = card_stats[cid, 2] / 5.0
                observations[i, base + 5] = card_stats[cid, 11] / 2097152.0

    ptr += 3 * STRIDE  # +30

    # C. LIVE (3)
    for slot in range(3):
        cid = batch_live[i, slot]
        base = ptr + slot * STRIDE
        if cid > 0:
            observations[i, base + 9] = cid / 2000.0
            observations[i, base + 8] = 5.0  # Live
            if cid < card_stats.shape[0]:
                observations[i, base + 3] = card_stats[cid, 2] / 5.0  # Hearts

    ptr += 3 * STRIDE  # +30

    # D. OPP STAGE (3)
    for slot in range(3):
        cid = opp_stage[i, slot]
        base = ptr + slot * STRIDE
        if cid >= 0:
            observations[i, base + 9] = cid / 2000.0
            observations[i, base + 8] = 3.0  # Opp Stage
            observations[i, base + 7] = 1.0 if opp_tapped[i, slot] else 0.0
            if cid < card_stats.shape[0]:
                observations[i, base + 0] = card_stats[cid, 0] / 10.0

    ptr += 3 * STRIDE  # +30

    # E. OPP HISTORY (5)
    for k in range(5):
        cid = batch_opp_history[i, k]
        base = ptr + k * STRIDE
        if cid > 0:
            observations[i, base + 9] = cid / 2000.0
            observations[i, base + 8] = 4.0  # History
            if cid < card_stats.shape[0]:
                observations[i, base + 0] = card_stats[cid, 0] / 10.0


@njit(cache=True, fastmath=True)
def encode_observations_compressed(
    num_envs,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    turn_number,
    observations,
):
    for i in range(num_envs):
        encode_observation_compressed_single(
            i,
            batch_hand,
            batch_stage,
            batch_energy_count,
            batch_tapped,
            batch_scores,
            opp_scores,
            opp_stage,
            opp_tapped,
            card_stats,
            batch_global_ctx,
            batch_live,
            batch_opp_history,
            turn_number,
            observations,
        )
    return observations


@njit(cache=True, fastmath=True)
def encode_observations_standard(
    num_envs,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    turn_number,
    observations,
):
    for i in range(num_envs):
        encode_observation_standard_single(
            i,
            batch_hand,
            batch_stage,
            batch_energy_count,
            batch_tapped,
            batch_scores,
            opp_scores,
            opp_stage,
            opp_tapped,
            card_stats,
            batch_global_ctx,
            batch_live,
            batch_opp_history,
            turn_number,
            observations,
        )
    return observations


@njit(nopython=True, cache=True, fastmath=True, inline="always")
def check_deck_refresh(p_deck, p_trash, g_ctx, DK_idx, TR_idx):
    # Rule 10.2: If deck empty and trash has cards, refresh.
    if g_ctx[DK_idx] <= 0 and g_ctx[TR_idx] > 0:
        # Move trash to deck
        d_ptr = 0
        for k in range(p_trash.shape[0]):
            cid = p_trash[k]
            if cid > 0:
                p_deck[d_ptr] = cid
                p_trash[k] = 0
                d_ptr += 1

        g_ctx[DK_idx] = d_ptr
        g_ctx[TR_idx] = 0
        # Shuffle Deck
        if d_ptr > 1:
            for k in range(d_ptr - 1, 0, -1):
                j = np.random.randint(0, k + 1)
                tmp = p_deck[k]
                p_deck[k] = p_deck[j]
                p_deck[j] = tmp


@njit(nopython=True, cache=True)
def start_turn_numba(i, batch_global_ctx, batch_hand, batch_deck, batch_trash, batch_tapped):
    """Handles Active, Energy, and Draw phases at turn start."""

    # 1. Active Phase (Untap)
    batch_tapped[i].fill(0)

    # 2. Energy Phase (+1 Energy)
    cur_en = batch_global_ctx[i, 5]
    if cur_en < 12:
        batch_global_ctx[i, 5] = cur_en + 1

    # 3. Draw Phase (Draw 1)
    check_deck_refresh(batch_deck[i], batch_trash[i], batch_global_ctx[i], 6, 2)
    found_card = False
    for d in range(60):
        if batch_deck[i, d] > 0:
            top_c = batch_deck[i, d]
            for h in range(60):
                if batch_hand[i, h] == 0:
                    batch_hand[i, h] = top_c
                    batch_deck[i, d] = 0
                    batch_global_ctx[i, 6] -= 1  # DK
                    batch_global_ctx[i, 3] += 1  # HD
                    found_card = True
                    break
            if found_card:
                break

    # 4. Set to Main Phase
    batch_global_ctx[i, 8] = 4


@njit(nopython=True, cache=True)
def execute_mulligan_numba(p_hand, p_deck, p_global_ctx, offset):
    """Effectively swaps marked cards in hand with new cards from deck."""

    to_return = np.zeros(6, dtype=np.int32)
    ptr = 0
    # 1. Identify and remove from hand
    for k in range(6):
        if p_global_ctx[offset + k] > 0:
            cid = p_hand[k]
            if cid > 0:
                to_return[ptr] = cid
                ptr += 1
                p_hand[k] = 0
                p_global_ctx[offset + k] = 0  # Clear flag
                p_global_ctx[3] -= 1  # HD decrement

    # 2. Draw replacements
    replacements_drawn = 0
    if ptr > 0:
        for k in range(60):
            if p_deck[k] > 0:
                card_id = p_deck[k]
                # Find empty slot in hand
                for h_idx in range(60):
                    if p_hand[h_idx] == 0:
                        p_hand[h_idx] = card_id
                        p_deck[k] = 0
                        p_global_ctx[6] -= 1  # DK
                        p_global_ctx[3] += 1  # HD (Actually HD stays same net)
                        # Wait, we removed cid, now adding one. Total HD stayed 6.
                        replacements_drawn += 1
                        break
                if replacements_drawn >= ptr:
                    break

        # 3. Put old cards back in deck (last slots)
        for k in range(ptr):
            for d_idx in range(60):
                if p_deck[d_idx] == 0:
                    p_deck[d_idx] = to_return[k]
                    p_global_ctx[6] += 1  # DK
                    break

        # 4. Shuffle entire deck (Rule 6.2.2.1)
        # Compact and shuffle
        compact_deck = np.zeros(60, dtype=np.int32)
        c_ptr = 0
        for d in range(60):
            if p_deck[d] > 0:
                compact_deck[c_ptr] = p_deck[d]
                c_ptr += 1

        if c_ptr > 1:
            for k in range(c_ptr - 1, 0, -1):
                j = np.random.randint(0, k + 1)
                tmp = compact_deck[k]
                compact_deck[k] = compact_deck[j]
                compact_deck[j] = tmp

        p_deck[:] = compact_deck[:]


@njit(cache=True, fastmath=True)
def step_player_single(
    act_id,
    player_id,
    p_hand,
    p_deck,
    p_stage,
    p_energy_vec,
    p_energy_count,
    p_tapped,
    p_live,
    p_scores,
    p_global_ctx,
    p_trash,
    p_continuous_vec,
    p_continuous_ptr,
    opp_tapped,
    card_stats,
    bytecode_map,
    bytecode_index,
):
    """
    Unified step logic for one player (Agent 0 or Opponent 1).
    """
    if act_id == 0:
        # Pass -> Next Phase
        if p_global_ctx[PH] == -1:  # MULL_P1 -> MULL_P2
            # Execute Mulligan for player 0
            execute_mulligan_numba(p_hand, p_deck, p_global_ctx, 120)
            p_global_ctx[PH] = 0
        elif p_global_ctx[PH] == 0:  # MULL_P2 -> ACTIVE
            # Execute Mulligan for player 0
            execute_mulligan_numba(p_hand, p_deck, p_global_ctx, 120)
            p_global_ctx[PH] = 1  # Active
            # Auto-advance to Main (simplified)
            p_global_ctx[PH] = 4
        else:
            # Pass -> Performance Phase
            p_global_ctx[PH] = 8
        return

    # 0. Mulligan Selection (300-359 or 64-69)
    is_mull_toggle = False
    mull_h_idx = -1
    if 300 <= act_id <= 359:
        is_mull_toggle = True
        mull_h_idx = act_id - 300
    elif 64 <= act_id <= 69:
        is_mull_toggle = True
        mull_h_idx = act_id - 64

    if is_mull_toggle:
        if p_global_ctx[PH] == -1 or p_global_ctx[PH] == 0:
            if mull_h_idx < 60:
                p_global_ctx[120 + mull_h_idx] = 1 - p_global_ctx[120 + mull_h_idx]
        return

    # 1. Member Play (1-45)
    if 1 <= act_id <= 45:
        adj = act_id - 1
        hand_idx = adj // 3
        slot = adj % 3

        if hand_idx < p_hand.shape[0]:
            card_id = p_hand[hand_idx]
            if cid >= 0:
                bid = get_base_id(cid)
                if bid < card_stats.shape[0]:
                    # Cost Calculation
                    cost = card_stats[bid, 0]
                    effective_cost = cost
                    prev_cid = p_stage[slot]
                    if prev_cid >= 0:
                        prev_bid = get_base_id(prev_cid)
                        if prev_bid < card_stats.shape[0]:
                            prev_cost = card_stats[prev_bid, 0]
                            effective_cost = cost - prev_cost
                            if effective_cost < 0:
                                effective_cost = 0

                # Pay Cost by Tapping Energy
                ec = p_global_ctx[EN]
                if ec > 12:
                    ec = 12
                paid = 0
                if effective_cost > 0:
                    for e_idx in range(ec):
                        if 3 + e_idx < 16:
                            if p_tapped[3 + e_idx] == 0:
                                p_tapped[3 + e_idx] = 1
                                paid += 1
                                if paid >= effective_cost:
                                    break

                # Capture prev_cid for Baton Pass logic (Index 60)
                p_global_ctx[PV] = prev_cid

                # Move to Stage
                p_stage[slot] = card_id

                # Shift Hand (Rule: Parity with Python)
                for k in range(hand_idx, 59):
                    p_hand[k] = p_hand[k + 1]
                p_hand[59] = 0

                p_global_ctx[HD] -= 1
                p_global_ctx[51 + slot] = 1  # Mark played in slot

                # Resolve Auto-Ability
                bid = get_base_id(card_id)
                if bid < bytecode_index.shape[0]:
                    map_idx = bytecode_index[bid, 0]
                    if map_idx >= 0:
                        delta_bonus = np.zeros(1, dtype=np.int32)
                        resolve_bytecode(
                            bytecode_map[map_idx],
                            np.zeros(64, dtype=np.int32),
                            p_global_ctx,
                            player_id,
                            p_hand,
                            p_deck,
                            p_stage,
                            p_energy_vec,
                            p_energy_count,
                            p_continuous_vec,
                            p_continuous_ptr,
                            p_tapped,
                            p_live,
                            opp_tapped,
                            p_trash,
                            bytecode_map,
                            bytecode_index,
                            delta_bonus,
                            card_stats,
                        )
                        p_scores[0] += delta_bonus[0]

    # 2. Activate Ability (61-63 or 200-202)
    elif (61 <= act_id <= 63) or (200 <= act_id <= 202):
        if 200 <= act_id <= 202:
            slot = act_id - 200
        else:
            slot = act_id - 61

        card_id = p_stage[slot]
        if card_id >= 0 and not p_tapped[slot]:
            bid = get_base_id(card_id)
            if bid < bytecode_index.shape[0]:
                map_idx = bytecode_index[bid, 0]
                if map_idx >= 0:
                    delta_bonus = np.zeros(1, dtype=np.int32)
                    resolve_bytecode(
                        bytecode_map[map_idx],
                        np.zeros(64, dtype=np.int32),
                        p_global_ctx,
                        player_id,
                        p_hand,
                        p_deck,
                        p_stage,
                        p_energy_vec,
                        p_energy_count,
                        p_continuous_vec,
                        p_continuous_ptr,
                        p_tapped,
                        p_live,
                        opp_tapped,
                        p_trash,
                        bytecode_map,
                        bytecode_index,
                        delta_bonus,
                        card_stats,
                    )
                    p_scores[0] += delta_bonus[0]
                    p_tapped[slot] = 1

    # 3. Set Live Card (46-60 or 400-459)
    elif (46 <= act_id <= 60) or (400 <= act_id <= 459):
        if 400 <= act_id <= 459:
            h_idx_live = act_id - 400
        else:
            h_idx_live = act_id - 46

        if h_idx_live < p_hand.shape[0]:
            card_id = p_hand[h_idx_live]
            if card_id > 0:
                # Find empty slot in Pending Live slots (3-5)
                for j in range(3, 6):
                    if p_live[j] == 0:
                        p_live[j] = card_id

                        # Shift Hand
                        for k in range(h_idx_live, 59):
                            p_hand[k] = p_hand[k + 1]
                        p_hand[59] = 0

                        # Rule 8.2.2/8.2.4: Draw replacement immediately
                        # Match deck refresh logic
                        DK_idx = 6
                        TR_idx = 2
                        if p_global_ctx[DK_idx] <= 0 and p_global_ctx[TR_idx] > 0:
                            # Move trash to deck
                            d_ptr = 0
                            for k in range(p_trash.shape[0]):
                                cid_tr = p_trash[k]
                                if cid_tr > 0:
                                    p_deck[d_ptr] = cid_tr
                                    p_trash[k] = 0
                                    d_ptr += 1
                            p_global_ctx[DK_idx] = d_ptr
                            p_global_ctx[TR_idx] = 0
                            # Shuffle
                            if d_ptr > 1:
                                for k in range(d_ptr - 1, 0, -1):
                                    rj = np.random.randint(0, k + 1)
                                    tmp = p_deck[k]
                                    p_deck[k] = p_deck[rj]
                                    p_deck[rj] = tmp

                        # Draw card
                        for k in range(60):
                            if p_deck[k] > 0:
                                d_cid = p_deck[k]
                                # Find empty slot in hand (usually at end because of shift)
                                for h_srch in range(60):
                                    if p_hand[h_srch] == 0:
                                        p_hand[h_srch] = d_cid
                                        p_deck[k] = 0
                                        p_global_ctx[6] -= 1  # DK
                                        # HD stays same (Set 1, Draw 1)
                                        break
                                break
                        break


@njit(cache=True, fastmath=True)
def reset_single(
    i,
    batch_stage,
    batch_energy_vec,
    batch_energy_count,
    batch_continuous_vec,
    batch_continuous_ptr,
    batch_tapped,
    batch_live,
    batch_scores,
    batch_flat_ctx,
    batch_global_ctx,
    batch_hand,
    batch_deck,
    opp_stage,
    opp_energy_vec,
    opp_energy_count,
    opp_tapped,
    opp_live,
    opp_scores,
    opp_global_ctx,
    opp_hand,
    opp_deck,
    batch_trash,
    opp_trash,
    batch_opp_history,  # Added
    ability_member_ids,
    ability_live_ids,
    force_start_order,
):
    # Clear Agent
    batch_stage[i].fill(-1)
    batch_energy_vec[i].fill(0)
    batch_energy_count[i].fill(0)
    batch_continuous_vec[i].fill(0)
    batch_continuous_ptr[i] = 0
    batch_tapped[i].fill(0)
    batch_live[i].fill(0)
    batch_scores[i] = 0
    batch_flat_ctx[i].fill(0)
    batch_global_ctx[i].fill(0)
    batch_trash[i].fill(0)
    batch_opp_history[i].fill(0)

    # Clear Opponent
    opp_stage[i].fill(-1)
    opp_energy_vec[i].fill(0)
    opp_energy_count[i].fill(0)
    opp_tapped[i].fill(0)
    opp_live[i].fill(0)
    opp_scores[i] = 0
    opp_global_ctx[i].fill(0)
    opp_trash[i].fill(0)

    # Generate Agent Deck - Exact Copy if sizes match (Shuffle later)
    # Members (0-47)
    if len(ability_member_ids) == 48:
        for k in range(48):
            batch_deck[i, k] = ability_member_ids[k]
    else:
        for k in range(48):
            idx = np.random.randint(0, len(ability_member_ids))
            batch_deck[i, k] = ability_member_ids[idx]

    # Lives (48-59) - All 12 go in deck. Live Zone starts EMPTY (Rule 6.2).
    # Cards are placed in Live Zone during Live Card Set Phase (Rule 8.2.2).
    n_live_pool = len(ability_live_ids)
    for k in range(12):
        idx = np.random.randint(0, n_live_pool)
        batch_deck[i, 48 + k] = ability_live_ids[idx]

    np.random.shuffle(batch_deck[i])

    # Draw Hand (6) - Rule 6.2.1.5
    batch_hand[i].fill(0)
    drawn = 0
    for k in range(60):
        if batch_deck[i, k] > 0:
            batch_hand[i, drawn] = batch_deck[i, k]
            batch_deck[i, k] = 0
            drawn += 1
            if drawn >= 6:
                break

    batch_global_ctx[i, 3] = 6  # HD
    batch_global_ctx[i, 6] = 54  # DK (60 - 6 hand = 54)
    batch_global_ctx[i, 5] = 3  # Initial Energy (Rule 6.2.1.7)
    batch_global_ctx[i, 8] = -1  # PH = MULLIGAN_P1
    batch_global_ctx[i, 54] = 1  # Turn

    # Opponent Setup
    # Members (0-47)
    if len(ability_member_ids) == 48:
        for k in range(48):
            opp_deck[i, k] = ability_member_ids[k]
    else:
        for k in range(48):
            idx = np.random.randint(0, len(ability_member_ids))
            opp_deck[i, k] = ability_member_ids[idx]

    # Lives (48-59)
    if len(ability_live_ids) == 12:
        for k in range(12):
            opp_deck[i, 48 + k] = ability_live_ids[k]
    else:
        for k in range(12):
            idx = np.random.randint(0, len(ability_live_ids))
            opp_deck[i, 48 + k] = ability_live_ids[idx]

    np.random.shuffle(opp_deck[i])

    # Draw Hand (6) - Rule 6.2.1.5. Live Zone starts empty.
    opp_hand[i].fill(0)
    drawn_o = 0
    for k in range(60):
        if opp_deck[i, k] > 0:
            opp_hand[i, drawn_o] = opp_deck[i, k]
            opp_deck[i, k] = 0
            drawn_o += 1
            if drawn_o >= 6:
                break

    opp_global_ctx[i, 3] = 6  # HD
    opp_global_ctx[i, 6] = 54  # DK (60 - 6 hand = 54)
    opp_global_ctx[i, 5] = 3  # Initial Energy
    opp_global_ctx[i, 8] = -1  # PH = MULLIGAN_P1
    opp_global_ctx[i, 54] = 1  # Turn

    # --- START ORDER ---
    # Index 10 in global_ctx will flag if Agent is Second (1) or First (0)
    # force_start_order: -1=Random, 0=P1(Agent First), 1=P2(Agent Second)
    if force_start_order == -1:
        is_second = np.random.randint(0, 2)
    else:
        is_second = force_start_order

    batch_global_ctx[i, 10] = is_second

    if is_second == 1:
        # Agent is P2.
        # 1. Opponent (P1) performs Mulligan immediately.
        # We simulate "Pass Mulligan" for opponent: Keep hand (simplified for now? or random?)
        # Let's say Opponent keeps hand to be simple, or does random swap.
        # Using execute_mulligan_numba with random flags 120-125
        # Set some random flags for opp
        for k in range(6):
            if np.random.random() < 0.3:
                opp_global_ctx[i, 120 + k] = 1

        execute_mulligan_numba(opp_hand[i], opp_deck[i], opp_global_ctx[i], 120)

        # 2. Agent starts in Phase 0 (Mulligan P2)
        batch_global_ctx[i, 8] = 0
        opp_global_ctx[i, 8] = 0

    else:
        # Agent is P1. Starts in Phase -1.
        batch_global_ctx[i, 8] = -1
        opp_global_ctx[i, 8] = -1


@njit(cache=True, parallel=True, fastmath=True)
def integrated_step_numba(
    num_envs,
    actions,
    batch_hand,
    batch_deck,
    batch_stage,
    batch_energy_vec,
    batch_energy_count,
    batch_continuous_vec,
    batch_continuous_ptr,
    batch_tapped,
    batch_live,
    batch_scores,
    batch_flat_ctx,
    batch_global_ctx,
    opp_hand,
    opp_deck,
    opp_stage,
    opp_energy_vec,
    opp_energy_count,
    opp_tapped,
    opp_live,
    opp_scores,
    opp_global_ctx,
    card_stats,
    bytecode_map,
    bytecode_index,
    batch_opp_history,
    obs_buffer,
    prev_scores,
    prev_opp_scores,
    prev_phases,
    ability_member_ids,
    ability_live_ids,
    turn_number_ptr,
    terminal_obs_buffer,
    batch_trash,
    opp_trash,
    term_scores_agent,
    term_scores_opp,
    obs_mode_int,
    game_config,  # New Config
    opp_mode_int,
    force_start_order,
):
    # Config Unpack
    CFG_TURN_LIMIT = int(game_config[0])
    CFG_STEP_LIMIT = int(game_config[1])
    CFG_REWARD_WIN = game_config[2]
    CFG_REWARD_LOSE = game_config[3]
    CFG_REWARD_SCALE = game_config[4]
    CFG_REWARD_TURN_PENALTY = game_config[5]

    rewards = np.zeros(num_envs, dtype=np.float32)
    dones = np.zeros(num_envs, dtype=np.bool_)

    # Import locally if needed or rely on global import?
    # Numba usually handles global imports if jitted.
    # Note: run_opponent_turn_loop must be available.
    # check_deck_refresh available from fast_logic

    for i in prange(num_envs):
        act_id = actions[i]
        ph = int(batch_global_ctx[i, 8])

        batch_global_ctx[i, 0] = batch_scores[i]

        if act_id != 0:
            # Step Safeguard (Index 58)
            batch_global_ctx[i, 58] += 1

            # 1. Execute Action
            score_arr = batch_scores[i : i + 1]

            # Mulligan Toggling
            is_mull_act = False
            mull_idx = -1
            if obs_mode_int == 3:  # ATTENTION
                if 64 <= act_id <= 69:
                    is_mull_act = True
                    mull_idx = act_id - 64
            else:  # Standard/IMAX
                if 300 <= act_id <= 310:
                    is_mull_act = True
                    mull_idx = act_id - 300

            if is_mull_act and (ph == -1 or ph == 0):
                if mull_idx < 6:
                    # Toggle selection flag at (120 + idx)
                    batch_global_ctx[i, 120 + mull_idx] = 1 - batch_global_ctx[i, 120 + mull_idx]
            else:
                step_player_single(
                    act_id,
                    0,
                    batch_hand[i],
                    batch_deck[i],
                    batch_stage[i],
                    batch_energy_vec[i],
                    batch_energy_count[i],
                    batch_tapped[i],
                    batch_live[i],
                    score_arr,
                    batch_global_ctx[i],
                    batch_trash[i],
                    batch_continuous_vec[i],
                    batch_continuous_ptr[i : i + 1],
                    opp_tapped[i],
                    card_stats,
                    bytecode_map,
                    bytecode_index,
                )

            # 2. Rewards (Score Change Only)
            current_score = batch_scores[i]
            score_diff = float(current_score) - float(prev_scores[i])
            opp_score_diff = float(opp_scores[i]) - float(prev_opp_scores[i])

            r = (score_diff * CFG_REWARD_SCALE) - (opp_score_diff * CFG_REWARD_SCALE)
            r += CFG_REWARD_TURN_PENALTY  # Turn Penalty (Match Path B)

            # Interaction Reward (Encourage taking actions in Main Phase)
            if score_diff == 0 and opp_score_diff == 0 and ph == 4:
                r += 0.01

            # Phase Advance Incentive (Discourage Mulligan looping)
            if ph <= 0 and act_id != 0:
                r -= 0.01

            win = current_score >= 3
            lose = opp_scores[i] >= 3

            if win:
                r += CFG_REWARD_WIN
            if lose:
                r += CFG_REWARD_LOSE

            rewards[i] = r
            rewards[i] = r
            # Turn limit or Step limit (1000 actions per game)
            is_done = (
                win
                or lose
                or (batch_global_ctx[i, 54] >= CFG_TURN_LIMIT)
                or (batch_global_ctx[i, 58] >= CFG_STEP_LIMIT)
            )
            dones[i] = is_done

            if is_done:
                # Terminal Obs
                if obs_mode_int == 0:
                    encode_observation_imax_single(
                        i,
                        batch_hand,
                        batch_stage,
                        batch_energy_count,
                        batch_tapped,
                        batch_scores,
                        opp_scores,
                        opp_stage,
                        opp_tapped,
                        card_stats,
                        batch_global_ctx,
                        batch_live,
                        batch_opp_history,
                        int(batch_global_ctx[i, 54]),
                        terminal_obs_buffer,
                    )
                elif obs_mode_int == 1:
                    encode_observation_standard_single(
                        i,
                        batch_hand,
                        batch_stage,
                        batch_energy_count,
                        batch_tapped,
                        batch_scores,
                        opp_scores,
                        opp_stage,
                        opp_tapped,
                        card_stats,
                        batch_global_ctx,
                        batch_live,
                        batch_opp_history,
                        int(batch_global_ctx[i, 54]),
                        terminal_obs_buffer,
                    )
                elif obs_mode_int == 3:
                    encode_observation_attention_single(
                        i,
                        batch_hand,
                        batch_stage,
                        batch_energy_count,
                        batch_tapped,
                        batch_scores,
                        opp_scores,
                        opp_stage,
                        opp_tapped,
                        card_stats,
                        batch_global_ctx,
                        batch_live,
                        batch_opp_history,
                        opp_global_ctx,
                        int(batch_global_ctx[i, 54]),
                        terminal_obs_buffer,
                    )
                else:
                    encode_observation_compressed_single(
                        i,
                        batch_hand,
                        batch_stage,
                        batch_energy_count,
                        batch_tapped,
                        batch_scores,
                        opp_scores,
                        opp_stage,
                        opp_tapped,
                        card_stats,
                        batch_global_ctx,
                        batch_live,
                        batch_opp_history,
                        int(batch_global_ctx[i, 54]),
                        terminal_obs_buffer,
                    )

                term_scores_agent[i] = batch_scores[i]
                term_scores_opp[i] = opp_scores[i]
                # Reset
                reset_single(
                    i,
                    batch_stage,
                    batch_energy_vec,
                    batch_energy_count,
                    batch_continuous_vec,
                    batch_continuous_ptr,
                    batch_tapped,
                    batch_live,
                    batch_scores,
                    batch_flat_ctx,
                    batch_global_ctx,
                    batch_hand,
                    batch_deck,
                    opp_stage,
                    opp_energy_vec,
                    opp_energy_count,
                    opp_tapped,
                    opp_live,
                    opp_scores,
                    opp_global_ctx,
                    opp_hand,
                    opp_deck,
                    batch_trash,
                    opp_trash,
                    batch_opp_history,
                    ability_member_ids,
                    ability_live_ids,
                    force_start_order,
                )
                prev_scores[i] = 0
                prev_opp_scores[i] = 0
                batch_global_ctx[i, 58] = 0  # Reset action counter

            else:
                prev_scores[i] = batch_scores[i]
                prev_opp_scores[i] = opp_scores[i]

            # 4. Standard Obs (Keep Phase correct)
            if batch_global_ctx[i, 8] < 4 and batch_global_ctx[i, 8] >= 1:
                batch_global_ctx[i, 8] = 4  # Auto-advance Active/Energy/Draw for RL

            if obs_mode_int == 0:
                encode_observation_imax_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )
            elif obs_mode_int == 1:
                encode_observation_standard_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )
            elif obs_mode_int == 3:
                encode_observation_attention_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    opp_global_ctx,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )
            else:
                encode_observation_compressed_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )

        # --- PATH B: PASS (Turn End or Mulligan Transition) ---
        else:  # act_id == 0
            ph = int(batch_global_ctx[i, 8])

            if ph == -1:  # Agent (P1) finished MULL_P1 selection
                # Exec Agent Mulligan
                execute_mulligan_numba(batch_hand[i], batch_deck[i], batch_global_ctx[i], 120)
                # Next: Opponent P2 Mulligan
                batch_global_ctx[i, 8] = 0  # To MULL_P2

            elif ph == 0:  # End of MULL_P2
                # Check who is P2
                is_second = batch_global_ctx[i, 10]

                if is_second == 1:
                    # Agent was P2. Agent just finished MULL_P2.
                    execute_mulligan_numba(batch_hand[i], batch_deck[i], batch_global_ctx[i], 120)

                    # NOW: Opponent Turn 1 must happen (because Agent is P2)
                    opp_score_arr = opp_scores[i : i + 1]
                    opp_cont_vec = np.zeros((32, 10), dtype=np.int32)
                    opp_cont_ptr = np.zeros(1, dtype=np.int32)

                    run_opponent_turn_loop(
                        opp_hand[i],
                        opp_deck[i],
                        opp_stage[i],
                        opp_energy_vec[i],
                        opp_energy_count[i],
                        opp_tapped[i],
                        opp_live[i],
                        opp_score_arr,
                        opp_global_ctx[i],
                        opp_trash[i],
                        opp_cont_vec,
                        opp_cont_ptr,
                        batch_tapped[i],
                        card_stats,
                        bytecode_map,
                        bytecode_index,
                    )

                    # Agent Starts Turn 1 (Active)
                    batch_global_ctx[i, 8] = 1
                    batch_tapped[i].fill(0)
                    opp_tapped[i].fill(0)

                else:
                    # Agent was P1. This Phase 0 was for Opponent (P2) Mulligan.
                    execute_mulligan_numba(opp_hand[i], opp_deck[i], opp_global_ctx[i], 120)

                    # Agent Turn 1 Start
                    batch_global_ctx[i, 8] = 1
                    batch_tapped[i].fill(0)
                    opp_tapped[i].fill(0)

            elif ph == 1:  # Transition from ACTIVE to ENERGY
                batch_global_ctx[i, 8] = 2

            elif ph == 2:  # Transition from ENERGY to DRAW
                cur_en = batch_global_ctx[i, 5]
                if cur_en < 12:
                    batch_global_ctx[i, 5] = cur_en + 1
                batch_global_ctx[i, 8] = 3

            elif ph == 3:  # Transition from DRAW to MAIN
                check_deck_refresh(batch_deck[i], batch_trash[i], batch_global_ctx[i], 6, 2)
                found_card = False
                for d in range(60):
                    if batch_deck[i, d] > 0:
                        top_c = batch_deck[i, d]
                        for h in range(60):
                            if batch_hand[i, h] == 0:
                                batch_hand[i, h] = top_c
                                batch_deck[i, d] = 0
                                batch_global_ctx[i, 6] -= 1  # DK
                                batch_global_ctx[i, 3] += 1  # HD
                                found_card = True
                                break
                        if found_card:
                            break
                batch_global_ctx[i, 8] = 4

            elif ph == 4:  # MAIN phase end
                # 1. Run Opponent Turn Loop
                # 1. Opponent Turn
                # Dummy Continuous for Opponent (Since we don't track it fully yet)
                opp_continuous_vec = np.zeros((batch_hand.shape[0], 32, 10), dtype=np.int32)
                opp_continuous_ptr = np.zeros(batch_hand.shape[0], dtype=np.int32)

                if opp_mode_int == 0:
                    # Heuristic
                    run_opponent_turn_loop(
                        opp_hand[i],
                        opp_deck[i],
                        opp_stage[i],
                        opp_energy_vec[i],
                        opp_energy_count[i],
                        opp_tapped[i],
                        opp_live[i],
                        opp_scores[i : i + 1],
                        opp_global_ctx[i],
                        opp_trash[i],
                        opp_continuous_vec[i],
                        opp_continuous_ptr[i : i + 1],
                        batch_tapped[i],
                        card_stats,
                        bytecode_map,
                        bytecode_index,
                    )
                elif opp_mode_int == 2:
                    # Solitaire Mode (Pass Only)
                    # Opponent does nothing.
                    pass
                else:
                    # Random
                    run_random_turn_loop(
                        opp_hand[i],
                        opp_deck[i],
                        opp_stage[i],
                        opp_energy_vec[i],
                        opp_energy_count[i],
                        opp_tapped[i],
                        opp_live[i],
                        opp_scores[i : i + 1],
                        opp_global_ctx[i],
                        opp_trash[i],
                        opp_continuous_vec[i],
                        opp_continuous_ptr[i : i + 1],
                        batch_tapped[i],
                        card_stats,
                        bytecode_map,
                        bytecode_index,
                    )

                # Sync Opp Stats
                batch_global_ctx[i, 4] = opp_global_ctx[i, HD]
                batch_global_ctx[i, 9] = opp_global_ctx[i, DK]
                batch_global_ctx[i, 7] = opp_global_ctx[i, TR]

                # 2. Performance Phase (Resolve Lives)
                agent_live_score = 0
                opp_live_score = 0
                has_agent_live = False
                has_opp_live = False

                # Agent
                agent_succ_cid = 0
                for z_idx in range(3, 10):  # Scan Pending slots
                    lid = batch_live[i, z_idx]
                    if lid > 0:
                        s = resolve_live_single(
                            i,
                            lid,
                            batch_stage,
                            batch_live,
                            batch_scores,
                            batch_global_ctx,
                            batch_deck,
                            batch_hand,
                            batch_trash,
                            card_stats,
                            batch_continuous_vec,
                            batch_continuous_ptr,
                            bytecode_map,
                            bytecode_index,
                        )
                        if s > 0:
                            agent_live_score += s
                            has_agent_live = True
                            if agent_succ_cid == 0:
                                agent_succ_cid = lid

                # Opponent
                opp_succ_cid = 0
                for z_idx in range(3, 10):  # Scan Pending slots
                    lid = opp_live[i, z_idx]
                    if lid > 0:
                        s = resolve_live_single(
                            i,
                            lid,
                            opp_stage,
                            opp_live,
                            opp_scores,
                            opp_global_ctx,
                            opp_deck,
                            opp_hand,
                            opp_trash,
                            card_stats,
                            batch_continuous_vec,
                            batch_continuous_ptr,
                            bytecode_map,
                            bytecode_index,
                        )
                        if s > 0:
                            opp_live_score += s
                            has_opp_live = True
                            if opp_succ_cid == 0:
                                opp_succ_cid = lid

                # 3. Battle Phase (Comparison)
                # Rule 8.4.3 & 8.4.6
                agent_wins = False
                opp_wins = False

                if has_agent_live and not has_opp_live:
                    agent_wins = True
                elif not has_agent_live and has_opp_live:
                    opp_wins = True
                elif has_agent_live and has_opp_live:
                    if agent_live_score > opp_live_score:
                        agent_wins = True
                    elif opp_live_score > agent_live_score:
                        opp_wins = True
                    else:
                        # Tie - Both Win
                        agent_wins = True
                        opp_wins = True

                # Apply Win Result (Rule 8.4.7)
                if agent_wins:
                    if opp_wins and batch_scores[i] == 2:
                        pass  # Tie at Match Point
                    else:
                        # Move ONE successful card to Success Zone (slots 0-2)
                        if agent_succ_cid > 0:
                            cur_score = batch_scores[i]
                            if cur_score < 3:
                                batch_live[i, cur_score] = agent_succ_cid
                        batch_scores[i] += 1
                        batch_global_ctx[i, 0] = batch_scores[i]

                if opp_wins:
                    if agent_wins and opp_scores[i] == 2:
                        pass  # Tie at Match Point
                    else:
                        if opp_succ_cid > 0:
                            cur_score_o = opp_scores[i]
                            if cur_score_o < 3:
                                opp_live[i, cur_score_o] = opp_succ_cid
                        opp_scores[i] += 1

                # 4. Cleanup Pending Live Zones (Rule 8.4.8)
                # Slot 3+ are pending and should be cleared/trashed
                for z_idx in range(3, 10):
                    lid = batch_live[i, z_idx]
                    if lid > 0:
                        move_to_trash(i, lid, batch_trash, batch_global_ctx, 2)
                        batch_live[i, z_idx] = 0

                for z_idx in range(3, 10):
                    lid = opp_live[i, z_idx]
                    if lid > 0:
                        move_to_trash(i, lid, opp_trash, opp_global_ctx, 2)
                        opp_live[i, z_idx] = 0

                # 3. Rewards & Game Over
                current_score = batch_scores[i]
                score_diff = float(current_score) - float(prev_scores[i])
                opp_score_diff = float(opp_scores[i]) - float(prev_opp_scores[i])

                r = (score_diff * CFG_REWARD_SCALE) - (opp_score_diff * CFG_REWARD_SCALE)
                r += CFG_REWARD_TURN_PENALTY  # Reduced Turn penalty (was 5.0)

                win = current_score >= 3
                lose = opp_scores[i] >= 3

                if win:
                    r += CFG_REWARD_WIN
                if lose:
                    r += CFG_REWARD_LOSE

                rewards[i] = r
                is_done = (
                    win
                    or lose
                    or (batch_global_ctx[i, 54] >= CFG_TURN_LIMIT)
                    or (batch_global_ctx[i, 58] >= CFG_STEP_LIMIT)
                )
                dones[i] = is_done

                if is_done:
                    if obs_mode_int == 0:
                        encode_observation_imax_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            int(batch_global_ctx[i, 54]),
                            terminal_obs_buffer,
                        )
                    elif obs_mode_int == 1:  # STANDARD
                        encode_observation_standard_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            int(batch_global_ctx[i, 54]),
                            terminal_obs_buffer,
                        )
                    elif obs_mode_int == 3:  # ATTENTION
                        encode_observation_attention_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            opp_global_ctx,
                            int(batch_global_ctx[i, 54]),
                            terminal_obs_buffer,
                        )
                    else:  # COMPRESSED
                        encode_observation_compressed_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            int(batch_global_ctx[i, 54]),
                            terminal_obs_buffer,
                        )
                    term_scores_agent[i] = batch_scores[i]
                    term_scores_opp[i] = opp_scores[i]
                    reset_single(
                        i,
                        batch_stage,
                        batch_energy_vec,
                        batch_energy_count,
                        batch_continuous_vec,
                        batch_continuous_ptr,
                        batch_tapped,
                        batch_live,
                        batch_scores,
                        batch_flat_ctx,
                        batch_global_ctx,
                        batch_hand,
                        batch_deck,
                        opp_stage,
                        opp_energy_vec,
                        opp_energy_count,
                        opp_tapped,
                        opp_live,
                        opp_scores,
                        opp_global_ctx,
                        opp_hand,
                        opp_deck,
                        batch_trash,
                        opp_trash,
                        batch_opp_history,
                        ability_member_ids,
                        ability_live_ids,
                        force_start_order,
                    )
                    prev_scores[i] = 0
                    prev_opp_scores[i] = 0

                    if obs_mode_int == 0:
                        encode_observation_imax_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            int(batch_global_ctx[i, 54]),
                            obs_buffer,
                        )
                    elif obs_mode_int == 1:
                        encode_observation_standard_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            int(batch_global_ctx[i, 54]),
                            obs_buffer,
                        )
                    elif obs_mode_int == 1:  # STANDARD
                        encode_observation_standard_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            int(batch_global_ctx[i, 54]),
                            obs_buffer,
                        )
                    elif obs_mode_int == 3:  # ATTENTION
                        encode_observation_attention_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            opp_global_ctx,
                            int(batch_global_ctx[i, 54]),
                            obs_buffer,
                        )
                    else:  # COMPRESSED
                        encode_observation_compressed_single(
                            i,
                            batch_hand,
                            batch_stage,
                            batch_energy_count,
                            batch_tapped,
                            batch_scores,
                            opp_scores,
                            opp_stage,
                            opp_tapped,
                            card_stats,
                            batch_global_ctx,
                            batch_live,
                            batch_opp_history,
                            int(batch_global_ctx[i, 54]),
                            obs_buffer,
                        )
                    continue

                else:
                    prev_scores[i] = batch_scores[i]
                    prev_opp_scores[i] = opp_scores[i]

                    # 4. NEXT TURN SETUP (Transitions to ACTIVE Phase (1) for Agent)
                    # In granular mode, we just set the phase to 1 and let subsequent 'Pass' steps handle Rule 7 logic
                    opp_tapped[i].fill(0)
                    opp_global_ctx[i, 54] += 1
                    opp_global_ctx[i, 5] = min(opp_global_ctx[i, 5] + 1, 12)
                    check_deck_refresh(opp_deck[i], opp_trash[i], opp_global_ctx[i], DK, TR)
                    # Standard Opponent Draw 1
                    found_card_o = False
                    for d in range(60):
                        if opp_deck[i, d] > 0:
                            for h in range(60):
                                if opp_hand[i, h] == 0:
                                    opp_hand[i, h] = opp_deck[i, d]
                                    opp_deck[i, d] = 0
                                    opp_global_ctx[i, DK] -= 1
                                    opp_global_ctx[i, HD] += 1
                                    found_card_o = True
                                    break
                            if found_card_o:
                                break

                    # Agent Untap immediately
                    batch_tapped[i].fill(0)
                    batch_global_ctx[i, 51:54].fill(0)  # Reset played-this-turn flags
                    batch_global_ctx[i, 54] += 1  # Agent Turn ++

                    # RULE: Draw up to 6 if hand size < 6 at turn start (Parity)
                    cur_hand = int(batch_global_ctx[i, 3])
                    if cur_hand < 6:
                        to_draw = 6 - cur_hand
                        for _ in range(to_draw):
                            check_deck_refresh(batch_deck[i], batch_trash[i], batch_global_ctx[i], 6, 2)
                            for d in range(60):
                                if batch_deck[i, d] > 0:
                                    for h in range(60):
                                        if batch_hand[i, h] == 0:
                                            batch_hand[i, h] = batch_deck[i, d]
                                            batch_deck[i, d] = 0
                                            batch_global_ctx[i, 6] -= 1
                                            batch_global_ctx[i, 3] += 1
                                            break
                                    break

                    batch_global_ctx[i, 8] = 2  # Next step for Agent is Energy Phase

            # End of Path B - Capture delta rewards for all transitions
            if rewards[i] == 0.0:
                cur_s = float(batch_scores[i])
                cur_os = float(opp_scores[i])
                s_diff = cur_s - float(prev_scores[i])
                os_diff = cur_os - float(prev_opp_scores[i])

                # Check for win/loss in this step (though usually happens in Main)
                win = cur_s >= 3
                lose = cur_os >= 3

                r = (s_diff * CFG_REWARD_SCALE) - (os_diff * CFG_REWARD_SCALE)
                r += CFG_REWARD_TURN_PENALTY

                if win:
                    r += CFG_REWARD_WIN
                if lose:
                    r += CFG_REWARD_LOSE

                rewards[i] = r
                dones[i] = (
                    win
                    or lose
                    or (batch_global_ctx[i, 54] >= CFG_TURN_LIMIT)
                    or (batch_global_ctx[i, 58] >= CFG_STEP_LIMIT)
                )

            # Update state for next step
            if not dones[i]:
                prev_scores[i] = batch_scores[i]
                prev_opp_scores[i] = opp_scores[i]

            # Path B helper observation update
            if obs_mode_int == 0:  # IMAX
                encode_observation_imax_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )
            elif obs_mode_int == 1:  # STANDARD
                encode_observation_standard_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )
            elif obs_mode_int == 3:  # ATTENTION
                encode_observation_attention_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    opp_global_ctx,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )
            else:  # COMPRESSED
                encode_observation_compressed_single(
                    i,
                    batch_hand,
                    batch_stage,
                    batch_energy_count,
                    batch_tapped,
                    batch_scores,
                    opp_scores,
                    opp_stage,
                    opp_tapped,
                    card_stats,
                    batch_global_ctx,
                    batch_live,
                    batch_opp_history,
                    int(batch_global_ctx[i, 54]),
                    obs_buffer,
                )

    turn_number_ptr[0] += 1
    return rewards, dones


@njit(parallel=True, cache=True)
def reset_kernel_numba(
    indices,
    batch_stage,
    batch_energy_vec,
    batch_energy_count,
    batch_continuous_vec,
    batch_continuous_ptr,
    batch_tapped,
    batch_live,
    batch_scores,
    batch_flat_ctx,
    batch_global_ctx,
    batch_hand,
    batch_deck,
    opp_stage,
    opp_energy_vec,
    opp_energy_count,
    opp_tapped,
    opp_live,
    opp_scores,
    opp_global_ctx,
    opp_hand,
    opp_deck,
    batch_trash,
    opp_trash,
    batch_opp_history,
    ability_member_ids,
    ability_live_ids,
    force_start_order,
):
    num_reset = indices.shape[0]
    for idx in prange(num_reset):
        i = indices[idx]
        reset_single(
            i,
            batch_stage,
            batch_energy_vec,
            batch_energy_count,
            batch_continuous_vec,
            batch_continuous_ptr,
            batch_tapped,
            batch_live,
            batch_scores,
            batch_flat_ctx,
            batch_global_ctx,
            batch_hand,
            batch_deck,
            opp_stage,
            opp_energy_vec,
            opp_energy_count,
            opp_tapped,
            opp_live,
            opp_scores,
            opp_global_ctx,
            opp_hand,
            opp_deck,
            batch_trash,
            opp_trash,
            batch_opp_history,
            ability_member_ids,
            ability_live_ids,
            force_start_order,
        )


@njit(cache=True)
def encode_observations_standard(
    num_envs,
    batch_hand,
    batch_stage,
    batch_energy_count,
    batch_tapped,
    batch_scores,
    opp_scores,
    opp_stage,
    opp_tapped,
    card_stats,
    batch_global_ctx,
    batch_live,
    batch_opp_history,
    turn_number,
    observations,
):
    for i in range(num_envs):
        encode_observation_standard_single(
            i,
            batch_hand,
            batch_stage,
            batch_energy_count,
            batch_tapped,
            batch_scores,
            opp_scores,
            opp_stage,
            opp_tapped,
            card_stats,
            batch_global_ctx,
            batch_live,
            batch_opp_history,
            turn_number,
            observations,
        )
    return observations
