"""
CUDA Kernels for GPU-Accelerated VectorEnv.

This module contains CUDA kernel implementations for:
- Environment reset
- Game step (integrated with opponent, phases, scoring)
- Observation encoding
- Action mask computation

All kernels are designed for the VectorGameStateGPU class.
"""

import numpy as np

try:
    from numba import cuda
    from numba.cuda.random import xoroshiro128p_normal_float32, xoroshiro128p_uniform_float32

    HAS_CUDA = True
except ImportError:
    HAS_CUDA = False

    # Mock for type checking
    class MockCuda:
        def jit(self, *args, **kwargs):
            def decorator(f):
                return f

            return decorator

        def grid(self, x):
            return 0

    cuda = MockCuda()

    def xoroshiro128p_uniform_float32(rng, i):
        return 0.5


# ============================================================================
# CONSTANTS (Must match fast_logic.py)
# ============================================================================
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

# Opcodes
O_DRAW = 10
O_BLADES = 11
O_HEARTS = 12
O_RECOV_L = 13
O_BOOST = 14
O_RECOV_M = 15
O_BUFF = 16
O_CHARGE = 17
O_TAP_O = 18
O_CHOOSE = 19
O_ADD_H = 20
O_RETURN = 999
O_JUMP = 100
O_JUMP_F = 101

# Conditions
C_TR1 = 200
C_CLR = 202
C_STG = 203
C_HND = 204
C_CTR = 206
C_LLD = 207
C_GRP = 208
C_OPH = 210
C_ENR = 213
C_CMP = 220

# Unique ID (UID) System
BASE_ID_MASK = 0xFFFFF


@cuda.jit(device=True)
def get_base_id_device(uid: int) -> int:
    """Extract the base card definition ID (0-1999) from a UID."""
    return uid & BASE_ID_MASK


# ============================================================================
# DEVICE FUNCTIONS (Callable from kernels)
# ============================================================================


@cuda.jit(device=True)
def check_deck_refresh_device(p_deck, p_trash, p_global_ctx, DK_idx, TR_idx):
    """Shuffle trash back into deck if deck is empty."""
    if p_global_ctx[DK_idx] <= 0:
        # Count trash
        tr_count = 0
        for t in range(60):
            if p_trash[t] > 0:
                tr_count += 1

        if tr_count > 0:
            # Move trash to deck
            d_ptr = 0
            for t in range(60):
                if p_trash[t] > 0:
                    p_deck[d_ptr] = p_trash[t]
                    p_trash[t] = 0
                    d_ptr += 1

            p_global_ctx[DK_idx] = d_ptr
            p_global_ctx[TR_idx] = 0


@cuda.jit(device=True)
def move_to_trash_device(card_id, p_trash, p_global_ctx, TR_idx):
    """Move a card to trash zone."""
    for t in range(60):
        if p_trash[t] == 0:
            p_trash[t] = card_id
            p_global_ctx[TR_idx] += 1
            break


@cuda.jit(device=True)
def draw_cards_device(count, p_hand, p_deck, p_trash, p_global_ctx):
    """Draw cards from deck to hand."""
    for _ in range(count):
        check_deck_refresh_device(p_deck, p_trash, p_global_ctx, DK, TR)

        if p_global_ctx[DK] <= 0:
            break

        # Find top card in deck
        top_card = 0
        d_idx_found = -1
        for d in range(60):
            if p_deck[d] > 0:
                top_card = p_deck[d]
                d_idx_found = d
                break

        if top_card > 0:
            # Find empty hand slot
            for h in range(60):
                if p_hand[h] == 0:
                    p_hand[h] = top_card
                    p_deck[d_idx_found] = 0
                    p_global_ctx[DK] -= 1
                    p_global_ctx[HD] += 1
                    break


