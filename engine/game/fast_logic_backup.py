import numpy as np
from numba import njit, prange

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
PH = 8

# Opcodes
O_DRAW = 10
O_BLADES = 11
O_HEARTS = 12
O_REDUCE_COST = 13
O_RECOV_L = 15
O_BOOST = 16
O_RECOV_M = 17
O_BUFF = 18
O_MOVE_MEMBER = 20
O_SWAP_CARDS = 21
O_SEARCH_DECK = 22
O_CHARGE = 23
O_ORDER_DECK = 28
O_SELECT_MODE = 30
O_TAP_O = 32
O_PLACE_UNDER = 33
O_LOOK_AND_CHOOSE = 41
O_ACTIVATE_MEMBER = 43
O_ADD_H = 44
O_REPLACE_EFFECT = 46
O_TRIGGER_REMOTE = 47
O_REDUCE_HEART_REQ = 48
O_RETURN = 1
O_JUMP = 2
O_JUMP_F = 3

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


@njit(nopython=True, cache=True)
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
    b_map,
    b_idx,
    out_bonus,  # Modified: Pass by ref array (size 1)
):
    ip = 0
    # Load cptr from reference
    cptr = out_cptr[0]
    # Bonus is accumulated into out_bonus[0]

    cond = True
    blen = bytecode.shape[0]

    # SAFETY: Infinite loop protection
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

        # Dynamic Target Handling (MEMBER_SELECT)
        if s == 10:
            s = int(flat_ctx[TS])

        if op == O_JUMP:
            new_ip = ip + v
            if 0 <= new_ip < blen:
                ip = new_ip
            else:
                ip = blen
            continue

        if op == O_JUMP_F:
            if not cond:
                new_ip = ip + v
                if 0 <= new_ip < blen:
                    ip = new_ip
                else:
                    ip = blen
                continue
            ip += 1
            continue

        if op == O_SELECT_MODE:
            choice = int(flat_ctx[CH])
            if 0 <= choice < v:
                jump_ip = ip + 1 + choice
                if jump_ip < blen:
                    offset = bytecode[jump_ip, 1]
                    new_ip = jump_ip + offset
                    if 0 <= new_ip < blen:
                        ip = new_ip
                        continue
            ip += v + 1
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
                if 0 <= a <= 4:
                    cond = global_ctx[30 + a] >= v
                else:
                    cond = False
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
            else:
                cond = True
            ip += 1
        else:
            if cond:
                if op == O_DRAW:
                    if global_ctx[DK] >= v:
                        global_ctx[DK] -= v
                        global_ctx[HD] += v
                    else:
                        t = global_ctx[DK]
                        global_ctx[DK] = 0
                        global_ctx[HD] += t
                elif op == O_CHARGE:
                    if global_ctx[DK] >= v:
                        global_ctx[DK] -= v
                        global_ctx[EN] += v
                    else:
                        t = global_ctx[DK]
                        global_ctx[DK] = 0
                        global_ctx[EN] += t
                elif op == O_BLADES:
                    if s >= 0 and cptr < 32:
                        p_cont_vec[cptr, 0] = 1
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = 4
                        p_cont_vec[cptr, 3] = s
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_HEARTS:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 2
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 5] = a
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                        global_ctx[0] += v
                elif op == O_REDUCE_COST:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 3
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_REDUCE_HEART_REQ:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 48
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_REPLACE_EFFECT:
                    if cptr < 32:
                        p_cont_vec[cptr, 0] = 46
                        p_cont_vec[cptr, 1] = v
                        p_cont_vec[cptr, 2] = s
                        p_cont_vec[cptr, 9] = 1
                        cptr += 1
                elif op == O_RECOV_L:
                    pass
                elif op == O_RECOV_M:
                    pass
                elif op == O_ACTIVATE_MEMBER:
                    if 0 <= s < 3:
                        p_tapped[s] = 0
                elif op == O_SWAP_CARDS:
                    removed = 0
                    for h_idx in range(60):
                        if p_hand[h_idx] > 0:
                            p_hand[h_idx] = 0
                            global_ctx[HD] -= 1
                            removed += 1
                            if removed >= v:
                                break

                    # Actually Move Cards for Draw
                    drawn = 0
                    for d_idx in range(60):
                        if p_deck[d_idx] > 0:
                            card_id = p_deck[d_idx]
                            p_deck[d_idx] = 0

                            # Find empty hand slot
                            for h_idx in range(60):
                                if p_hand[h_idx] == 0:
                                    p_hand[h_idx] = card_id
                                    break

                            global_ctx[DK] -= 1
                            global_ctx[HD] += 1
                            drawn += 1
                            if drawn >= v:
                                break

                    # If not enough cards, we stop (counters already updated per card)

                elif op == O_PLACE_UNDER:
                    placed = 0
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
                    out_bonus[0] += v
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
                                p_deck[rid] = 0
                                global_ctx[DK] -= 1

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
                    if global_ctx[DK] >= v:
                        global_ctx[DK] -= v
                        global_ctx[HD] += v
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

                elif op == O_TRIGGER_REMOTE:
                    target_slot = s
                    if target_slot < 0:
                        pass

                    target_card_id = -1
                    if 0 <= target_slot < 3:
                        target_card_id = p_stage[target_slot]

                    if target_card_id > 0 and target_card_id < b_idx.shape[0]:
                        map_idx = b_idx[target_card_id, 0]
                        if map_idx >= 0:
                            sub_code = b_map[map_idx]
                            out_cptr[0] = cptr
                            resolve_bytecode(
                                sub_code,
                                flat_ctx,
                                global_ctx,
                                player_id,
                                p_hand,
                                p_deck,
                                p_stage,
                                p_energy_vec,
                                p_energy_count,
                                p_cont_vec,
                                out_cptr,
                                p_tapped,
                                p_live,
                                opp_tapped,
                                b_map,
                                b_idx,
                                out_bonus,
                            )
                            cptr = out_cptr[0]

            ip += 1

    out_cptr[0] = cptr


