from engine.game.fast_logic import (
    C_CLR,
    C_CMP,
    C_CTR,
    C_ENR,
    C_GRP,
    C_HND,
    C_LLD,
    C_OPH,
    C_STG,
    C_TR1,
    DK,
    EN,
    HD,
    O_ADD_H,
    O_BLADES,
    O_BOOST,
    O_BUFF,
    O_CHARGE,
    O_CHOOSE,
    O_DRAW,
    O_HEARTS,
    O_JUMP,
    O_JUMP_F,
    O_RECOV_L,
    O_RECOV_M,
    O_RETURN,
    O_TAP_O,
    OS,
    OT,
    SC,
    TR,
)

try:
    from numba import cuda
    from numba.cuda.random import xoroshiro128p_uniform_float32

    HAS_CUDA = True
except ImportError:
    HAS_CUDA = False

    class MockCuda:
        def jit(self, *args, **kwargs):
            return lambda x: x

        def grid(self, x):
            return 0

    cuda = MockCuda()

    def xoroshiro128p_uniform_float32(rng, idx):
        return 0.5


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
):
    """
    GPU Device function for resolving bytecode.
    Equivalent to engine/game/fast_logic.py:resolve_bytecode but optimized for CUDA.
    """
    ip = 0
    cptr = p_cont_ptr
    bonus = 0
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

        # Jumps with safety checks
        if op == O_JUMP:
            new_ip = ip + v
            if 0 <= new_ip < blen:
                ip = new_ip
            else:
                ip = blen  # Exit
            continue

        if op == O_JUMP_F:
            if not cond:
                new_ip = ip + v
                if 0 <= new_ip < blen:
                    ip = new_ip
                else:
                    ip = blen  # Exit
                continue
            ip += 1
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
                cond = flat_ctx[7] == 1  # SZ=7 (Hand=1)
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
                if op == O_DRAW or op == O_CHOOSE or op == O_ADD_H:
                    # Draw v cards logic (O_CHOOSE is Look v add 1, simplified to Draw 1)
                    # O_ADD_H is add v from deck
                    draw_amt = v
                    if op == O_CHOOSE:
                        draw_amt = 1

                    if global_ctx[DK] >= draw_amt:
                        global_ctx[DK] -= draw_amt
                        global_ctx[HD] += draw_amt

                        # Perform actual card movement
                        for _ in range(draw_amt):
                            # 1. Find top card
                            top_card = 0
                            d_idx_found = -1
                            for d_idx in range(60):
                                if p_deck[d_idx] > 0:
                                    top_card = p_deck[d_idx]
                                    d_idx_found = d_idx
                                    break

                            if top_card > 0:
                                # 2. Find empty hand slot
                                for h_idx in range(60):
                                    if p_hand[h_idx] == 0:
                                        p_hand[h_idx] = top_card
                                        p_deck[d_idx_found] = 0
                                        break

                    else:
                        # Draw remaining deck? (Simplified: just draw what we can)
                        t = global_ctx[DK]
                        if t > 0:
                            # Draw t cards
                            for _ in range(t):
                                top_card = 0
                                d_idx_found = -1
                                for d_idx in range(60):
                                    if p_deck[d_idx] > 0:
                                        top_card = p_deck[d_idx]
                                        d_idx_found = d_idx
                                        break
                                if top_card > 0:
                                    for h_idx in range(60):
                                        if p_hand[h_idx] == 0:
                                            p_hand[h_idx] = top_card
                                            p_deck[d_idx_found] = 0
                                            break

                            global_ctx[DK] = 0
                            global_ctx[HD] += t

                elif op == O_CHARGE:
                    if global_ctx[DK] >= v:
                        global_ctx[DK] -= v
                        global_ctx[EN] += v
                        # Move v cards from Deck to "Energy" (which is virtual count or zone?)
                        # Logic usually says Charge = move to energy zone.
                        # In fast_logic, we have p_energy_vec (3 slots x 32).
                        # But Charge typically goes to specific member energy?
                        # Or global energy? The global context EN is just a count.
                        # For POC, we just consume from deck. Real logic needs target slot.

                        for _ in range(v):
                            # Remove from deck
                            for d_idx in range(60):
                                if p_deck[d_idx] > 0:
                                    p_deck[d_idx] = 0
                                    break
                    else:
                        t = global_ctx[DK]
                        global_ctx[DK] = 0
                        global_ctx[EN] += t
                        for _ in range(t):
                            for d_idx in range(60):
                                if p_deck[d_idx] > 0:
                                    p_deck[d_idx] = 0
                                    break

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
                        global_ctx[0] += v  # SC = 0. Immediate scoring for Vectorized RL.
                elif op == O_RECOV_L:
                    if 0 <= s < p_live.shape[0]:
                        p_live[s] = 0
                elif op == O_RECOV_M:
                    if 0 <= s < 3:
                        p_tapped[s] = 0
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


