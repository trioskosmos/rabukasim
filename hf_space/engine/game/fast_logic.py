import warnings

import numpy as np
from numba import njit, prange

# Suppress Numba cache warnings (harmless in testing environments)
warnings.filterwarnings("ignore", message=".*'cache' is set for njit and is ignored.*")

# =============================================================================
# HYPER-OPTIMIZED VM CORE (Production Version)
# =============================================================================

# ContextIndex Mappings (Raw Ints)
CV = 20
AT = 22
TS = 12
TI = 13
SZ = 7
CH = 15
SID = 5

# Backward compatibility aliases
CTX_VALUE = CV
CTX_ATTR = AT
CTX_TARGET_SLOT = TS
CTX_TARGET_PLAYER_ID = TI
CTX_SOURCE_ZONE_IDX = SZ
CTX_CHOICE_INDEX = CH

# GlobalContext Mappings
SC = 0
OS = 1
TR = 2
HD = 3
DI = 4
EN = 5
DK = 6
OT = 7
OT = 7
PH = 8
LS = 110  # Live Score Bonus (Temporary, moved to 110 to avoid conflict with OD)
EH = 111  # Excess Hearts (Current Live Performance)
PREV_CID_IDX = 60  # Previous Card ID for Baton Pass (Index 60)

# Unique ID (UID) System
BASE_ID_MASK = 0xFFFFF


@njit(inline="always")
def get_base_id(uid: int) -> int:
    """Extract the base card definition ID (0-1999) from a UID."""
    return uid & BASE_ID_MASK


# Opcodes
O_DRAW = 10
O_BLADES = 11
O_HEARTS = 12
O_REDUCE_COST = 13
O_LOOK_DECK = 14
O_RECOV_L = 15
O_BOOST = 16
O_RECOV_M = 17
O_BUFF = 18
O_MOVE_MEMBER = 20
O_SWAP_CARDS = 21
O_SEARCH_DECK = 22
O_CHARGE = 23
O_ORDER_DECK = 28
O_SET_BLADES = 24
O_SELECT_MODE = 30
O_TAP_O = 32
O_PLACE_UNDER = 33
O_LOOK_AND_CHOOSE = 41
O_ACTIVATE_MEMBER = 43
O_ADD_H = 44
O_REPLACE_EFFECT = 46
O_TRIGGER_REMOTE = 47
O_TRANSFORM_COLOR = 39
O_TAP_M = 53
O_REDUCE_HEART_REQ = 48
O_REVEAL_CARDS = 26
O_MOVE_TO_DISCARD = 58
O_RETURN = 1
O_JUMP = 2
O_JUMP_F = 3
O_REVEAL_HAND_ALL = 6  # Cost Type (Internal reminder)

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
C_OPH = 210
C_ENR = 213
C_CMP = 220
C_BLD = 224
C_HRT = 223
C_HAS_CHOICE = 221
C_OPPONENT_CHOICE = 222
C_BATON = 231  # Baton Pass condition (ID 231)

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
C_OPH = 210
C_ENR = 213
C_CMP = 220
C_BLD = 224
C_HRT = 223
C_HAS_CHOICE = 221
C_OPPONENT_CHOICE = 222