@cuda.jit(device=True)
def resolve_bytecode_device(
    bytecode,
    flat_ctx,
    global_ctx,
    player_id,
    p_hand,
    p_deck,
    p_stage,
    p_energy_vec,
    p_energy_count,
    p_cont_vec,
    p_cont_ptr,
    p_tapped,
    p_live,
    opp_tapped,
    p_trash,
    bytecode_map,
    bytecode_index,
):
    """
    GPU Device function for resolving bytecode.
    Returns (new_cont_ptr, status, bonus).
    """
    ip = 0
    cptr = p_cont_ptr
    bonus = 0
    cond = True
    blen = bytecode.shape[0]
    safety_counter = 0

    while ip < blen and safety_counter < 500:
        safety_counter += 1
        op = bytecode[ip, 0]
        v = bytecode[ip, 1]
        a = bytecode[ip, 2]
        s = bytecode[ip, 3]

        if op == 0:
            ip += 1
            continue
        if op == O_RETURN:
            break

        # Jumps
        if op == O_JUMP:
            new_ip = ip + v
            if 0 <= new_ip < blen:
                ip = new_ip
            else:
                break
            continue

        if op == O_JUMP_F:
            if not cond:
                new_ip = ip + v
                if 0 <= new_ip < blen:
                    ip = new_ip
                else:
                    break
                continue
            ip += 1
            continue

        # Conditions (op >= 200)
        if op >= 200:
            if op == C_TR1:
                cond = global_ctx[TR] == 1
            elif op == C_STG:
                ct = 0
                for j in range(3):
                    if p_stage[j] != -1:
                        ct += 1
                cond = ct >= v
            elif op == C_HND:
                cond = global_ctx[HD] >= v
            elif op == C_LLD:
                cond = global_ctx[SC] > global_ctx[OS]
            elif op == C_ENR:
                cond = global_ctx[EN] >= v
            elif op == C_CMP:
                if v > 0:
                    cond = global_ctx[SC] >= v
                else:
                    cond = global_ctx[SC] > global_ctx[OS]
            elif op == C_OPH:
                cond = global_ctx[OT] >= v if v > 0 else global_ctx[OT] > 0
            else:
                cond = True
            ip += 1
        else:
            # Effects
            if cond:
                if op == O_DRAW:
                    draw_cards_device(v, p_hand, p_deck, p_trash, global_ctx)
                elif op == O_CHARGE:
                    # Move cards from deck to energy (simplified)
                    amt = min(v, global_ctx[DK])
                    for _ in range(amt):
                        for d in range(60):
                            if p_deck[d] > 0:
                                p_deck[d] = 0
                                global_ctx[DK] -= 1
                                global_ctx[EN] += 1
                                break
                elif op == O_HEARTS:
                    # Add hearts (points)
                    bonus += v
                    # Register continuous effect
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 2
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 5] = a
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_BLADES:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 1
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = 4
                        p_cont_vec[cptr, 3] = s
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_RECOV_M:
                    if 0 <= s < 3:
                        p_tapped[s] = 0
                elif op == O_RECOV_L:
                    if 0 <= s < p_live.shape[0]:
                        p_live[s] = 0
                elif op == O_TAP_O:
                    if 0 <= s < 3:
                        opp_tapped[s] = 1
                elif op == O_BUFF:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 8
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_BOOST:
                    bonus += v
            ip += 1

    return cptr, 0, bonus