@njit(nopython=True)
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
    b_map,
    b_idx,
):
    num_envs = batch_bytecode.shape[0]
    for i in prange(num_envs):
        cptr_slice = p_cont_ptr[i : i + 1]
        dummy_bonus = np.zeros(1, dtype=np.int32)

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
            b_map,
            b_idx,
            dummy_bonus,
        )


@njit(nopython=True, cache=True)
def copy_state(s_stg, s_ev, s_ec, s_cv, d_stg, d_ev, d_ec, d_cv):
    d_stg[:] = s_stg[:]
    d_ev[:] = s_ev[:]
    d_ec[:] = s_ec[:]
    d_cv[:] = s_cv[:]


@njit(nopython=True)
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
    b_map,
    b_idx,
):
    # Sync individual scores and turn to global_ctx before stepping
    for i in prange(actions.shape[0]):
        g_ctx_batch[i, SC] = p_sb[i]
        act_id = actions[i]

        if act_id > 0:
            card_id = act_id
            if card_id < b_idx.shape[0]:
                map_idx = b_idx[card_id, 0]
                if map_idx >= 0:
                    code_seq = b_map[map_idx]
                    f_ctx_batch[i, 7] = 1

                    cptr_slice = p_cp[i : i + 1]
                    delta_bonus = np.zeros(1, dtype=np.int32)

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
                        cptr_slice,
                        p_tap[i],
                        p_lr[i],
                        o_tap[i],
                        b_map,
                        b_idx,
                        delta_bonus,
                    )

                    p_sb[i] += delta_bonus[0]
                    f_ctx_batch[i, 7] = 0

                found_h = False
                for h_idx in range(60):
                    if p_h[i, h_idx] == card_id:
                        p_h[i, h_idx] = 0
                        g_ctx_batch[i, 3] -= 1
                        found_h = True
                        break

                if found_h and card_id < 900:
                    for s_idx in range(3):
                        if p_stg[i, s_idx] == -1:
                            p_stg[i, s_idx] = card_id
                            break

                cnt = 0
                for h_idx in range(60):
                    if p_h[i, h_idx] > 0:
                        cnt += 1

                if cnt < 5:
                    top_card = 0
                    deck_idx = -1
                    for d_idx in range(60):
                        if p_d[i, d_idx] > 0:
                            top_card = p_d[i, d_idx]
                            deck_idx = d_idx
                            break

                    if top_card > 0:
                        for h_idx in range(60):
                            if p_h[i, h_idx] == 0:
                                p_h[i, h_idx] = top_card
                                p_d[i, deck_idx] = 0
                                g_ctx_batch[i, 3] += 1
                                g_ctx_batch[i, 6] -= 1
                                break
            else:
                pass


@njit(nopython=True, cache=True)
def apply_action(aid, pid, p_stg, p_ev, p_ec, p_cv, p_cp, p_tap, p_sb, p_lr, o_tap, f_ctx, g_ctx, p_h, p_d):
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
            bc, f_ctx, g_ctx, pid, p_h, p_d, p_stg, p_ev, p_ec, p_cv, cptr_arr, p_tap, p_lr, o_tap, d_map, d_idx, bn_arr
        )
        return cptr_arr[0], p_sb + bn_arr[0]
    return p_cp, p_sb