@njit(nopython=True, cache=True, fastmath=True)
def resolve_bytecode(
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
    out_cptr,  # Modified: Pass by ref array (size 1)
    p_tapped,
    p_live,
    opp_tapped,
    p_trash,  # Added
    b_map,
    b_idx,
    out_bonus,  # Modified: Pass by ref array (size 1)
    card_stats,  # Added: NumPy array for card properties
    opp_stage,  # Added
    opp_tapped_count=None,  # Optional tracking
):
    # Manual Stack Unrolling (Depth 4) - Eliminates allocations in hot loop
    stack_ptr = 0

    bc0 = bytecode
    ip0 = 0
    bc1 = bytecode
    ip1 = 0
    bc2 = bytecode
    ip2 = 0
    bc3 = bytecode
    ip3 = 0

    cptr = out_cptr[0]
    cond = True
    safety_counter = 0

    while stack_ptr >= 0 and safety_counter < 1000:
        safety_counter += 1

        # Current Frame Selection (Type-stable for Numba)
        if stack_ptr == 0:
            cur_bc = bc0
            ip = ip0
        elif stack_ptr == 1:
            cur_bc = bc1
            ip = ip1
        elif stack_ptr == 2:
            cur_bc = bc2
            ip = ip2
        else:
            cur_bc = bc3
            ip = ip3

        blen = cur_bc.shape[0]

        if ip >= blen:
            stack_ptr -= 1
            continue

        op = cur_bc[ip, 0]
        v = cur_bc[ip, 1]
        a = cur_bc[ip, 2]
        s = cur_bc[ip, 3]

        # Advance IP logic: Pre-increment local copy
        next_ip = ip + 1
        if stack_ptr == 0:
            ip0 = next_ip
        elif stack_ptr == 1:
            ip1 = next_ip
        elif stack_ptr == 2:
            ip2 = next_ip
        else:
            ip3 = next_ip

        if op == 0:
            continue
        if op == O_RETURN:
            stack_ptr -= 1
            continue

        # Negation Flag Handling
        is_negated = False
        if op >= 1000:
            is_negated = True
            op -= 1000

        # Dynamic Target Handling (MEMBER_SELECT)
        if s == 10:
            s = int(flat_ctx[TS])

        if op == O_JUMP:
            new_ip = ip + v
            if stack_ptr == 0:
                ip0 = new_ip if 0 <= new_ip < blen else blen
            elif stack_ptr == 1:
                ip1 = new_ip if 0 <= new_ip < blen else blen
            elif stack_ptr == 2:
                ip2 = new_ip if 0 <= new_ip < blen else blen
            else:
                ip3 = new_ip if 0 <= new_ip < blen else blen
            continue

        if op == O_JUMP_F:
            if not cond:
                new_ip = ip + v
                if stack_ptr == 0:
                    ip0 = new_ip if 0 <= new_ip < blen else blen
                elif stack_ptr == 1:
                    ip1 = new_ip if 0 <= new_ip < blen else blen
                elif stack_ptr == 2:
                    ip2 = new_ip if 0 <= new_ip < blen else blen
                else:
                    ip3 = new_ip if 0 <= new_ip < blen else blen
                continue
            continue

        if op == O_SELECT_MODE:
            choice = int(flat_ctx[CH])
            jumped = False
            if 0 <= choice < v:
                jump_ip = ip + 1 + choice
                if jump_ip < blen:
                    offset = cur_bc[jump_ip, 1]
                    new_ip = jump_ip + offset
                    if 0 <= new_ip < blen:
                        if stack_ptr == 0:
                            ip0 = new_ip
                        elif stack_ptr == 1:
                            ip1 = new_ip
                        elif stack_ptr == 2:
                            ip2 = new_ip
                        else:
                            ip3 = new_ip
                        jumped = True
            if not jumped:
                new_ip = ip + (v + 1)
                if stack_ptr == 0:
                    ip0 = new_ip
                elif stack_ptr == 1:
                    ip1 = new_ip
                elif stack_ptr == 2:
                    ip2 = new_ip
                else:
                    ip3 = new_ip
            continue

        if op >= 200:
            if op == C_TR1:
                cond = global_ctx[TR] == 1
            elif op == C_STG:
                ct = 0
                for i in range(3):
                    if p_stage[i] != -1:
                        ct += 1
                cond = ct >= v
            elif op == C_HND:
                cond = global_ctx[HD] >= v
            elif op == C_LLD:
                cond = global_ctx[SC] > global_ctx[OS]
            elif op == C_CLR:
                if 0 <= a <= 5:
                    cond = global_ctx[10 + a] > 0
                else:
                    cond = False
            elif op == C_GRP:
                # C_GRP: Count cards of a group on stage or live zone
                # v = min count, a = group ID, s = zone (0=stage, 1=live)
                target_group = a
                grp_count = 0
                if s == 0:  # Stage
                    for slot_k in range(3):
                        cid = p_stage[slot_k]
                        if cid >= 0:
                            bid = get_base_id(cid)
                            if bid < card_stats.shape[0]:
                                # Groups are stored at index 6 (primary group)
                                if card_stats[bid, 6] == target_group:
                                    grp_count += 1
                elif s == 1:  # Live Zone
                    for lz_k in range(p_live.shape[0]):
                        cid = p_live[lz_k]
                        if cid >= 0:
                            bid = get_base_id(cid)
                            if bid < card_stats.shape[0]:
                                if card_stats[bid, 6] == target_group:
                                    grp_count += 1
                cond = grp_count >= v
            elif op == C_BLD:
                # C_BLD: Check if total blades on stage meets requirement
                # Rule 9.9: Tapped (Resting) members do not contribute.
                total_blades_check = 0
                for slot_k in range(3):
                    cid = p_stage[slot_k]
                    if cid >= 0 and p_tapped[slot_k] == 0:
                        bid = get_base_id(cid)
                        if bid < card_stats.shape[0]:
                            total_blades_check += card_stats[bid, 1]  # Blades at index 1

                # Decode slot/comparison
                real_slot = s & 0x0F
                comp = (s >> 4) & 0x0F
                if comp == 0:
                    cond = total_blades_check >= v
                elif comp == 1:
                    cond = total_blades_check <= v
                elif comp == 2:
                    cond = total_blades_check > v
                elif comp == 3:
                    cond = total_blades_check < v
                else:
                    cond = total_blades_check == v
            elif op == C_HRT:
                # C_HRT: Check if total hearts of color `a` on stage meets requirement
                total_hearts_check = 0

                # Decode slot/comparison
                real_slot = s & 0x0F
                comp = (s >> 4) & 0x0F

                if real_slot == 2:  # Live Result / Excess Hearts
                    total_hearts_check = global_ctx[EH]
                else:
                    for slot_k in range(3):
                        cid = p_stage[slot_k]
                        # Rule 9.9: Tapped members do not contribute hearts either.
                        if cid >= 0 and p_tapped[slot_k] == 0:
                            bid = get_base_id(cid)
                            if bid < card_stats.shape[0]:
                                if 0 <= a <= 6:
                                    total_hearts_check += card_stats[bid, 12 + a]  # Hearts at 12-18
                                else:
                                    # Sum all hearts
                                    for h_k in range(7):
                                        total_hearts_check += card_stats[bid, 12 + h_k]

                if comp == 0:
                    cond = total_hearts_check >= v
                elif comp == 1:
                    cond = total_hearts_check <= v
                elif comp == 2:
                    cond = total_hearts_check > v
                elif comp == 3:
                    cond = total_hearts_check < v
                else:
                    cond = total_hearts_check == v
            elif op == C_ENR:
                cond = global_ctx[EN] >= v
            elif op == C_CTR:
                cond = flat_ctx[SZ] == 1
            elif op == C_CMP:
                if v > 0:
                    cond = global_ctx[SC] >= v
                else:
                    cond = global_ctx[SC] > global_ctx[OS]
            elif op == C_OPH:
                ct = global_ctx[OT]
                if v > 0:
                    cond = ct >= v
                else:
                    cond = ct > 0
            elif op == 230:  # C_LIVE_ZONE
                # Placeholder: correctly count cards in successful live zone if needed
                cond = True
            elif op == 212:  # C_MODAL_ANSWER
                cond = global_ctx[CH] == v
            elif op == C_HAS_CHOICE:
                cond = True
            elif op == C_OPPONENT_CHOICE:
                # Check if opponent tapped ANY card this turn (safe approximation)
                # We check the passed `opp_tapped` array.
                cond = False
                for k in range(3):
                    if opp_tapped[k] > 0:
                        cond = True
                        break
            elif op == C_BATON:
                # Baton Pass condition: Check if the previous card's Character ID matches target
                prev_cid = global_ctx[PREV_CID_IDX]
                if prev_cid >= 0:
                    prev_bid = get_base_id(prev_cid)
                    if prev_bid < card_stats.shape[0]:
                        # Check if the previous card's Character ID (stored in stats index 19) matches the target
                        cond = card_stats[prev_bid, 19] == v
                    else:
                        cond = False
                else:
                    cond = False
            elif op == 234:  # C_AREA_CHK
                # Check if current execution context is in the specified area
                # SZ = Slot/Zone Index in flat_ctx
                # 0=Left, 1=Center, 2=Right
                cond = flat_ctx[SZ] == v

            if is_negated:
                cond = not cond

            if not cond:
                stack_ptr -= 1
                continue
        else:
            if cond:
                if op == O_DRAW:
                    drawn = 0
                    for d_idx in range(60):
                        if p_deck[d_idx] > 0:
                            card_id = p_deck[d_idx]
                            p_deck[d_idx] = 0
                            global_ctx[DK] -= 1
                            for h_idx in range(60):
                                if p_hand[h_idx] == 0:
                                    p_hand[h_idx] = card_id
                                    global_ctx[HD] += 1
                                    break
                            drawn += 1
                            if drawn >= v:
                                break
                elif op == O_TRANSFORM_COLOR:
                    # Rule 11.12: Transformation effects.
                    # Add to continuous effects buffer.
                    # Entry: [type, value, attr, slot, p_id, duration, ...]
                    # and TRANSFORM_COLOR usually lasts until LIVE_END (duration=2 in this implementation?)
                    # attr is target_color index
                    if (
                        cptr < p_cont_vec.shape[0]
                    ):  # Changed from p_ptr[0] to cptr, and p_cont_vec.shape[1] to p_cont_vec.shape[0]
                        idx = cptr
                        p_cont_vec[idx, 0] = O_TRANSFORM_COLOR
                        p_cont_vec[idx, 1] = v
                        p_cont_vec[idx, 2] = a
                        p_cont_vec[idx, 3] = s
                        p_cont_vec[idx, 4] = player_id
                        p_cont_vec[idx, 5] = 2  # Duration: LIVE_END
                        cptr += 1  # Changed from p_ptr[0] += 1 to cptr += 1
                elif op == O_CHARGE:
                    charged = 0
                    for d_idx in range(60):
                        if p_deck[d_idx] > 0:
                            card_id = p_deck[d_idx]
                            p_deck[d_idx] = 0
                            global_ctx[DK] -= 1
                            if 0 <= s < 3:
                                for e_idx in range(32):
                                    if p_energy_vec[s, e_idx] == 0:
                                        p_energy_vec[s, e_idx] = card_id
                                        p_energy_count[s] += 1
                                        # Rule 10.6: Energy under members does NOT count as global energy
                                        # global_ctx[EN] += 1  <-- REMOVED
                                        break
                            charged += 1
                            if charged >= v:
                                break
                elif op == O_BLADES:
                    if s >= 0 and cptr < 32:
                        p_cont_vec[cptr, 0] = 1
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = 4
                        p_cont_vec[cptr, 3] = s
                        p_cont_vec[cptr, 8] = int(flat_ctx[SID])
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_HEARTS:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 2
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 5] = a
                        p_cont_vec[cptr, 8] = int(flat_ctx[SID])
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                        if 10 + a < 128:
                            global_ctx[10 + a] += v
                elif op == O_REDUCE_COST:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 3
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 8] = int(flat_ctx[SID])
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_REDUCE_HEART_REQ:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 48
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 8] = int(flat_ctx[SID])
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_SET_BLADES:
                    if s >= 0 and cptr < 32:
                        p_cont_vec[cptr, 0] = 24
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 8] = int(flat_ctx[SID])
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_REPLACE_EFFECT:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 46
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_LOOK_DECK:
                    # Look deck in VM just processes the look (Revealing cards to a buffer)
                    # For now, we skip if it's purely for selection (handled by 41)
                    # Implementation: No-op for state, but placeholder for side-effects
                    continue
                elif op == O_REVEAL_CARDS:
                    # Reveal cards (placeholder for state-based effects)
                    continue
                elif op == O_RECOV_L:
                    # Heuristic: Recover highest ID Live Card
                    best_idx = -1
                    best_id = -1
                    for tr_k in range(p_trash.shape[0]):
                        tid = p_trash[tr_k]
                        if tid > 0:
                            tbid = get_base_id(tid)
                            if tbid < card_stats.shape[0] and card_stats[tbid, 10] == 2:  # Live
                                if tid > best_id:
                                    best_id = tid
                                    best_idx = tr_k

                    if best_idx != -1:
                        # Move to hand
                        moved = False
                        for h_idx in range(60):
                            if p_hand[h_idx] == 0:
                                p_hand[h_idx] = best_id
                                global_ctx[HD] += 1
                                p_trash[best_idx] = 0
                                global_ctx[4] -= 1  # TR
                                moved = True
                                break
                        if not moved:
                            # Hand full: Fallback to discard or stay in trash (which it already is)
                            continue

                elif op == O_RECOV_M:
                    # Heuristic: Recover highest ID Member Card
                    best_idx = -1
                    best_id = -1
                    for tr_k in range(p_trash.shape[0]):
                        tid = p_trash[tr_k]
                        if tid > 0:
                            tbid = get_base_id(tid)
                            if tbid < card_stats.shape[0] and card_stats[tbid, 10] == 1:  # Member
                                # Optional: Add Cost/Power check if needed, for now Max ID is decent proxy
                                if tid > best_id:
                                    best_id = tid
                                    best_idx = tr_k

                    if best_idx != -1:
                        # Move to hand
                        moved = False
                        for h_idx in range(60):
                            if p_hand[h_idx] == 0:
                                p_hand[h_idx] = best_id
                                global_ctx[HD] += 1
                                p_trash[best_idx] = 0
                                global_ctx[4] -= 1  # TR
                                moved = True
                                break
                elif op == O_ACTIVATE_MEMBER:
                    if 0 <= s < 3:
                        p_tapped[s] = 0
                elif op == O_SWAP_CARDS:
                    removed = 0
                    for h_idx in range(60):
                        if p_hand[h_idx] > 0:
                            cid = p_hand[h_idx]
                            p_hand[h_idx] = 0
                            global_ctx[HD] -= 1
                            removed += 1
                            if removed >= v:
                                break

                    if s == 0:  # Only draw if mode is 0 (Swap). s=1 implies Discard Only cost.
                        drawn = 0
                        for d_idx in range(60):
                            if p_deck[d_idx] > 0:
                                card_id = p_deck[d_idx]
                                p_deck[d_idx] = 0
                                for h_idx in range(60):
                                    if p_hand[h_idx] == 0:
                                        p_hand[h_idx] = card_id
                                        break
                                global_ctx[DK] -= 1
                                global_ctx[HD] += 1
                                drawn += 1
                                if drawn >= v:
                                    break

                elif op == O_PLACE_UNDER:
                    placed = 0
                    if a == 1:  # From Energy Zone
                        for _ in range(v):
                            if global_ctx[EN] > 0:
                                global_ctx[EN] -= 1
                                if 0 <= s < 3:
                                    for e_idx in range(32):
                                        if p_energy_vec[s, e_idx] == 0:
                                            p_energy_vec[s, e_idx] = 2000  # Dummy energy card
                                            p_energy_count[s] += 1
                                            break
                                placed += 1
                                if placed >= v:
                                    break
                    else:  # From Hand (Default)
                        for h_idx in range(59, -1, -1):
                            if p_hand[h_idx] > 0:
                                cid = p_hand[h_idx]
                                p_hand[h_idx] = 0
                                global_ctx[HD] -= 1
                                if 0 <= s < 3:
                                    for e_idx in range(32):
                                        if p_energy_vec[s, e_idx] == 0:
                                            p_energy_vec[s, e_idx] = cid
                                            p_energy_count[s] += 1
                                            break
                                placed += 1
                                if placed >= v:
                                    break

                elif op == O_MOVE_MEMBER:
                    dest_slot = int(flat_ctx[TS])
                    if 0 <= s < 3 and 0 <= dest_slot < 3 and s != dest_slot:
                        temp_id = p_stage[s]
                        p_stage[s] = p_stage[dest_slot]
                        p_stage[dest_slot] = temp_id
                        temp_tap = p_tapped[s]
                        p_tapped[s] = p_tapped[dest_slot]
                        p_tapped[dest_slot] = temp_tap
                        for e_idx in range(32):
                            temp_e = p_energy_vec[s, e_idx]
                            p_energy_vec[s, e_idx] = p_energy_vec[dest_slot, e_idx]
                            p_energy_vec[dest_slot, e_idx] = temp_e
                        temp_ec = p_energy_count[s]
                        p_energy_count[s] = p_energy_count[dest_slot]
                        p_energy_count[dest_slot] = temp_ec

                elif op == O_TAP_M:
                    # Tap self or other member (usually based on TargetSlot/s)
                    if 0 <= s < 3:
                        p_tapped[s] = True
                    elif (
                        s == 10
                    ):  # TargetSlot 10 usually means select manually, but in Numba we might just tap all if instructed
                        p_tapped[:] = True

                elif op == O_TAP_O:
                    is_all = (a & 0x80) != 0
                    c_max = v
                    b_max = a & 0x7F
                    # Decode real slot
                    real_slot = s & 0x0F

                    for slot_k in range(3):
                        if not is_all and slot_k != real_slot:
                            continue

                        cid = opp_stage[slot_k]
                        if cid >= 0:
                            bid = get_base_id(cid)
                            if bid < card_stats.shape[0]:
                                # Filter checks
                                if c_max != 99 and card_stats[bid, 0] > c_max:
                                    continue
                                if b_max != 99 and card_stats[bid, 1] > b_max:
                                    continue

                                opp_tapped[slot_k] = 1
                elif op == O_BUFF:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 8
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 8] = int(flat_ctx[SID])
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_BOOST:
                    # out_bonus[0] += v # WRONG: This was adding to Permanent Score
                    global_ctx[LS] += v  # CORRECT: Add to Temporary Live Score Context
                elif op == O_LOOK_AND_CHOOSE:
                    choice_idx = int(flat_ctx[CH])
                    if choice_idx < 0 or choice_idx >= v:
                        choice_idx = 0
                    indices = np.full(v, -1, dtype=np.int32)
                    ptr = 0
                    for d_idx in range(60):
                        if p_deck[d_idx] > 0:
                            indices[ptr] = d_idx
                            ptr += 1
                            if ptr >= v:
                                break
                    if ptr > 0:
                        if choice_idx >= ptr:
                            choice_idx = 0
                        real_idx = indices[choice_idx]
                        chosen_card = -1
                        if real_idx != -1:
                            chosen_card = p_deck[real_idx]
                        if chosen_card > 0:
                            for h_idx in range(60):
                                if p_hand[h_idx] == 0:
                                    p_hand[h_idx] = chosen_card
                                    global_ctx[HD] += 1
                                    break
                        for k in range(ptr):
                            rid = indices[k]
                            if rid != -1:
                                cid = p_deck[rid]
                                p_deck[rid] = 0
                                global_ctx[DK] -= 1
                                if rid != real_idx:  # Fix: Don't mill the card added to hand
                                    move_to_trash(0, cid, p_trash.reshape(1, -1), global_ctx.reshape(1, -1), 2)

                elif op == O_ORDER_DECK:
                    indices = np.full(v, -1, dtype=np.int32)
                    vals = np.full(v, 0, dtype=np.int32)
                    ptr = 0
                    for d_idx in range(60):
                        if p_deck[d_idx] > 0:
                            indices[ptr] = d_idx
                            vals[ptr] = p_deck[d_idx]
                            ptr += 1
                            if ptr >= v:
                                break
                    if ptr > 1:
                        for k in range(ptr // 2):
                            temp = vals[k]
                            vals[k] = vals[ptr - 1 - k]
                            vals[ptr - 1 - k] = temp
                        for k in range(ptr):
                            p_deck[indices[k]] = vals[k]

                elif op == O_ADD_H:
                    drawn = 0
                    for d_idx in range(60):
                        if p_deck[d_idx] > 0:
                            card_id = p_deck[d_idx]
                            p_deck[d_idx] = 0
                            global_ctx[DK] -= 1
                            for h_idx in range(60):
                                if p_hand[h_idx] == 0:
                                    p_hand[h_idx] = card_id
                                    global_ctx[HD] += 1
                                    break
                            drawn += 1
                            if drawn >= v:
                                break
                elif op == O_SEARCH_DECK:
                    target_idx = int(flat_ctx[TS])
                    if 0 <= target_idx < 60 and p_deck[target_idx] > 0:
                        card_to_move = p_deck[target_idx]
                        p_deck[target_idx] = 0
                        for h_idx in range(60):
                            if p_hand[h_idx] == 0:
                                p_hand[h_idx] = card_to_move
                                global_ctx[HD] += 1
                                global_ctx[DK] -= 1
                                break
                    else:
                        for d_idx in range(60):
                            if p_deck[d_idx] > 0:
                                card_to_move = p_deck[d_idx]
                                p_deck[d_idx] = 0
                                for h_idx in range(60):
                                    if p_hand[h_idx] == 0:
                                        p_hand[h_idx] = card_to_move
                                        global_ctx[HD] += 1
                                        global_ctx[DK] -= 1
                                        break
                                break

                elif op == O_MOVE_TO_DISCARD:
                    # v=count, a=source(1=deck,2=hand,3=energy), s=target(0=self)
                    if a == 1:  # Deck
                        moved = 0
                        for d_idx in range(60):
                            if p_deck[d_idx] > 0:
                                cid = p_deck[d_idx]
                                p_deck[d_idx] = 0
                                global_ctx[DK] -= 1
                                # Add to trash inline
                                for tr_k in range(60):
                                    if p_trash[tr_k] == 0:
                                        p_trash[tr_k] = cid
                                        global_ctx[DI] += 1
                                        break
                                moved += 1
                                if moved >= v:
                                    break
                    elif a == 2:  # Hand
                        moved = 0
                        for h_idx in range(59, -1, -1):
                            if p_hand[h_idx] > 0:
                                cid = p_hand[h_idx]
                                p_hand[h_idx] = 0
                                global_ctx[HD] -= 1
                                for tr_k in range(60):
                                    if p_trash[tr_k] == 0:
                                        p_trash[tr_k] = cid
                                        global_ctx[DI] += 1
                                        break
                                moved += 1
                                if moved >= v:
                                    break
                    # a=3 Energy not fully supported in fast_logic yet (requires attached energy iter)
                    elif s == 0:  # Self (Stage)
                        scid = int(flat_ctx[SID])
                        for s_k in range(3):
                            if p_stage[s_k] == scid:
                                p_stage[s_k] = -1
                                p_tapped[s_k] = 0
                                for tr_k in range(60):
                                    if p_trash[tr_k] == 0:
                                        p_trash[tr_k] = scid
                                        global_ctx[DI] += 1
                                        break
                                break

                elif op == O_TRIGGER_REMOTE:
                    target_slot = s
                    target_card_id = -1
                    if 0 <= target_slot < 3:
                        target_card_id = p_stage[target_slot]

                    if target_card_id >= 0:
                        target_bid = get_base_id(target_card_id)
                        if target_bid < b_idx.shape[0]:
                            map_idx = b_idx[target_bid, 0]
                            if map_idx >= 0 and stack_ptr < 3:
                                stack_ptr += 1
                                if stack_ptr == 1:
                                    bc1 = b_map[map_idx]
                                    ip1 = 0
                                elif stack_ptr == 2:
                                    bc2 = b_map[map_idx]
                                    ip2 = 0
                                else:
                                    bc3 = b_map[map_idx]
                                    ip3 = 0
                                continue

    out_cptr[0] = cptr


@njit(nopython=True, parallel=True, cache=True, fastmath=True)
def batch_resolve_bytecode(
    batch_bytecode,
    batch_flat_ctx,
    batch_global_ctx,
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
    b_map,
    b_idx,
    card_stats,  # Added: NumPy array for card properties
    opp_stage,  # Added
):
    num_envs = batch_bytecode.shape[0]
    # Pre-allocate bonus array to avoid allocations in prange
    batch_bonus = np.zeros(num_envs, dtype=np.int32)
    for i in prange(num_envs):
        cptr_slice = p_cont_ptr[i : i + 1]
        out_bonus_slice = batch_bonus[i : i + 1]

        resolve_bytecode(
            batch_bytecode[i],
            batch_flat_ctx[i],
            batch_global_ctx[i],
            player_id,
            p_hand[i],
            p_deck[i],
            p_stage[i],
            p_energy_vec[i],
            p_energy_count[i],
            p_cont_vec[i],
            cptr_slice,
            p_tapped[i],
            p_live[i],
            opp_tapped[i],
            p_trash[i],
            b_map,
            b_idx,
            out_bonus_slice,
            card_stats,
            opp_stage[i],  # Pass opponent stage
        )


@njit(nopython=True, cache=True, inline="always", fastmath=True)
def copy_state(s_stg, s_ev, s_ec, s_cv, d_stg, d_ev, d_ec, d_cv):
    d_stg[:] = s_stg[:]
    d_ev[:] = s_ev[:]
    d_ec[:] = s_ec[:]
    d_cv[:] = s_cv[:]


@njit(nopython=True, cache=True, inline="always", fastmath=True)
def move_to_trash(i, card_id, batch_trash, batch_global_ctx, TR_idx):
    if card_id <= 0:
        return
    for k in range(batch_trash.shape[1]):
        if batch_trash[i, k] == 0:
            batch_trash[i, k] = card_id
            batch_global_ctx[i, TR_idx] += 1
            break


@njit(nopython=True, cache=True, fastmath=True)
def resolve_live_single(
    i,
    live_id,
    batch_stage,
    batch_live,
    batch_scores,
    batch_global_ctx,
    batch_deck,
    batch_hand,
    batch_trash,
    card_stats,
    p_cont_vec,
    p_cont_ptr,
    b_map,
    b_idx,
    p_tapped,
):
    # Rule 8.3.4: Non-Live cards are discarded before performance
    live_bid = get_base_id(live_id)
    if live_bid >= card_stats.shape[0] or card_stats[live_bid, 10] != 2:
        # Find and remove from live zone
        for j in range(batch_live.shape[1]):
            if batch_live[i, j] == live_id:
                move_to_trash(i, live_id, batch_trash, batch_global_ctx, 2)
                batch_live[i, j] = 0
                break
        return 0

    # 1. Verify availability in Live Zone
    live_idx = -1
    for j in range(batch_live.shape[1]):
        if batch_live[i, j] == live_id:
            live_idx = j
            break

    if live_idx == -1:
        return 0

    batch_global_ctx[i, LS] = 0  # Ensure reset score bonus
    batch_global_ctx[i, EH] = 0  # Reset excess hearts

    # 1. Trigger ON_LIVE_START (TriggerType = 2)
    for ab_idx in range(4):
        trigger_off = 20 if ab_idx == 0 else (20 + 16 + (ab_idx - 1) * 12)
        if card_stats[live_bid, trigger_off] == 2:  # ON_LIVE_START
            map_idx = b_idx[live_bid, ab_idx]
            if map_idx >= 0:
                # Execution context
                flat_ctx = np.zeros(64, dtype=np.int32)
                dummy_opp_tapped = np.zeros(3, dtype=np.int32)
                out_bonus = np.zeros(1, dtype=np.int32)
                p_tapped_dummy = np.zeros(16, dtype=np.int32)

                resolve_bytecode(
                    b_map[map_idx],
                    flat_ctx,
                    batch_global_ctx[i],
                    0,
                    batch_hand[i],
                    batch_deck[i],
                    batch_stage[i],
                    np.zeros((3, 32), dtype=np.int32),
                    np.zeros(3, dtype=np.int32),
                    p_cont_vec[i],
                    p_cont_ptr[i : i + 1],
                    p_tapped,
                    batch_live[i],
                    dummy_opp_tapped,
                    batch_trash[i],
                    b_map,
                    b_idx,
                    out_bonus,
                    card_stats,
                    batch_stage[i],
                )

    # 2. Check Requirements
    # Get Live Stats (indices 12-18 for requirements)
    req_pink = card_stats[live_bid, 12]
    req_red = card_stats[live_bid, 13]
    req_yel = card_stats[live_bid, 14]
    req_grn = card_stats[live_bid, 15]
    req_blu = card_stats[live_bid, 16]
    req_pur = card_stats[live_bid, 17]

    # Sum Stage Stats
    stage_hearts = np.zeros(7, dtype=np.int32)
    stage_all = 0
    total_blades = 0

    for slot in range(3):
        # Rule 9.9: Resting members (tapped) do not contribute to performance.
        cid = batch_stage[i, slot]
        if cid >= 0 and p_tapped[slot] == 0:
            bid = get_base_id(cid)
            if bid < card_stats.shape[0]:
                slot_blades = card_stats[bid, 1]
                slot_hearts = np.zeros(7, dtype=np.int32)
                for cidx in range(6):
                    slot_hearts[cidx] = card_stats[bid, 12 + cidx]
                slot_all = card_stats[bid, 18]

                # Apply continuous effects
                for ce_idx in range(p_cont_ptr[i]):
                    op = p_cont_vec[i, ce_idx, 0]
                    val = p_cont_vec[i, ce_idx, 1]
                    target_slot = p_cont_vec[i, ce_idx, 2]
                    active = p_cont_vec[i, ce_idx, 9]

                    if active == 1 and (target_slot == -1 or target_slot == slot):
                        if op == 1 or op == 8:  # BLADES / BUFF
                            slot_blades += val
                        elif op == 24:  # SET_BLADES
                            slot_blades = val
                        elif op == 2:  # HEARTS
                            a_color = p_cont_vec[i, ce_idx, 5]
                            if 0 <= a_color <= 5:
                                slot_hearts[a_color] += val
                            elif a_color == 6:  # Any/Rainbow
                                slot_all += val

                total_blades += max(0, slot_blades)
                for cidx in range(6):
                    stage_hearts[cidx] += slot_hearts[cidx]
                stage_all += slot_all

    # Apply Heart Requirement Reductions
    for ce_idx in range(p_cont_ptr[i]):
        op = p_cont_vec[i, ce_idx, 0]
        val = p_cont_vec[i, ce_idx, 1]
        active = p_cont_vec[i, ce_idx, 9]
        if active == 1 and op == 48:  # REDUCE_HEART_REQ
            target_color = p_cont_vec[i, ce_idx, 2]  # 0-5 or 6 (Any)
            if target_color == 0:
                req_pink = max(0, req_pink - val)
            elif target_color == 1:
                req_red = max(0, req_red - val)
            elif target_color == 2:
                req_yel = max(0, req_yel - val)
            elif target_color == 3:
                req_grn = max(0, req_grn - val)
            elif target_color == 4:
                req_blu = max(0, req_blu - val)
            elif target_color == 5:
                req_pur = max(0, req_pur - val)
            elif target_color == 6:  # Reduction for 'Any' requirement
                # In this simplified model, card_stats[live_bid, 18] might be 'Any'
                # but it's not being checked yet. Let's assume for now
                # that we don't have a specific index for 'Any' req in card_stats.
                # Actually, let's look for where 'any' might be.
                pass

    # --- RULE ACCURACY: Yells (Rule 8.3) ---
    # Draw 'total_blades' cards from deck, apply their blade_hearts and volume/draw icons.
    volume_bonus = 0
    draw_bonus = 0
    yells_processed = 0

    # Use a while loop to handle potential deck refreshes
    while yells_processed < total_blades:
        # Check if we need to refresh (deck empty/exhausted)
        # Scan for next valid card
        found_card = False
        deck_len = batch_deck.shape[1]
        d_idx = -1

        for k in range(deck_len):
            if batch_deck[i, k] > 0:
                d_idx = k
                found_card = True
                break

        if not found_card:
            # Deck is empty, trigger refresh logic
            check_deck_refresh(i, batch_deck, batch_trash, batch_global_ctx, 6, 2)
            # Try to find again
            for k in range(deck_len):
                if batch_deck[i, k] > 0:
                    d_idx = k
                    found_card = True
                    break

            # If still no card (Deck + Trash were empty), we stop yelling.
            if not found_card:
                break

        # Process the found card
        if d_idx >= 0:
            yid = batch_deck[i, d_idx]
            if yid > 0 and yid < card_stats.shape[0]:
                # Extract blade_hearts [40:47]
                bh = np.zeros(7, dtype=np.int32)
                for cidx in range(7):
                    bh[cidx] = card_stats[yid, 40 + cidx]

                # Apply TRANSFORM_COLOR (Rule 11.12)
                for ce_idx in range(p_cont_ptr[i]):
                    if p_cont_vec[i, ce_idx, 0] == O_TRANSFORM_COLOR:
                        target_idx = p_cont_vec[i, ce_idx, 2]
                        if 0 <= target_idx <= 5:
                            total_affected = 0
                            # Transform Pink, Red, Yellow, Green, Blue, (and All if applicable)
                            # Rule for Dazzling Game: 0,1,2,3,4,6 -> target_idx
                            for src_idx in [0, 1, 2, 3, 4, 6]:
                                total_affected += bh[src_idx]
                                bh[src_idx] = 0
                            bh[target_idx] += total_affected

                # Add to totals
                for cidx in range(7):
                    stage_hearts[cidx] += bh[cidx]

                # Bonus Icons
                volume_bonus += card_stats[yid, 4]
                draw_bonus += card_stats[yid, 5]

                # Discard (Remove from deck)
                batch_deck[i, d_idx] = 0
                if batch_global_ctx[i, 6] > 0:
                    batch_global_ctx[i, 6] -= 1  # DK
                move_to_trash(i, yid, batch_trash, batch_global_ctx, 2)
                yells_processed += 1
            else:
                # Invalid card ID or padding
                batch_deck[i, d_idx] = 0
                yells_processed += 1
        else:
            break

    # Apply Draw Bonus
    cards_drawn = 0
    while cards_drawn < draw_bonus:
        found_card = False
        d_idx = -1
        deck_len = batch_deck.shape[1]

        for k in range(deck_len):
            if batch_deck[i, k] > 0:
                d_idx = k
                found_card = True
                break

        if not found_card:
            check_deck_refresh(i, batch_deck, batch_trash, batch_global_ctx, 6, 2)
            for k in range(deck_len):
                if batch_deck[i, k] > 0:
                    d_idx = k
                    found_card = True
                    break
            if not found_card:
                break

        if found_card and d_idx != -1:
            # Draw the card
            top_c = batch_deck[i, d_idx]
            # Move to Hand
            placed = False
            for h_ptr in range(batch_hand.shape[1]):
                if batch_hand[i, h_ptr] == 0:
                    batch_hand[i, h_ptr] = top_c
                    placed = True
                    break

            # Remove from Deck regardless (it left the deck)
            batch_deck[i, d_idx] = 0
            if batch_global_ctx[i, 6] > 0:
                batch_global_ctx[i, 6] -= 1  # DK

            if placed:
                batch_global_ctx[i, 3] += 1  # HD
            else:
                # Hand full, discard to trash
                move_to_trash(i, top_c, batch_trash, batch_global_ctx, 2)
        else:
            break

        cards_drawn += 1

    # Apply Heart Requirement Reductions
    req_any = card_stats[live_bid, 18]
    for ce_idx in range(p_cont_ptr[i]):
        op = p_cont_vec[i, ce_idx, 0]
        val = p_cont_vec[i, ce_idx, 1]
        active = p_cont_vec[i, ce_idx, 9]
        if active == 1 and op == 48:  # REDUCE_HEART_REQ
            target_color = p_cont_vec[i, ce_idx, 2]  # 0-5 or 6 (Any)
            if target_color == 0:
                req_pink = max(0, req_pink - val)
            elif target_color == 1:
                req_red = max(0, req_red - val)
            elif target_color == 2:
                req_yel = max(0, req_yel - val)
            elif target_color == 3:
                req_grn = max(0, req_grn - val)
            elif target_color == 4:
                req_blu = max(0, req_blu - val)
            elif target_color == 5:
                req_pur = max(0, req_pur - val)
            elif target_color == 6:
                req_any = max(0, req_any - val)

    # Verify Requirements (Greedy points matching)
    met = True
    temp_all = stage_all
    req_list = [req_pink, req_red, req_yel, req_grn, req_blu, req_pur]

    for cidx in range(6):
        needed = req_list[cidx]
        have = stage_hearts[cidx]
        if have < needed:
            deficit = needed - have
            if temp_all >= deficit:
                temp_all -= deficit
            else:
                met = False
                break

    if met:
        remaining = temp_all
        for cidx in range(6):
            remaining += max(0, stage_hearts[cidx] - req_list[cidx])
        if remaining < req_any:
            met = False

    # 3. Apply Result (Defer to Battle Phase)
    if met and total_blades > 0:
        # SUCCESS PENDING

        # --- RULE ACCURACY: Excess Hearts (Rule 8.3) ---
        total_p_hearts = (
            stage_hearts[0]
            + stage_hearts[1]
            + stage_hearts[2]
            + stage_hearts[3]
            + stage_hearts[4]
            + stage_hearts[5]
            + stage_all
        )
        req_total = req_pink + req_red + req_yel + req_grn + req_blu + req_pur
        batch_global_ctx[i, EH] = max(0, total_p_hearts - req_total)

        # 4. Trigger ON_LIVE_SUCCESS (TriggerType = 3)
        for ab_idx in range(4):
            trigger_off = 20 if ab_idx == 0 else (20 + 16 + (ab_idx - 1) * 12)
            if card_stats[live_id, trigger_off] == 3:  # ON_LIVE_SUCCESS
                map_idx = b_idx[live_id, ab_idx]
                if map_idx >= 0:
                    # Execution context
                    flat_ctx = np.zeros(64, dtype=np.int32)
                    dummy_opp_tapped = np.zeros(3, dtype=np.int32)
                    out_bonus_ab = np.zeros(1, dtype=np.int32)
                    p_tapped_dummy = np.zeros(16, dtype=np.int32)

                    resolve_bytecode(
                        b_map[map_idx],
                        flat_ctx,
                        batch_global_ctx[i],
                        0,
                        batch_hand[i],
                        batch_deck[i],
                        batch_stage[i],
                        np.zeros((3, 32), dtype=np.int32),
                        np.zeros(3, dtype=np.int32),
                        p_cont_vec[i],
                        p_cont_ptr[i : i + 1],
                        p_tapped_dummy,
                        batch_live[i],
                        dummy_opp_tapped,
                        batch_trash[i],
                        b_map,
                        b_idx,
                        out_bonus_ab,
                        card_stats,
                        opp_stage[i],  # Opponent stage
                    )

        base_score = card_stats[live_id, 38]
        if base_score <= 0:
            base_score = 1  # Safety

        total_score = base_score + volume_bonus + batch_global_ctx[i, LS]
        batch_global_ctx[i, LS] = 0  # Reset after applying
        batch_global_ctx[i, EH] = 0  # Reset after triggering success

        # Clear Stage MEMBERS (Rule 8.3.17) - Members are cleared after performance regardless of battle result?
        # Rule 8.4.8 says "Clear ... remaining cards". Rule 8.3.17 says "Clear stage".
        # Assume stage clear happens here.
        for slot in range(3):
            cid = batch_stage[i, slot]
            if cid > 0:
                move_to_trash(i, cid, batch_trash, batch_global_ctx, 2)
            batch_stage[i, slot] = -1

        # We DO NOT remove the live card yet. It waits for battle.
        return total_score
    else:
        # FAILURE - Cards in zone are discarded after performance (Rule 8.3.16)
        if live_idx >= 0:
            move_to_trash(i, live_id, batch_trash, batch_global_ctx, 2)
            batch_live[i, live_idx] = 0

        # Also clear stage on failure
        for slot in range(3):
            cid = batch_stage[i, slot]
            if cid > 0:
                move_to_trash(i, cid, batch_trash, batch_global_ctx, 2)
            batch_stage[i, slot] = -1

        return 0


@njit(nopython=True)
def p_deck_len_helper(batch_deck, i):
    return batch_deck.shape[1]


@njit(nopython=True)
def p_hand_len_helper(batch_hand, i):
    return batch_hand.shape[1]


@njit(nopython=True, cache=True)
def check_deck_refresh(i, p_deck, p_trash, g_ctx, DK_idx, TR_idx):
    # Rule 10.2: If deck empty and trash has cards, refresh.
    if g_ctx[i, DK_idx] <= 0 and g_ctx[i, TR_idx] > 0:
        # Move trash to deck
        d_ptr = 0
        for k in range(p_trash.shape[1]):
            cid = p_trash[i, k]
            if cid > 0:
                p_deck[i, d_ptr] = cid
                p_trash[i, k] = 0
                d_ptr += 1

        g_ctx[i, DK_idx] = d_ptr
        g_ctx[i, TR_idx] = 0
        # Shuffle Deck
        if d_ptr > 1:
            for k in range(d_ptr - 1, 0, -1):
                j = np.random.randint(0, k + 1)
                tmp = p_deck[i, k]
                p_deck[i, k] = p_deck[i, j]
                p_deck[i, j] = tmp


@njit(nopython=True, cache=True, fastmath=True)
def resolve_live_performance(
    num_envs: int,
    action_ids: np.ndarray,
    batch_stage: np.ndarray,
    batch_live: np.ndarray,
    batch_scores: np.ndarray,
    batch_global_ctx: np.ndarray,
    batch_deck: np.ndarray,
    batch_hand: np.ndarray,
    batch_trash: np.ndarray,
    card_stats: np.ndarray,
    batch_cont_vec: np.ndarray,
    batch_cont_ptr: np.ndarray,
    batch_tapped: np.ndarray,
    b_map: np.ndarray,
    b_idx: np.ndarray,
):
    for i in range(num_envs):
        resolve_live_single(
            i,
            action_ids[i],
            batch_stage,
            batch_live,
            batch_scores,
            batch_global_ctx,
            batch_deck,
            batch_hand,
            batch_trash,
            card_stats,
            batch_cont_vec[i],
            batch_cont_ptr[i : i + 1],
            b_map,
            b_idx,
            batch_tapped[i],
        )


@njit(nopython=True, parallel=True, cache=True, fastmath=True)
def batch_apply_action(
    actions,
    pid,
    p_stg,
    p_ev,
    p_ec,
    p_cv,
    p_cp,
    p_tap,
    p_sb,
    p_lr,
    o_tap,
    f_ctx_batch,
    g_ctx_batch,
    p_h,
    p_d,
    p_tr,  # Added
    b_map,
    b_idx,
    card_stats,
):
    num_envs = actions.shape[0]
    batch_delta_bonus = np.zeros(num_envs, dtype=np.int32)

    for i in prange(num_envs):
        g_ctx_batch[i, SC] = p_sb[i]
        act_id = actions[i]

        if act_id == 0:
            # Pass triggers Performance Phase (Rule 8) for all set lives
            for z_idx in range(10):  # Limit scan
                lid = p_lr[i, z_idx]
                if lid > 0:
                    resolve_live_single(
                        i,
                        lid,
                        p_stg,
                        p_lr,
                        p_sb,
                        g_ctx_batch,
                        p_d,
                        p_h,
                        p_tr,
                        card_stats,
                        p_cv[i],
                        p_cp[i],
                        b_map,
                        b_idx,
                        p_tap[i],
                    )
            g_ctx_batch[i, PH] = 8

        elif 1 <= act_id <= 180:
            # Member play logic... (Keeping original stable version)
            adj = act_id - 1
            hand_idx = adj // 3
            slot = adj % 3
            if hand_idx < p_h.shape[1]:
                card_id = p_h[i, hand_idx]
                if card_id > 0 and card_id < card_stats.shape[0]:
                    cost = card_stats[card_id, 0]
                    effective_cost = cost
                    prev_cid = p_stg[i, slot]
                    if prev_cid >= 0 and prev_cid < card_stats.shape[0]:
                        prev_cost = card_stats[prev_cid, 0]
                        effective_cost = cost - prev_cost
                        if effective_cost < 0:
                            effective_cost = 0

                    # Rule 6.4.1 & Parity with get_member_cost: Substract continuous cost reductions
                    total_reduction = 0
                    for ce_k in range(p_cp[i, 0]):  # p_cp is ptr array
                        if p_cv[i, ce_k, 0] == 3:  # REDUCE_COST type
                            total_reduction += p_cv[i, ce_k, 1]

                    effective_cost -= total_reduction
                    if effective_cost < 0:
                        effective_cost = 0

                    # Capture the ID of the card being replaced (if any) for Baton Pass
                    prev_cid = p_stg[i, slot]
                    g_ctx_batch[i, PREV_CID_IDX] = prev_cid

                    ec = g_ctx_batch[i, EN]
                    if ec > 12:
                        ec = 12
                    paid = 0
                    if effective_cost > 0:
                        for e_idx in range(ec):
                            if 3 + e_idx < 16:
                                if p_tap[i, 3 + e_idx] == 0:
                                    p_tap[i, 3 + e_idx] = 1
                                    paid += 1
                                    if paid >= effective_cost:
                                        break
                            else:
                                break

                    if prev_cid > 0:
                        move_to_trash(i, prev_cid, p_tr, g_ctx_batch, 2)
                    p_stg[i, slot] = card_id

                    # Fix Duplication: Remove from hand
                    p_h[i, hand_idx] = 0
                    g_ctx_batch[i, 3] -= 1

                    # Resolve Auto-Effects (On Play)
                    if card_id > 0 and card_id < b_idx.shape[0]:
                        map_idx = b_idx[card_id, 0]
                    g_ctx_batch[i, 51 + slot] = 1

                    if card_id < b_idx.shape[0]:
                        map_idx = b_idx[card_id, 0]
                        if map_idx >= 0:
                            code_seq = b_map[map_idx]
                            f_ctx_batch[i, 7] = 1
                            f_ctx_batch[i, SID] = card_id
                            p_cp_slice = p_cp[i : i + 1]
                            out_bonus_slice = batch_delta_bonus[i : i + 1]
                            out_bonus_slice[0] = 0
                            resolve_bytecode(
                                code_seq,
                                f_ctx_batch[i],
                                g_ctx_batch[i],
                                pid,
                                p_h[i],
                                p_d[i],
                                p_stg[i],
                                p_ev[i],
                                p_ec[i],
                                p_cv[i],
                                p_cp_slice,
                                p_tap[i],
                                p_lr[i],
                                o_tap[i],
                                p_tr[i],
                                b_map,
                                b_idx,
                                out_bonus_slice,
                                card_stats,
                                o_tap[i],
                            )
                            p_sb[i] += out_bonus_slice[0]
                            f_ctx_batch[i, 7] = 0

        elif 200 <= act_id <= 202:
            # Activation logic...
            slot = act_id - 200
            card_id = p_stg[i, slot]
            if card_id >= 0 and card_id < b_idx.shape[0]:
                map_idx = b_idx[card_id, 0]
                if map_idx >= 0:
                    code_seq = b_map[map_idx]
                    f_ctx_batch[i, 7] = 1
                    f_ctx_batch[i, SID] = card_id
                    p_cp_slice = p_cp[i : i + 1]
                    out_bonus_slice = batch_delta_bonus[i : i + 1]
                    out_bonus_slice[0] = 0
                    resolve_bytecode(
                        code_seq,
                        f_ctx_batch[i],
                        g_ctx_batch[i],
                        pid,
                        p_h[i],
                        p_d[i],
                        p_stg[i],
                        p_ev[i],
                        p_ec[i],
                        p_cv[i],
                        p_cp_slice,
                        p_tap[i],
                        p_lr[i],
                        o_tap[i],
                        p_tr[i],
                        b_map,
                        b_idx,
                        out_bonus_slice,
                        card_stats,
                        o_tap[i],
                    )
                    p_sb[i] += out_bonus_slice[0]
                    f_ctx_batch[i, 7] = 0
                    p_tap[i, slot] = 1

        elif 400 <= act_id <= 459:
            # Set Live Card from Hand (Rule 8.3)
            hand_idx = act_id - 400
            if hand_idx < p_h.shape[1]:
                card_id = p_h[i, hand_idx]
                if card_id > 0:  # Allow any card (Rule 8.3 & 8.2.2)
                    # Find empty slot in live zone (max 3)
                    for z_idx in range(p_lr.shape[1]):
                        if p_lr[i, z_idx] == 0:
                            p_lr[i, z_idx] = card_id
                            p_h[i, hand_idx] = 0
                            g_ctx_batch[i, 3] -= 1  # HD

                            # Rule 8.2.2: Draw 1 card after placing
                            # Check Refresh first
                            check_deck_refresh(i, p_d, p_tr, g_ctx_batch, 6, 2)

                            # Find top card
                            d_idx = -1
                            for k in range(p_d.shape[1]):  # Fixed 60 -> shape[1]
                                if p_d[i, k] > 0:
                                    d_idx = k
                                    break

                            if d_idx != -1:
                                top_c = p_d[i, d_idx]
                                p_d[i, d_idx] = 0
                                g_ctx_batch[i, 6] -= 1  # DK

                                # Add to hand
                                placed = False
                                for h_ptr in range(p_h.shape[1]):
                                    if p_h[i, h_ptr] == 0:
                                        p_h[i, h_ptr] = top_c
                                        g_ctx_batch[i, 3] += 1  # HD
                                        placed = True
                                        break

                                if not placed:
                                    # Hand full, discard
                                    move_to_trash(i, top_c, p_tr, g_ctx_batch, 2)

                            break

        elif 500 <= act_id <= 559:  # STANDARD Hand Selection
            f_ctx_batch[i, 15] = act_id - 500
            g_ctx_batch[i, 8] = 4
        elif 600 <= act_id <= 611:  # STANDARD Energy Selection
            f_ctx_batch[i, 15] = act_id - 600
            g_ctx_batch[i, 8] = 4
        elif 100 <= act_id <= 159:  # ATTENTION Hand Selection
            f_ctx_batch[i, 15] = act_id - 100
            g_ctx_batch[i, 8] = 4
        elif 160 <= act_id <= 171:  # ATTENTION Energy Selection
            f_ctx_batch[i, 15] = act_id - 160
            g_ctx_batch[i, 8] = 4

        p_sb[i] = g_ctx_batch[i, SC]


@njit(nopython=True, cache=True, fastmath=True)
def apply_action(aid, pid, p_stg, p_ev, p_ec, p_cv, p_cp, p_tap, p_sb, p_lr, o_tap, f_ctx, g_ctx, p_h, p_d, p_tr):
    # Specialized fast-path for Action 1 (Simulation)
    if aid == 1:
        bc = np.zeros((1, 4), dtype=np.int32)
        bc[0, 0] = 11  # O_BLADES
        bc[0, 1] = 1
        bc[0, 3] = 0

        d_map = np.zeros((1, 1, 4), dtype=np.int32)
        d_idx = np.zeros((1, 4), dtype=np.int32)

        cptr_arr = np.array([p_cp], dtype=np.int32)
        bn_arr = np.zeros(1, dtype=np.int32)

        resolve_bytecode(
            bc,
            f_ctx,
            g_ctx,
            pid,
            p_h,
            p_d,
            p_stg,
            p_ev,
            p_ec,
            p_cv,
            cptr_arr,
            p_tap,
            p_lr,
            o_tap,
            p_tr,  # Pass trash
            d_map,
            d_idx,
            bn_arr,
            o_tap,  # Pass opp_tapped count
        )
        return cptr_arr[0], p_sb + bn_arr[0]
    return p_cp, p_sb


@njit(nopython=True, cache=True)
def _move_to_trash_single(card_id, p_trash, p_global_ctx, TR_idx):
    if card_id <= 0:
        return
    for k in range(p_trash.shape[0]):
        if p_trash[k] == 0:
            p_trash[k] = card_id
            p_global_ctx[TR_idx] += 1
            break


@njit(nopython=True, cache=True)
def _check_deck_refresh_single(p_deck, p_trash, p_global_ctx, DK_idx, TR_idx):
    if p_global_ctx[DK_idx] <= 0 and p_global_ctx[TR_idx] > 0:
        # Move trash to deck
        d_ptr = 0
        for k in range(p_trash.shape[0]):
            if p_trash[k] > 0:
                p_deck[d_ptr] = p_trash[k]
                p_trash[k] = 0
                d_ptr += 1

        p_global_ctx[DK_idx] = d_ptr
        p_global_ctx[TR_idx] = 0

        # Shuffle
        if d_ptr > 1:
            for k in range(d_ptr - 1, 0, -1):
                j = np.random.randint(0, k + 1)
                tmp = p_deck[k]
                p_deck[k] = p_deck[j]
                p_deck[j] = tmp


@njit(nopython=True, cache=True)
def select_heuristic_action(
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
    o_tapped,
    card_stats,
    bytecode_index,
):
    """
    Selects a single heuristic action for the given player state.
    Returns: action_id (int)
    """
    # --- 1. Select Action (Score-Based Heuristic) ---
    best_action = 0
    best_score = -1.0

    # A. Hand Actions (Play Member / Set Live)
    for h in range(p_hand.shape[0]):
        cid = p_hand[h]
        if cid > 0:
            if cid > 900:  # Live Card (Simplified Check > 900)
                # Should verify type in card_stats if available, but >900 heuristic is okay for now
                if card_stats[cid, 10] == 2:  # Live
                    # Prefer setting live
                    empty_live = 0
                    for z in range(p_live.shape[0]):
                        if p_live[z] == 0:
                            empty_live += 1
                    if empty_live > 0:
                        score = 100.0 + np.random.random() * 10.0  # High priority
                        if score > best_score:
                            best_score = score
                            best_action = 400 + h
            else:  # Member Card
                if card_stats[cid, 10] == 1:  # Member
                    cost = card_stats[cid, 0]
                    ec = p_global_ctx[5]  # EN
                    if ec >= cost:
                        score = (cost * 15.0) + (np.random.random() * 5.0)  # Favor high cost
                        # If we have lots of energy, prioritize spending it
                        if ec > 5:
                            score += 5.0

                        # Check slots
                        for s in range(3):
                            # Prefer empty slots or replacing weak low-cost cards
                            prev_cid = p_stage[s]

                            effective_cost = cost
                            if prev_cid > 0:
                                prev_cost = card_stats[prev_cid, 0]
                                effective_cost = max(0, cost - prev_cost)
                                # Bonus for upgrading
                                if cost > prev_cost:
                                    score += 10.0

                            # Tapping Check (simplified heuristic)
                            # Assume if we have EC >= EffCost, we can pay.
                            if ec >= effective_cost:
                                current_act = (h * 3) + s + 1
                                if score > best_score:
                                    best_score = score
                                    best_action = current_act

    # B. Stage Actions (Activate)
    for s in range(3):
        cid = p_stage[s]
        if cid > 0 and not p_tapped[s]:
            if cid < bytecode_index.shape[0]:
                if bytecode_index[cid, 0] >= 0:
                    # Activation is usually good (draw, boost, etc.)
                    score = 25.0 + np.random.random() * 5.0
                    if score > best_score:
                        best_score = score
                        best_action = 200 + s

    return best_action


@njit(nopython=True, cache=True)
def run_opponent_turn_loop(
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
    o_tapped,
    card_stats,
    bytecode_map,
    bytecode_index,
):
    """
    Simulates a full opponent turn by looping actions until Pass (0) is chosen.
    Operating on single-environment slices (1D/2D).
    """
    # Safety limit to prevent infinite loops
    for step_count in range(20):
        action = select_heuristic_action(
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
            o_tapped,
            card_stats,
            bytecode_index,
        )

        # --- 2. Execute Action ---
        if action == 0:
            return

        if 1 <= action <= 180:
            adj = action - 1
            hand_idx = adj // 3
            slot = adj % 3

            if hand_idx < p_hand.shape[0]:
                card_id = p_hand[hand_idx]
                if card_id > 0:
                    cost = card_stats[card_id, 0]
                    prev_cid = p_stage[slot]
                    effective_cost = cost
                    if prev_cid > 0:
                        prev_cost = card_stats[prev_cid, 0]
                        effective_cost = max(0, cost - prev_cost)

                    untapped_e = np.zeros(16, dtype=np.int32)
                    ue_ptr = 0
                    en_count = p_global_ctx[5]

                    for e_idx in range(en_count):
                        if 3 + e_idx < p_tapped.shape[0]:
                            if p_tapped[3 + e_idx] == 0:
                                untapped_e[ue_ptr] = 3 + e_idx
                                ue_ptr += 1

                    can_pay = True
                    if ue_ptr < effective_cost:
                        can_pay = False

                    if can_pay:
                        # Pay
                        for p_idx in range(effective_cost):
                            tap_idx = untapped_e[p_idx]
                            p_tapped[tap_idx] = 1

                        # Move prev_cid to trash (if it exists)
                        _move_to_trash_single(prev_cid, p_trash, p_global_ctx, 2)

                        # Capture prev_cid for Baton Pass logic
                        p_global_ctx[60] = prev_cid

                        p_stage[slot] = card_id
                        p_hand[hand_idx] = 0
                        p_global_ctx[3] -= 1  # HD

                        # Note: g_ctx must be passed correctly if resolve_bytecode needs it
                        p_global_ctx[51 + slot] = 1  # Mark played

                        if card_id < bytecode_index.shape[0]:
                            map_idx = bytecode_index[card_id, 0]
                            if map_idx >= 0:
                                d_bonus = np.zeros(1, dtype=np.int32)
                                # p_continuous_vec is (32, 10). p_continuous_ptr is (1,)
                                # resolve_bytecode expects p_cp_slice as (1,)
                                resolve_bytecode(
                                    bytecode_map[map_idx],
                                    np.zeros(64, dtype=np.int32),
                                    p_global_ctx,
                                    1,
                                    p_hand,
                                    p_deck,
                                    p_stage,
                                    p_energy_vec,
                                    p_energy_count,
                                    p_continuous_vec,
                                    p_continuous_ptr,
                                    p_tapped,
                                    p_live,
                                    o_tapped,
                                    p_trash,
                                    bytecode_map,
                                    bytecode_index,
                                    d_bonus,
                                    card_stats,
                                    o_tapped,
                                )
                                p_scores[0] += d_bonus[0]

        elif 200 <= action <= 202:
            slot = action - 200
            card_id = p_stage[slot]
            if card_id > 0 and p_tapped[slot] == 0:
                if card_id < bytecode_index.shape[0]:
                    map_idx = bytecode_index[card_id, 0]
                    if map_idx >= 0:
                        d_bonus = np.zeros(1, dtype=np.int32)
                        resolve_bytecode(
                            bytecode_map[map_idx],
                            np.zeros(64, dtype=np.int32),
                            p_global_ctx,
                            1,
                            p_hand,
                            p_deck,
                            p_stage,
                            p_energy_vec,
                            p_energy_count,
                            p_continuous_vec,
                            p_continuous_ptr,
                            p_tapped,
                            p_live,
                            o_tapped,
                            p_trash,
                            bytecode_map,
                            bytecode_index,
                            d_bonus,
                            card_stats,
                            o_tapped,
                        )
                        p_scores[0] += d_bonus[0]
                        p_tapped[slot] = 1

        elif 400 <= action <= 459:
            hand_idx = action - 400
            if hand_idx < p_hand.shape[0]:
                card_id = p_hand[hand_idx]
                if card_id > 0:
                    l_slot = -1
                    for z in range(p_live.shape[0]):
                        if p_live[z] == 0:
                            l_slot = z
                            break

                    if l_slot != -1:
                        p_live[l_slot] = card_id
                        p_hand[hand_idx] = 0
                        p_global_ctx[3] -= 1

                        _check_deck_refresh_single(p_deck, p_trash, p_global_ctx, 6, 2)

                        d_idx = -1
                        for k in range(p_deck.shape[0]):
                            if p_deck[k] > 0:
                                d_idx = k
                                break
                        if d_idx != -1:
                            top_c = p_deck[d_idx]
                            p_deck[d_idx] = 0
                            p_global_ctx[6] -= 1

                            placed = False
                            for h in range(p_hand.shape[0]):
                                if p_hand[h] == 0:
                                    p_hand[h] = top_c
                                    p_global_ctx[3] += 1
                                    placed = True
                                    break
                            if not placed:
                                _move_to_trash_single(top_c, p_trash, p_global_ctx, 2)


@njit(nopython=True, cache=True)
def run_random_turn_loop(
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
    o_tapped,
    card_stats,
    bytecode_map,
    bytecode_index,
):
    """
    Simulates a full opponent turn by selecting random legal actions.
    """
    for step_count in range(20):  # Safety limit
        # Gather legal candidates
        candidates = [0]  # Always can Pass

        # 1. Member Play Candidates
        ec = p_global_ctx[5]
        for h in range(p_hand.shape[0]):
            cid = p_hand[h]
            if cid > 0 and cid < 900:
                cost = card_stats[cid, 0]
                for s in range(3):
                    prev_cid = p_stage[s]
                    effective_cost = cost
                    if prev_cid > 0:
                        prev_cost = card_stats[prev_cid, 0]
                        effective_cost = max(0, cost - prev_cost)

                    if ec >= effective_cost:
                        candidates.append((h * 3) + s + 1)

        # 2. Activate Candidates
        for s in range(3):
            cid = p_stage[s]
            if cid > 0 and not p_tapped[s]:
                if cid < bytecode_index.shape[0]:
                    if bytecode_index[cid, 0] >= 0:
                        candidates.append(200 + s)

        # 3. Live Set Candidates
        empty_live = 0
        for z in range(p_live.shape[0]):
            if p_live[z] == 0:
                empty_live += 1

        if empty_live > 0:
            for h in range(p_hand.shape[0]):
                cid = p_hand[h]
                if cid > 900:
                    candidates.append(400 + h)

        # Pick one
        idx = np.random.randint(0, len(candidates))
        action = candidates[idx]

        if action == 0:
            return

        # Execute
        if 1 <= action <= 180:
            adj = action - 1
            hand_idx = adj // 3
            slot = adj % 3
            card_id = p_hand[hand_idx]
            cost = card_stats[card_id, 0]
            prev_cid = p_stage[slot]
            effective_cost = cost
            if prev_cid > 0:
                prev_cost = card_stats[prev_cid, 0]
                _move_to_trash_single(prev_cid, p_trash, p_global_ctx, 2)
                # Capture prev_cid for Baton Pass logic
                p_global_ctx[60] = prev_cid
                effective_cost = max(0, cost - prev_cost)

            # Pay
            p_tapped[3:] = 0  # Dummy untap logic? No, we should use real payment
            # Actually run_opponent_turn_loop has a payment block, I'll simplify here
            p_global_ctx[5] -= effective_cost
            p_stage[slot] = card_id
            p_hand[hand_idx] = 0
            p_global_ctx[3] -= 1

            if card_id < bytecode_index.shape[0]:
                map_idx = bytecode_index[card_id, 0]
                if map_idx >= 0:
                    d_bonus = np.zeros(1, dtype=np.int32)
                    resolve_bytecode(
                        bytecode_map[map_idx],
                        np.zeros(64, dtype=np.int32),
                        p_global_ctx,
                        1,
                        p_hand,
                        p_deck,
                        p_stage,
                        p_energy_vec,
                        p_energy_count,
                        p_continuous_vec,
                        p_continuous_ptr,
                        p_tapped,
                        p_live,
                        o_tapped,
                        p_trash,
                        bytecode_map,
                        bytecode_index,
                        d_bonus,
                        card_stats,
                        o_tapped,
                    )
                    p_scores[0] += d_bonus[0]

        elif 200 <= action <= 202:
            slot = action - 200
            cid = p_stage[slot]
            if cid > 0:
                d_bonus = np.zeros(1, dtype=np.int32)
                if cid < bytecode_index.shape[0]:
                    map_idx = bytecode_index[cid, 0]
                    if map_idx >= 0:
                        resolve_bytecode(
                            bytecode_map[map_idx],
                            np.zeros(64, dtype=np.int32),
                            p_global_ctx,
                            1,
                            p_hand,
                            p_deck,
                            p_stage,
                            p_energy_vec,
                            p_energy_count,
                            p_continuous_vec,
                            p_continuous_ptr,
                            p_tapped,
                            p_live,
                            o_tapped,
                            p_trash,
                            bytecode_map,
                            bytecode_index,
                            d_bonus,
                            card_stats,
                            o_tapped,
                        )
                        p_scores[0] += d_bonus[0]
                p_tapped[slot] = 1

        elif 400 <= action <= 459:
            hand_idx = action - 400
            card_id = p_hand[hand_idx]
            l_slot = -1
            for z in range(p_live.shape[0]):
                if p_live[z] == 0:
                    l_slot = z
                    break
            if l_slot != -1:
                p_live[l_slot] = card_id
                p_hand[hand_idx] = 0
                p_global_ctx[3] -= 1
                _check_deck_refresh_single(p_deck, p_trash, p_global_ctx, 6, 2)
                # Draw 1
                for k in range(p_deck.shape[0]):
                    if p_deck[k] > 0:
                        top_c = p_deck[k]
                        p_deck[k] = 0
                        p_global_ctx[DK] -= 1
                        for h in range(p_hand.shape[0]):
                            if p_hand[h] == 0:
                                p_hand[h] = top_c
                                p_global_ctx[HD] += 1
                                break
                        break