@cuda.jit(device=True)
def step_player_device(
    act_id,
    player_id,
    rng_state,
    i,
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
    Device function for single player step.
    Returns bonus score from this action.
    """
    bonus = 0

    if act_id == 0:
        # Pass -> Next Phase
        ph = p_global_ctx[PH]
        if ph == -1:
            p_global_ctx[PH] = 0
        elif ph == 0:
            p_global_ctx[PH] = 4  # Skip to Main
        elif ph == 4:
            p_global_ctx[PH] = 8  # Performance
        return 0

    # Member Play (1-180)
    if 1 <= act_id <= 180:
        adj = act_id - 1
        hand_idx = adj // 3
        slot = adj % 3

        if hand_idx < 60:
            card_id = p_hand[hand_idx]
            if card_id >= 0:
                bid = get_base_id_device(card_id)
                if bid < card_stats.shape[0]:
                    # Cost calculation
                    cost = card_stats[bid, 0]
                    effective_cost = cost
                    prev_cid = p_stage[slot]
                    if prev_cid >= 0:
                        prev_bid = get_base_id_device(prev_cid)
                        if prev_bid < card_stats.shape[0]:
                            prev_cost = card_stats[prev_bid, 0]
                            effective_cost = max(0, cost - prev_cost)

                # Pay cost by tapping energy
                ec = min(p_global_ctx[EN], 12)
                paid = 0
                if effective_cost > 0:
                    for e_idx in range(ec):
                        if 3 + e_idx < 16:
                            if p_tapped[3 + e_idx] == 0:
                                p_tapped[3 + e_idx] = 1
                                paid += 1
                                if paid >= effective_cost:
                                    break

                # Move to stage
                p_stage[slot] = card_id
                p_hand[hand_idx] = 0
                p_global_ctx[HD] -= 1
                p_global_ctx[51 + slot] = 1  # Mark played

                # Resolve auto-ability
                bid = get_base_id_device(card_id)
                if bid < bytecode_index.shape[0]:
                    map_idx = bytecode_index[bid, 0]
                    if map_idx >= 0:
                        flat_ctx = cuda.local.array(64, dtype=np.int32)
                        for j in range(64):
                            flat_ctx[j] = 0

                        new_ptr, _, ab_bonus = resolve_bytecode_device(
                            bytecode_map[map_idx],
                            flat_ctx,
                            p_global_ctx,
                            player_id,
                            p_hand,
                            p_deck,
                            p_stage,
                            p_energy_vec,
                            p_energy_count,
                            p_continuous_vec,
                            p_continuous_ptr[0],
                            p_tapped,
                            p_live,
                            opp_tapped,
                            p_trash,
                            bytecode_map,
                            bytecode_index,
                        )
                        p_continuous_ptr[0] = new_ptr
                        bonus += ab_bonus

    # Activate Ability (200-202)
    elif 200 <= act_id <= 202:
        slot = act_id - 200
        card_id = p_stage[slot]
        if card_id >= 0 and p_tapped[slot] == 0:
            bid = get_base_id_device(card_id)
            if bid < bytecode_index.shape[0]:
                map_idx = bytecode_index[bid, 0]
                if map_idx >= 0:
                    flat_ctx = cuda.local.array(64, dtype=np.int32)
                    for j in range(64):
                        flat_ctx[j] = 0

                    new_ptr, _, ab_bonus = resolve_bytecode_device(
                        bytecode_map[map_idx],
                        flat_ctx,
                        p_global_ctx,
                        player_id,
                        p_hand,
                        p_deck,
                        p_stage,
                        p_energy_vec,
                        p_energy_count,
                        p_continuous_vec,
                        p_continuous_ptr[0],
                        p_tapped,
                        p_live,
                        opp_tapped,
                        p_trash,
                        bytecode_map,
                        bytecode_index,
                    )
                    p_continuous_ptr[0] = new_ptr
                    bonus += ab_bonus
                    p_tapped[slot] = 1

    # Set Live Card (400-459)
    elif 400 <= act_id <= 459:
        hand_idx = act_id - 400
        if hand_idx < 60:
            card_id = p_hand[hand_idx]
            if card_id > 0:
                # Find empty live zone slot
                for j in range(50):
                    if p_live[j] == 0:
                        p_live[j] = card_id
                        p_hand[hand_idx] = 0
                        p_global_ctx[HD] -= 1
                        break

    return bonus


@cuda.jit(device=True)
def resolve_live_device(
    live_id, p_stage, p_live, p_scores, p_global_ctx, p_deck, p_hand, p_trash, card_stats, p_cont_vec, p_cont_ptr
):
    """
    Device function to resolve a live card.
    Returns the score value if successful, 0 otherwise.
    """
    bid = get_base_id_device(live_id)
    if live_id < 0 or bid >= card_stats.shape[0]:
        return 0

    # Get required hearts from card_stats (indices 12-18)
    required = cuda.local.array(7, dtype=np.int32)
    for c in range(7):
        required[c] = card_stats[bid, 12 + c]

    total_required = 0
    for c in range(7):
        total_required += required[c]

    if total_required <= 0:
        # No requirements - auto-succeed
        return card_stats[bid, 38]  # Score value

    # Calculate provided hearts from stage members
    provided = cuda.local.array(7, dtype=np.int32)
    for c in range(7):
        provided[c] = 0

    for slot in range(3):
        cid = p_stage[slot]
        if cid > 0:
            s_bid = get_base_id_device(cid)
            if s_bid < card_stats.shape[0]:
                for c in range(7):
                    provided[c] += card_stats[s_bid, 12 + c]

    # Check if requirements met
    for c in range(6):  # Colors (not All)
        if required[c] > provided[c]:
            return 0  # Failed

    # All requirements met
    return card_stats[bid, 38]


@cuda.jit(device=True)
def run_opponent_turn_device(
    rng_state,
    i,
    opp_hand,
    opp_deck,
    opp_stage,
    opp_energy_vec,
    opp_energy_count,
    opp_tapped,
    opp_live,
    opp_scores,
    opp_global_ctx,
    opp_trash,
    p_tapped,
    opp_history,
    card_stats,
    bytecode_map,
    bytecode_index,
):
    """
    Simple heuristic opponent turn.
    Plays members if possible, activates abilities, sets lives.
    """
    # Play up to 3 members in empty slots
    for slot in range(3):
        if opp_stage[slot] == -1:
            # Find playable member in hand
            for h in range(60):
                cid = opp_hand[h]
                if cid >= 0:
                    bid = get_base_id_device(cid)
                    if bid < card_stats.shape[0]:
                        ctype = card_stats[bid, 10]
                        if ctype == 1:  # Member
                            cost = card_stats[bid, 0]
                            if cost <= opp_global_ctx[EN]:
                                # Play it
                                opp_stage[slot] = cid
                                opp_hand[h] = 0
                                opp_global_ctx[HD] -= 1
                                # Update History
                                for k in range(5, 0, -1):
                                    opp_history[i, k] = opp_history[i, k - 1]
                                opp_history[i, 0] = cid
                                break

    # Set a live card if possible
    for h in range(60):
        cid = opp_hand[h]
        if cid >= 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                ctype = card_stats[bid, 10]
                if ctype == 2:  # Live
                    for lz in range(50):
                        if opp_live[lz] == 0:
                            opp_live[lz] = cid
                            opp_hand[h] = 0
                            opp_global_ctx[HD] -= 1
                            # Update History
                            for k in range(5, 0, -1):
                                opp_history[i, k] = opp_history[i, k - 1]
                            opp_history[i, 0] = cid
                            break
                    break


# ============================================================================
# MAIN KERNELS
# ============================================================================


@cuda.jit
def reset_kernel(
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
    batch_trash,
    batch_opp_history,
    opp_stage,
    opp_energy_vec,
    opp_energy_count,
    opp_tapped,
    opp_live,
    opp_scores,
    opp_global_ctx,
    opp_hand,
    opp_deck,
    opp_trash,
    ability_member_ids,
    ability_live_ids,
    rng_states,
    force_start_order,
    obs_buffer,
    card_stats,
):
    """
    CUDA Kernel to reset environments.
    """
    tid = cuda.grid(1)
    if tid >= indices.shape[0]:
        return

    i = indices[tid]

    # Clear agent state
    for j in range(3):
        batch_stage[i, j] = -1
    for j in range(3):
        for k in range(32):
            batch_energy_vec[i, j, k] = 0
        batch_energy_count[i, j] = 0
    for j in range(32):
        for k in range(10):
            batch_continuous_vec[i, j, k] = 0
    batch_continuous_ptr[i] = 0
    for j in range(16):
        batch_tapped[i, j] = 0
    for j in range(50):
        batch_live[i, j] = 0
    batch_scores[i] = 0
    for j in range(64):
        batch_flat_ctx[i, j] = 0
    for j in range(128):
        batch_global_ctx[i, j] = 0
    for j in range(60):
        batch_trash[i, j] = 0
    for j in range(6):
        batch_opp_history[i, j] = 0

    # Clear opponent state
    for j in range(3):
        opp_stage[i, j] = -1
    for j in range(3):
        for k in range(32):
            opp_energy_vec[i, j, k] = 0
        opp_energy_count[i, j] = 0
    for j in range(16):
        opp_tapped[i, j] = 0
    for j in range(50):
        opp_live[i, j] = 0
    opp_scores[i] = 0
    for j in range(128):
        opp_global_ctx[i, j] = 0
    for j in range(60):
        opp_trash[i, j] = 0

    # Generate deck
    n_members = ability_member_ids.shape[0]
    n_lives = ability_live_ids.shape[0]

    # Members (0-47)
    for k in range(48):
        if n_members == 48:
            batch_deck[i, k] = ability_member_ids[k]
            opp_deck[i, k] = ability_member_ids[k]
        else:
            # Random pick using RNG
            r = xoroshiro128p_uniform_float32(rng_states, i)
            idx = int(r * n_members) % n_members
            batch_deck[i, k] = ability_member_ids[idx]
            r = xoroshiro128p_uniform_float32(rng_states, i)
            idx = int(r * n_members) % n_members
            opp_deck[i, k] = ability_member_ids[idx]

    # Lives (48-59)
    for k in range(12):
        if n_lives == 12:
            batch_deck[i, 48 + k] = ability_live_ids[k]
            opp_deck[i, 48 + k] = ability_live_ids[k]
        else:
            r = xoroshiro128p_uniform_float32(rng_states, i)
            idx = int(r * n_lives) % n_lives
            batch_deck[i, 48 + k] = ability_live_ids[idx]
            r = xoroshiro128p_uniform_float32(rng_states, i)
            idx = int(r * n_lives) % n_lives
            opp_deck[i, 48 + k] = ability_live_ids[idx]

    # Shuffle decks (Fisher-Yates)
    for k in range(59, 0, -1):
        r = xoroshiro128p_uniform_float32(rng_states, i)
        j = int(r * (k + 1)) % (k + 1)
        tmp = batch_deck[i, k]
        batch_deck[i, k] = batch_deck[i, j]
        batch_deck[i, j] = tmp

        r = xoroshiro128p_uniform_float32(rng_states, i)
        j = int(r * (k + 1)) % (k + 1)
        tmp = opp_deck[i, k]
        opp_deck[i, k] = opp_deck[i, j]
        opp_deck[i, j] = tmp

    # Place 2 cards in Live Zone
    batch_live[i, 0] = batch_deck[i, 0]
    batch_live[i, 1] = batch_deck[i, 1]
    batch_deck[i, 0] = 0
    batch_deck[i, 1] = 0

    opp_live[i, 0] = opp_deck[i, 0]
    opp_live[i, 1] = opp_deck[i, 1]
    opp_deck[i, 0] = 0
    opp_deck[i, 1] = 0

    # Draw hand (6 cards)
    for j in range(60):
        batch_hand[i, j] = 0
        opp_hand[i, j] = 0

    drawn = 0
    for k in range(2, 60):
        if batch_deck[i, k] > 0 and drawn < 6:
            batch_hand[i, drawn] = batch_deck[i, k]
            batch_deck[i, k] = 0
            drawn += 1

    drawn_o = 0
    for k in range(2, 60):
        if opp_deck[i, k] > 0 and drawn_o < 6:
            opp_hand[i, drawn_o] = opp_deck[i, k]
            opp_deck[i, k] = 0
            drawn_o += 1

    # Set initial global context
    batch_global_ctx[i, HD] = 6
    batch_global_ctx[i, DK] = 52
    batch_global_ctx[i, EN] = 3
    batch_global_ctx[i, PH] = 4  # Start in Main phase (simplified)
    batch_global_ctx[i, 54] = 1  # Turn 1

    opp_global_ctx[i, HD] = 6
    opp_global_ctx[i, DK] = 52
    opp_global_ctx[i, EN] = 3
    opp_global_ctx[i, PH] = 4
    opp_global_ctx[i, 54] = 1

    # Start order
    if force_start_order == -1:
        r = xoroshiro128p_uniform_float32(rng_states, i)
        is_second = 1 if r > 0.5 else 0
    else:
        is_second = force_start_order
    batch_global_ctx[i, 10] = is_second


@cuda.jit
def step_kernel(
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
    obs_buffer,
    rewards,
    dones,
    prev_scores,
    prev_opp_scores,
    prev_phases,
    terminal_obs_buffer,
    batch_trash,
    opp_trash,
    batch_opp_history,
    term_scores_agent,
    term_scores_opp,
    ability_member_ids,
    ability_live_ids,
    rng_states,
    game_config,
    opp_mode,
    force_start_order,
):
    """
    Main integrated step kernel.
    Processes one environment per thread.
    """
    i = cuda.grid(1)
    if i >= num_envs:
        return

    # Config
    CFG_TURN_LIMIT = int(game_config[0])
    CFG_STEP_LIMIT = int(game_config[1])
    CFG_REWARD_WIN = game_config[2]
    CFG_REWARD_LOSE = game_config[3]
    CFG_REWARD_SCALE = game_config[4]
    CFG_REWARD_TURN_PENALTY = game_config[5]

    act_id = actions[i]
    ph = int(batch_global_ctx[i, PH])

    # Sync score to context
    batch_global_ctx[i, SC] = batch_scores[i]

    # Increment step counter
    batch_global_ctx[i, 58] += 1

    # Get continuous pointer slice
    cont_ptr_arr = batch_continuous_ptr[i : i + 1]
    score_arr = batch_scores[i : i + 1]

    # Execute action
    bonus = step_player_device(
        act_id,
        0,
        rng_states,
        i,
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
        cont_ptr_arr,
        opp_tapped[i],
        card_stats,
        bytecode_map,
        bytecode_index,
    )
    batch_scores[i] += bonus

    # Handle turn end (Pass in Main Phase)
    if act_id == 0 and ph == 4:
        # Run opponent turn
        run_opponent_turn_device(
            rng_states,
            i,
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
            batch_tapped[i],
            batch_opp_history,
            card_stats,
            bytecode_map,
            bytecode_index,
        )

        # Resolve lives for both players
        agent_live_score = 0
        opp_live_score = 0

        for z in range(10):
            lid = batch_live[i, z]
            if lid > 0:
                s = resolve_live_device(
                    lid,
                    batch_stage[i],
                    batch_live[i],
                    batch_scores[i : i + 1],
                    batch_global_ctx[i],
                    batch_deck[i],
                    batch_hand[i],
                    batch_trash[i],
                    card_stats,
                    batch_continuous_vec[i],
                    cont_ptr_arr,
                )
                agent_live_score += s
                # Clear used live
                if s > 0:
                    move_to_trash_device(lid, batch_trash[i], batch_global_ctx[i], TR)
                    batch_live[i, z] = 0

        for z in range(10):
            lid = opp_live[i, z]
            if lid > 0:
                s = resolve_live_device(
                    lid,
                    opp_stage[i],
                    opp_live[i],
                    opp_scores[i : i + 1],
                    opp_global_ctx[i],
                    opp_deck[i],
                    opp_hand[i],
                    opp_trash[i],
                    card_stats,
                    batch_continuous_vec[i],
                    cont_ptr_arr,
                )
                opp_live_score += s
                if s > 0:
                    move_to_trash_device(lid, opp_trash[i], opp_global_ctx[i], TR)
                    opp_live[i, z] = 0

        # Scoring comparison
        if agent_live_score > 0 and opp_live_score == 0:
            batch_scores[i] += 1
        elif agent_live_score == 0 and opp_live_score > 0:
            opp_scores[i] += 1
        elif agent_live_score > 0 and opp_live_score > 0:
            if agent_live_score > opp_live_score:
                batch_scores[i] += 1
            elif opp_live_score > agent_live_score:
                opp_scores[i] += 1
            else:
                # Tie - both score
                batch_scores[i] += 1
                opp_scores[i] += 1

        # Next turn setup
        batch_global_ctx[i, 54] += 1
        opp_global_ctx[i, 54] += 1

        # Untap and energy
        for j in range(16):
            batch_tapped[i, j] = 0
            if j < opp_tapped.shape[1]:
                opp_tapped[i, j] = 0

        batch_global_ctx[i, EN] = min(batch_global_ctx[i, EN] + 1, 12)
        opp_global_ctx[i, EN] = min(opp_global_ctx[i, EN] + 1, 12)

        # Draw card
        draw_cards_device(1, batch_hand[i], batch_deck[i], batch_trash[i], batch_global_ctx[i])
        draw_cards_device(1, opp_hand[i], opp_deck[i], opp_trash[i], opp_global_ctx[i])

    # Calculate rewards
    current_score = batch_scores[i]
    score_diff = float(current_score) - float(prev_scores[i])
    opp_score_diff = float(opp_scores[i]) - float(prev_opp_scores[i])

    r = (score_diff * CFG_REWARD_SCALE) - (opp_score_diff * CFG_REWARD_SCALE)
    r += CFG_REWARD_TURN_PENALTY

    win = current_score >= 3
    lose = opp_scores[i] >= 3

    if win:
        r += CFG_REWARD_WIN
    if lose:
        r += CFG_REWARD_LOSE

    rewards[i] = r

    # Sync Opp Stats to Agent Context (for Attention features)
    batch_global_ctx[i, 4] = opp_global_ctx[i, 3]  # HD
    batch_global_ctx[i, 9] = opp_global_ctx[i, 6]  # DK
    batch_global_ctx[i, 7] = opp_global_ctx[i, 2]  # TR

    # Check done
    is_done = win or lose or batch_global_ctx[i, 54] >= CFG_TURN_LIMIT or batch_global_ctx[i, 58] >= CFG_STEP_LIMIT
    dones[i] = is_done

    if is_done:
        term_scores_agent[i] = batch_scores[i]
        term_scores_opp[i] = opp_scores[i]
        # Note: Auto-reset should be called separately

    # Update prev scores
    prev_scores[i] = batch_scores[i]
    prev_opp_scores[i] = opp_scores[i]


@cuda.jit
def compute_action_masks_kernel(
    num_envs,
    batch_hand,
    batch_stage,
    batch_tapped,
    batch_global_ctx,
    batch_live,
    card_stats,
    masks,  # Output: (N, 2000)
):
    """
    Compute legal action masks on GPU.
    """
    i = cuda.grid(1)
    if i >= num_envs:
        return

    # Reset all to False
    for a in range(2000):
        masks[i, a] = False

    ph = batch_global_ctx[i, PH]

    # Action 0: Pass is always legal in Main Phase
    if ph == 4:
        masks[i, 0] = True

    # Member Play (1-180): HandIdx * 3 + Slot + 1
    for h_idx in range(60):
        cid = batch_hand[i, h_idx]
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                ctype = card_stats[bid, 10]
                cost = card_stats[bid, 0]

                if ctype == 1:  # Member
                    for slot in range(3):
                        # Check if slot empty or can upgrade
                        old_cid = batch_stage[i, slot]
                        effective_cost = cost
                        if old_cid >= 0:
                            old_bid = get_base_id_device(old_cid)
                            if old_bid < card_stats.shape[0]:
                                effective_cost = max(0, cost - card_stats[old_bid, 0])

                        # Check energy
                        available_energy = 0
                        for e in range(12):
                            if batch_tapped[i, 3 + e] == 0:
                                available_energy += 1

                        if available_energy >= effective_cost:
                            action_id = h_idx * 3 + slot + 1
                            if action_id < 181:
                                masks[i, action_id] = True

    # Activate Ability (200-202)
    for slot in range(3):
        cid = batch_stage[i, slot]
        if cid > 0 and batch_tapped[i, slot] == 0:
            masks[i, 200 + slot] = True

    # Set Live (400-459)
    for h_idx in range(60):
        cid = batch_hand[i, h_idx]
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                ctype = card_stats[bid, 10]
                if ctype == 2:  # Live
                    # Check if there's an empty live zone slot
                    for lz_idx in range(50):
                        if batch_live[i, lz_idx] == 0:
                            if h_idx < 60:  # This check is redundant due to outer loop
                                masks[i, 400 + h_idx] = True
                                break  # Only need one empty slot to make it legal


@cuda.jit
def encode_observations_kernel(
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
    turn_number,
    obs_buffer,
):
    """
    Encode observations on GPU (STANDARD mode).
    """
    i = cuda.grid(1)
    if i >= num_envs:
        return

    obs_dim = obs_buffer.shape[1]

    # Clear observation
    for j in range(obs_dim):
        obs_buffer[i, j] = 0.0

    # Metadata
    obs_buffer[i, 0] = float(batch_scores[i]) / 3.0
    obs_buffer[i, 1] = float(opp_scores[i]) / 3.0
    obs_buffer[i, 2] = float(batch_global_ctx[i, EN]) / 12.0
    obs_buffer[i, 3] = float(batch_global_ctx[i, HD]) / 60.0
    obs_buffer[i, 4] = float(batch_global_ctx[i, DK]) / 60.0
    obs_buffer[i, 5] = float(batch_global_ctx[i, 54]) / 100.0  # Turn

    offset = 10

    # Stage (3 slots x 20 features)
    for slot in range(3):
        cid = batch_stage[i, slot]
        base = offset + slot * 20
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                obs_buffer[i, base] = 1.0  # Presence
                obs_buffer[i, base + 1] = float(cid) / 2000.0
                obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0  # Cost
                obs_buffer[i, base + 3] = float(card_stats[bid, 1]) / 5.0  # Blades
                obs_buffer[i, base + 4] = float(card_stats[bid, 2]) / 10.0  # Hearts
                obs_buffer[i, base + 5] = 1.0 if batch_tapped[i, slot] > 0 else 0.0

    offset += 60

    # Opponent Stage
    for slot in range(3):
        cid = opp_stage[i, slot]
        base = offset + slot * 20
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                obs_buffer[i, base] = 1.0
                obs_buffer[i, base + 1] = float(cid) / 2000.0
                obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0
                obs_buffer[i, base + 3] = float(card_stats[bid, 1]) / 5.0
                obs_buffer[i, base + 4] = float(card_stats[bid, 2]) / 10.0

    offset += 60

    # Hand (up to 20 cards shown)
    h_count = 0
    for h_idx in range(60):
        cid = batch_hand[i, h_idx]
        if cid > 0 and h_count < 20:
            base = offset + h_count * 20
            if base + 10 < obs_dim:
                obs_buffer[i, base] = 1.0
                obs_buffer[i, base + 1] = float(cid) / 2000.0
                bid = get_base_id_device(cid)
                if bid < card_stats.shape[0]:
                    obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0
                    obs_buffer[i, base + 3] = float(card_stats[bid, 10])  # Type
            h_count += 1

    offset += 400

    # Live zone (up to 10 cards)
    l_count = 0
    for l_idx in range(50):
        cid = batch_live[i, l_idx]
        if cid > 0 and l_count < 10:
            base = offset + l_count * 10
            if base + 5 < obs_dim:
                obs_buffer[i, base] = 1.0
                obs_buffer[i, base + 1] = float(cid) / 2000.0
            l_count += 1


@cuda.jit
def encode_observations_attention_kernel(
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
    opp_global_ctx,  # Added
    turn_number,
    obs_buffer,
):
    """
    Encode observations for Attention Architecture (2240-dim).
    """
    i = cuda.grid(1)
    if i >= num_envs:
        return

    # Constants
    FEAT = 64
    MAX_HAND = 15  # +1 overflow

    # Offsets
    HAND_START = 0
    HAND_OVER_START = HAND_START + (MAX_HAND * FEAT)  # 960
    STAGE_START = HAND_OVER_START + FEAT  # 1024
    LIVE_START = STAGE_START + (3 * FEAT)  # 1216
    LIVE_SUCC_START = LIVE_START + (3 * FEAT)  # 1408
    OPP_STAGE_START = LIVE_SUCC_START + (3 * FEAT)  # 1600
    OPP_HIST_START = OPP_STAGE_START + (3 * FEAT)  # 1792
    GLOBAL_START = OPP_HIST_START + (6 * FEAT)  # 2176

    # Clear buffer
    for k in range(2240):
        obs_buffer[i, k] = 0.0

    # --- A. HAND (16 slots) ---
    hand_count = 0
    for j in range(60):
        cid = batch_hand[i, j]
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                if hand_count < 16:
                    base = HAND_START + hand_count * FEAT

                    obs_buffer[i, base + 0] = 1.0  # Presence
                    obs_buffer[i, base + 1] = float(card_stats[bid, 10]) / 2.0  # Type
                    obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0  # Cost
                    obs_buffer[i, base + 3] = float(card_stats[bid, 1]) / 5.0  # Blades
                    obs_buffer[i, base + 5] = float(cid) / 2000.0  # Card ID (New)
                    obs_buffer[i, base + 6] = 0.2  # Location: Hand

                    # Hearts (8-14)
                    for k in range(7):
                        if 12 + k < card_stats.shape[1]:
                            obs_buffer[i, base + 8 + k] = float(card_stats[bid, 12 + k]) / 5.0

                    # Group (22-28)
                    raw_group = card_stats[bid, 11]
                    obs_buffer[i, base + 22 + (raw_group % 7)] = 1.0

                    # Context
                    obs_buffer[i, base + 58] = float(hand_count) / 10.0
                    obs_buffer[i, base + 59] = 1.0  # Mine

                    hand_count += 1

    # --- B. MY STAGE (3 slots) ---
    for slot in range(3):
        cid = batch_stage[i, slot]
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                base = STAGE_START + slot * FEAT

                obs_buffer[i, base + 0] = 1.0
                obs_buffer[i, base + 1] = float(card_stats[bid, 10]) / 2.0
                obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0
                obs_buffer[i, base + 3] = float(card_stats[bid, 1]) / 5.0
                obs_buffer[i, base + 4] = 1.0 if batch_tapped[i, slot] > 0 else 0.0
                obs_buffer[i, base + 5] = float(cid) / 2000.0  # Card ID (New)
                obs_buffer[i, base + 6] = 0.4  # Location: Stage

                for k in range(7):
                    if 12 + k < card_stats.shape[1]:
                        obs_buffer[i, base + 8 + k] = float(card_stats[bid, 12 + k]) / 5.0

                raw_group = card_stats[bid, 11]
                obs_buffer[i, base + 22 + (raw_group % 7)] = 1.0

                obs_buffer[i, base + 58] = float(slot) / 10.0
                obs_buffer[i, base + 59] = 1.0

    # --- C. LIVE ZONE (6 slots) ---
    live_count = 0
    for j in range(50):
        cid = batch_live[i, j]
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0] and live_count < 6:
                base = LIVE_START + live_count * FEAT

                obs_buffer[i, base + 0] = 1.0
                obs_buffer[i, base + 1] = float(card_stats[bid, 10]) / 2.0
                obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0
                obs_buffer[i, base + 5] = float(cid) / 2000.0  # Card ID (New)
                obs_buffer[i, base + 6] = 0.6  # Location: Live

                for k in range(7):
                    if 12 + k < card_stats.shape[1]:
                        obs_buffer[i, base + 8 + k] = float(card_stats[bid, 12 + k]) / 5.0

                obs_buffer[i, base + 58] = float(live_count) / 10.0
                obs_buffer[i, base + 59] = 1.0
                live_count += 1

    # --- D. OPP STAGE (3 slots) ---
    for slot in range(3):
        cid = opp_stage[i, slot]
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                base = OPP_STAGE_START + slot * FEAT

                obs_buffer[i, base + 0] = 1.0
                obs_buffer[i, base + 1] = float(card_stats[bid, 10]) / 2.0
                obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0
                obs_buffer[i, base + 3] = float(card_stats[bid, 1]) / 5.0
                obs_buffer[i, base + 4] = 1.0 if opp_tapped[i, slot] > 0 else 0.0
                obs_buffer[i, base + 5] = float(cid) / 2000.0  # Card ID (New)
                obs_buffer[i, base + 6] = 0.8  # Location: Opp Stage

                for k in range(7):
                    if 12 + k < card_stats.shape[1]:
                        obs_buffer[i, base + 8 + k] = float(card_stats[bid, 12 + k]) / 5.0

                obs_buffer[i, base + 58] = float(slot) / 10.0
                obs_buffer[i, base + 59] = -1.0

    # --- E. OPP HISTORY (6 slots) ---
    for h in range(6):
        cid = batch_opp_history[i, h]
        if cid > 0:
            bid = get_base_id_device(cid)
            if bid < card_stats.shape[0]:
                base = OPP_HIST_START + h * FEAT

                obs_buffer[i, base + 0] = 1.0
                obs_buffer[i, base + 1] = float(card_stats[bid, 10]) / 2.0
                obs_buffer[i, base + 2] = float(card_stats[bid, 0]) / 10.0
                obs_buffer[i, base + 5] = float(cid) / 2000.0  # Card ID (New)
                obs_buffer[i, base + 6] = 1.0  # Location: History

                obs_buffer[i, base + 58] = float(h) / 10.0
                obs_buffer[i, base + 59] = -1.0

    # --- F. GLOBAL SCALARS ---
    obs_buffer[i, GLOBAL_START + 0] = float(batch_scores[i]) / 10.0
    obs_buffer[i, GLOBAL_START + 1] = float(opp_scores[i]) / 10.0
    obs_buffer[i, GLOBAL_START + 2] = float(batch_global_ctx[i, 54]) / 20.0  # Turn from Context
    obs_buffer[i, GLOBAL_START + 3] = float(batch_global_ctx[i, 8]) / 10.0
    obs_buffer[i, GLOBAL_START + 4] = float(batch_global_ctx[i, 5]) / 10.0
    obs_buffer[i, GLOBAL_START + 5] = float(batch_global_ctx[i, 6]) / 40.0
    obs_buffer[i, GLOBAL_START + 6] = float(hand_count) / 15.0

    # Opponent Resources (New)
    obs_buffer[i, GLOBAL_START + 7] = float(opp_global_ctx[i, 5]) / 10.0  # Opp Energy
    obs_buffer[i, GLOBAL_START + 8] = float(batch_global_ctx[i, 4]) / 10.0  # Opp Hand (from ctx[4])
    obs_buffer[i, GLOBAL_START + 9] = float(batch_global_ctx[i, 9]) / 40.0  # Opp Deck (from ctx[9])
    obs_buffer[i, GLOBAL_START + 10] = float(batch_global_ctx[i, 7]) / 10.0  # Opp Trash (from ctx[7])