@cuda.jit
def step_kernel(
    rng_states,
    batch_stage,  # (N, 3)
    batch_energy_vec,  # (N, 3, 32)
    batch_energy_count,  # (N, 3)
    batch_continuous_vec,  # (N, 32, 10)
    batch_continuous_ptr,  # (N,)
    batch_tapped,  # (N, 3)
    batch_live,  # (N, 50)
    batch_opp_tapped,  # (N, 3)
    batch_scores,  # (N,)
    batch_flat_ctx,  # (N, 64)
    batch_global_ctx,  # (N, 128)
    batch_hand,  # (N, 60)
    batch_deck,  # (N, 60)
    bytecode_map,  # (MapSize, 64, 4)
    bytecode_index,  # (MaxCards, 4)
    actions,  # (N,)
):
    """
    Main CUDA Kernel for Stepping N Environments.
    """
    i = cuda.grid(1)

    if i >= batch_global_ctx.shape[0]:
        return

    # Sync Score
    batch_global_ctx[i, SC] = batch_scores[i]

    act_id = actions[i]

    # 1. Apply Action
    if act_id > 0:
        card_id = act_id

        # Check Bounds
        if card_id < bytecode_index.shape[0]:
            # Assume Ability 0
            map_idx = bytecode_index[card_id, 0]

            if map_idx >= 0:
                code_seq = bytecode_map[map_idx]

                # Set Source Zone to Hand (1) -> mapped to index 7 in flat_ctx?
                # In fast_logic.py: SZ = 7.
                batch_flat_ctx[i, 7] = 1

                # Execute
                nc, st, bn = resolve_bytecode_device(
                    code_seq,
                    batch_flat_ctx[i],
                    batch_global_ctx[i],
                    0,  # Player ID
                    batch_hand[i],
                    batch_deck[i],
                    batch_stage[i],
                    batch_energy_vec[i],
                    batch_energy_count[i],
                    batch_continuous_vec[i],
                    batch_continuous_ptr[i],  # Passed as scalar? No, ptr[i] is scalar, but device func expects ref?
                    # fast_logic expects 'p_cont_ptr' as int,
                    # returns new ptr.
                    # Wait, resolve_bytecode returns (cptr, ...).
                    # So we pass VALUE of ptr.
                    batch_tapped[i],
                    batch_live[i],
                    batch_opp_tapped[i],
                )

                # Update State
                batch_continuous_ptr[i] = nc
                batch_scores[i] = batch_global_ctx[i, SC] + bn  # SC updated inside + bonus?
                # Actually resolve_bytecode updates SC in global_ctx for O_HEARTS.
                # So we just take global_ctx[SC].

                # Reset SZ
                batch_flat_ctx[i, 7] = 0

            # Remove Card from Hand
            found = False
            for h_idx in range(60):
                if batch_hand[i, h_idx] == card_id:
                    batch_hand[i, h_idx] = 0
                    batch_global_ctx[i, 3] -= 1  # HD
                    found = True
                    break

            # Place on Stage (if Member)
            if found and card_id < 900:
                for s_idx in range(3):
                    if batch_stage[i, s_idx] == -1:
                        batch_stage[i, s_idx] = card_id
                        break

            # Draw Logic (Refill to 5)
            # Count Hand
            h_cnt = 0
            for h_idx in range(60):
                if batch_hand[i, h_idx] > 0:
                    h_cnt += 1

            if h_cnt < 5:
                # Draw top card
                top_card = 0
                d_idx_found = -1
                for d_idx in range(60):
                    if batch_deck[i, d_idx] > 0:
                        top_card = batch_deck[i, d_idx]
                        d_idx_found = d_idx
                        break

                if top_card > 0:
                    for h_idx in range(60):
                        if batch_hand[i, h_idx] == 0:
                            batch_hand[i, h_idx] = top_card
                            batch_deck[i, d_idx_found] = 0
                            batch_global_ctx[i, 3] += 1
                            batch_global_ctx[i, 6] -= 1
                            break

    # 2. Opponent (Random) Simulation
    # Use XOROSHIRO RNG
    if rng_states is not None:
        r = xoroshiro128p_uniform_float32(rng_states, i)
        if r > 0.8:
            # Randomly tap an agent member?
            pass
