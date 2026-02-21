fn rng_jump() -> u32 {
    g_rng.x ^= g_rng.y << 13u;
    g_rng.y ^= g_rng.x >> 7u;
    g_rng.x ^= g_rng.y << 17u;
    return g_rng.x + g_rng.y;
}

fn count_bits(v: u32) -> u32 {
    var x = v;
    x = x - ((x >> 1u) & 0x55555555u);
    x = (x & 0x33333333u) + ((x >> 2u) & 0x33333333u);
    return (((x + (x >> 4u)) & 0x0F0F0F0Fu) * 0x01010101u) >> 24u;
}

// Get card from hand (packed u16 pairs)
fn get_hand_card(p_idx: u32, h_idx: u32) -> u32 {
    let word_idx = h_idx / 2u;
    let shift = (h_idx % 2u) * 16u;
    var word = 0u;
    if (p_idx == 0u) {
        word = states[g_gid].player0.hand[word_idx];
    } else {
        word = states[g_gid].player1.hand[word_idx];
    }
    return (word >> shift) & 0xFFFFu;
}

// Get card from discard (packed u16 pairs)
fn get_discard_card(p_idx: u32, idx: u32) -> u32 {
    var d_len = 0u;
    if (p_idx == 0u) { d_len = states[g_gid].player0.discard_pile_len; }
    else { d_len = states[g_gid].player1.discard_pile_len; }
    
    if (idx >= d_len) { return 0u; }
    let word_idx = idx / 2u;
    let shift = (idx % 2u) * 16u;
    var word = 0u;
    if (p_idx == 0u) {
        word = states[g_gid].player0.discard_pile[word_idx];
    } else {
        word = states[g_gid].player1.discard_pile[word_idx];
    }
    return (word >> shift) & 0xFFFFu;
}

// Get card from stage (packed u16 pairs)
fn get_live_card(p_idx: u32, slot: u32) -> u32 {
    let word_idx = slot / 2u;
    let shift = (slot % 2u) * 16u;
    var word = 0u;
    if (p_idx == 0u) {
        word = states[g_gid].player0.live_zone[word_idx];
    } else {
        word = states[g_gid].player1.live_zone[word_idx];
    }
    return (word >> shift) & 0xFFFFu;
}

fn set_live_card(p_idx: u32, s_idx: u32, card_id: u32) {
    let word_idx = s_idx / 2u;
    let shift = (s_idx % 2u) * 16u;
    if (p_idx == 0u) {
        states[g_gid].player0.live_zone[word_idx] = (states[g_gid].player0.live_zone[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
    } else {
        states[g_gid].player1.live_zone[word_idx] = (states[g_gid].player1.live_zone[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
    }
}

fn remove_from_hand(p_idx: u32, hand_idx: u32) {
    var p_hand_len = 0u;
    if (p_idx == 0u) { p_hand_len = states[g_gid].player0.hand_len; }
    else { p_hand_len = states[g_gid].player1.hand_len; }

    if (p_hand_len == 0u || hand_idx >= p_hand_len) { return; }
    for (var i = hand_idx; i < 31u; i = i + 1u) {
        if (i >= p_hand_len - 1u) { break; }
        let next_card = get_hand_card(p_idx, i + 1u);
        let dst_shift = (i % 2u) * 16u;
        if (p_idx == 0u) {
            states[g_gid].player0.hand[i / 2u] = (states[g_gid].player0.hand[i / 2u] & ~(0xFFFFu << dst_shift)) | (next_card << dst_shift);
        } else {
            states[g_gid].player1.hand[i / 2u] = (states[g_gid].player1.hand[i / 2u] & ~(0xFFFFu << dst_shift)) | (next_card << dst_shift);
        }
    }
    let last_idx = p_hand_len - 1u;
    let l_shift = (last_idx % 2u) * 16u;
    if (p_idx == 0u) {
        states[g_gid].player0.hand[last_idx / 2u] &= ~(0xFFFFu << l_shift);
        states[g_gid].player0.hand_len -= 1u;
    } else {
        states[g_gid].player1.hand[last_idx / 2u] &= ~(0xFFFFu << l_shift);
        states[g_gid].player1.hand_len -= 1u;
    }
}

fn get_stage_card(p_idx: u32, s_idx: u32) -> u32 {
    let word_idx = s_idx / 2u;
    let shift = (s_idx % 2u) * 16u;
    var word = 0u;
    if (p_idx == 0u) {
        word = states[g_gid].player0.stage[word_idx];
    } else {
        word = states[g_gid].player1.stage[word_idx];
    }
    return (word >> shift) & 0xFFFFu;
}

fn set_stage_card(p_idx: u32, s_idx: u32, card_id: u32) {
    let word_idx = s_idx / 2u;
    let shift = (s_idx % 2u) * 16u;
    if (p_idx == 0u) {
        states[g_gid].player0.stage[word_idx] = (states[g_gid].player0.stage[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
    } else {
        states[g_gid].player1.stage[word_idx] = (states[g_gid].player1.stage[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
    }
}

fn set_moved(p_idx: u32, slot: u32) {
    if (p_idx == 0u) {
        states[g_gid].player0.moved_flags |= (1u << slot);
        states[g_gid].player0.flags |= (1u << (6u + slot));
    } else {
        states[g_gid].player1.moved_flags |= (1u << slot);
        states[g_gid].player1.flags |= (1u << (6u + slot));
    }
}

fn add_to_deck_bottom(p_idx: u32, card_id: u32) {
    if (card_id == 0u) { return; }
    var d_len = 0u;
    if (p_idx == 0u) { d_len = states[g_gid].player0.deck_len; }
    else { d_len = states[g_gid].player1.deck_len; }
    if (d_len >= 64u) { return; }

    for (var i = d_len; i > 0u; i = i - 1u) {
        let prev_card = get_deck_card(p_idx, i - 1u);
        let dst_idx = i;
        let t_shift = (dst_idx % 2u) * 16u;
        if (p_idx == 0u) {
            states[g_gid].player0.deck[dst_idx / 2u] = (states[g_gid].player0.deck[dst_idx / 2u] & ~(0xFFFFu << t_shift)) | (prev_card << t_shift);
        } else {
            states[g_gid].player1.deck[dst_idx / 2u] = (states[g_gid].player1.deck[dst_idx / 2u] & ~(0xFFFFu << t_shift)) | (prev_card << t_shift);
        }
    }
    if (p_idx == 0u) {
        states[g_gid].player0.deck[0] = (states[g_gid].player0.deck[0] & ~0xFFFFu) | card_id;
        states[g_gid].player0.deck_len += 1u;
    } else {
        states[g_gid].player1.deck[0] = (states[g_gid].player1.deck[0] & ~0xFFFFu) | card_id;
        states[g_gid].player1.deck_len += 1u;
    }
}

fn get_deck_card(p_idx: u32, d_idx: u32) -> u32 {
    let word_idx = d_idx / 2u;
    let shift = (d_idx % 2u) * 16u;
    var word = 0u;
    if (p_idx == 0u) {
        word = states[g_gid].player0.deck[word_idx];
    } else {
        word = states[g_gid].player1.deck[word_idx];
    }
    return (word >> shift) & 0xFFFFu;
}

fn set_deck_card(p_idx: u32, d_idx: u32, card_id: u32) {
    let word_idx = d_idx / 2u;
    let shift = (d_idx % 2u) * 16u;
    if (p_idx == 0u) {
        states[g_gid].player0.deck[word_idx] = (states[g_gid].player0.deck[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
    } else {
        states[g_gid].player1.deck[word_idx] = (states[g_gid].player1.deck[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
    }
}

fn is_moved(p_idx: u32, slot: u32) -> bool {
    var m_flags = 0u;
    if (p_idx == 0u) { m_flags = states[g_gid].player0.moved_flags; }
    else { m_flags = states[g_gid].player1.moved_flags; }
    return (m_flags & (1u << slot)) != 0u;
}

fn add_to_discard(p_idx: u32, card_id: u32) {
    if (card_id == 0u) { return; }
    var disc_len = 0u;
    if (p_idx == 0u) { disc_len = states[g_gid].player0.discard_pile_len; }
    else { disc_len = states[g_gid].player1.discard_pile_len; }

    if (disc_len < 32u) {
        if (p_idx == 0u) {
            states[g_gid].player0.discard_pile[disc_len / 2u] |= (card_id << ((disc_len % 2u) * 16u));
            states[g_gid].player0.discard_pile_len = disc_len + 1u;
        } else {
            states[g_gid].player1.discard_pile[disc_len / 2u] |= (card_id << ((disc_len % 2u) * 16u));
            states[g_gid].player1.discard_pile_len = disc_len + 1u;
        }
    }
}

fn remove_from_discard(p_idx: u32, idx: u32) {
    var d_len = 0u;
    if (p_idx == 0u) { d_len = states[g_gid].player0.discard_pile_len; }
    else { d_len = states[g_gid].player1.discard_pile_len; }
    if (idx >= d_len) { return; }
    
    for (var i = idx; i < 63u; i = i + 1u) {
        if (i >= d_len - 1u) { break; }
        let next_card = get_discard_card(p_idx, i + 1u);
        let t_shift = (i % 2u) * 16u;
        if (p_idx == 0u) {
            states[g_gid].player0.discard_pile[i / 2u] = (states[g_gid].player0.discard_pile[i / 2u] & ~(0xFFFFu << t_shift)) | (next_card << t_shift);
        } else {
            states[g_gid].player1.discard_pile[i / 2u] = (states[g_gid].player1.discard_pile[i / 2u] & ~(0xFFFFu << t_shift)) | (next_card << t_shift);
        }
    }
    let last_idx = d_len - 1u;
    if (p_idx == 0u) {
        states[g_gid].player0.discard_pile[last_idx / 2u] &= ~(0xFFFFu << ((last_idx % 2u) * 16u));
        states[g_gid].player0.discard_pile_len -= 1u;
    } else {
        states[g_gid].player1.discard_pile[last_idx / 2u] &= ~(0xFFFFu << ((last_idx % 2u) * 16u));
        states[g_gid].player1.discard_pile_len -= 1u;
    }
}

fn get_success_card(p_idx: u32, idx: u32) -> u32 {
    let word_idx = idx / 2u;
    let shift = (idx % 2u) * 16u;
    if (p_idx == 0u) { return (states[g_gid].player0.success_lives[word_idx] >> shift) & 0xFFFFu; }
    return (states[g_gid].player1.success_lives[word_idx] >> shift) & 0xFFFFu;
}

fn add_to_success_pile(p_idx: u32, card_id: u32) {
    if (card_id == 0u) { return; }
    var len = 0u;
    if (p_idx == 0u) { len = states[g_gid].player0.lives_cleared_count; }
    else { len = states[g_gid].player1.lives_cleared_count; }
    if (len >= 8u) { return; }
    
    let word_idx = len / 2u;
    let shift = (len % 2u) * 16u;
    if (p_idx == 0u) {
        states[g_gid].player0.success_lives[word_idx] |= (card_id << shift);
        states[g_gid].player0.lives_cleared_count += 1u;
    } else {
        states[g_gid].player1.success_lives[word_idx] |= (card_id << shift);
        states[g_gid].player1.lives_cleared_count += 1u;
    }
}

fn add_to_hand(p_idx: u32, card_id: u32) {
    var h_idx = 0u;
    if (p_idx == 0u) { h_idx = states[g_gid].player0.hand_len; }
    else { h_idx = states[g_gid].player1.hand_len; }

    if (h_idx >= 32u) { return; }
    let word_idx = h_idx / 2u;
    let shift = (h_idx % 2u) * 16u;
    if (p_idx == 0u) {
        states[g_gid].player0.hand[word_idx] = (states[g_gid].player0.hand[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
        states[g_gid].player0.hand_len += 1u;
    } else {
        states[g_gid].player1.hand[word_idx] = (states[g_gid].player1.hand[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
        states[g_gid].player1.hand_len += 1u;
    }
}

fn refresh_deck(p_idx: u32) {
    var d_len = 0u; var disc_len = 0u;
    if (p_idx == 0u) { 
        d_len = states[g_gid].player0.deck_len;
        disc_len = states[g_gid].player0.discard_pile_len;
    } else { 
        d_len = states[g_gid].player1.deck_len;
        disc_len = states[g_gid].player1.discard_pile_len;
    }
    if (disc_len == 0u) { return; }
    
    if (d_len > 0u) {
        for (var i = d_len; i > 0u; i = i - 1u) {
            let old_idx = i - 1u;
            let card_id = get_deck_card(p_idx, old_idx);
            set_deck_card(p_idx, old_idx + disc_len, card_id);
        }
    }
    
    for (var i = 0u; i < disc_len; i = i + 1u) {
        let card_id = get_discard_card(p_idx, i);
        set_deck_card(p_idx, i, card_id);
    }
    
    if (p_idx == 0u) {
        states[g_gid].player0.deck_len = d_len + disc_len;
        states[g_gid].player0.discard_pile_len = 0u;
        states[g_gid].player0.flags |= 2u; 
        for (var w = 0u; w < 32u; w = w + 1u) { states[g_gid].player0.discard_pile[w] = 0u; }
    } else {
        states[g_gid].player1.deck_len = d_len + disc_len;
        states[g_gid].player1.discard_pile_len = 0u;
        states[g_gid].player1.flags |= 2u; 
        for (var w = 0u; w < 32u; w = w + 1u) { states[g_gid].player1.discard_pile[w] = 0u; }
    }
}

fn draw_card(p_idx: u32) {
    var d_len = 0u;
    if (p_idx == 0u) { d_len = states[g_gid].player0.deck_len; }
    else { d_len = states[g_gid].player1.deck_len; }

    if (d_len == 0u) {
        refresh_deck(p_idx);
        if (p_idx == 0u) { d_len = states[g_gid].player0.deck_len; }
        else { d_len = states[g_gid].player1.deck_len; }
    }
    
    if (d_len == 0u) { return; }
    let card_id = get_deck_card(p_idx, d_len - 1u);
    
    add_to_hand(p_idx, card_id);

    if (p_idx == 0u) { states[g_gid].player0.deck_len -= 1u; }
    else { states[g_gid].player1.deck_len -= 1u; }
}

fn pop_deck(p_idx: u32) -> u32 {
    var d_len = 0u;
    if (p_idx == 0u) { d_len = states[g_gid].player0.deck_len; }
    else { d_len = states[g_gid].player1.deck_len; }

    if (d_len == 0u) {
        refresh_deck(p_idx);
        if (p_idx == 0u) { d_len = states[g_gid].player0.deck_len; }
        else { d_len = states[g_gid].player1.deck_len; }
    }
    
    if (d_len == 0u) { return 0u; }
    let cid = get_deck_card(p_idx, d_len - 1u);
    if (p_idx == 0u) { states[g_gid].player0.deck_len -= 1u; }
    else { states[g_gid].player1.deck_len -= 1u; }
    return cid;
}

fn draw_energy(p_idx: u32) {
    var e_d_len = 0u;
    if (p_idx == 0u) { e_d_len = states[g_gid].player0.energy_deck_len; }
    else { e_d_len = states[g_gid].player1.energy_deck_len; }

    if (e_d_len > 0u) {
        if (p_idx == 0u) {
            states[g_gid].player0.energy_deck_len -= 1u;
            states[g_gid].player0.energy_count += 1u;
        } else {
            states[g_gid].player1.energy_deck_len -= 1u;
            states[g_gid].player1.energy_count += 1u;
        }
    }
}

fn end_main_phase() {
    let p_idx = states[g_gid].current_player;
    let first_p = states[g_gid].first_player;
    if (p_idx == first_p) {
        let other_p = 1u - first_p;
        states[g_gid].current_player = other_p;
        draw_energy(other_p);
        draw_card(other_p);
        states[g_gid].phase = PHASE_MAIN;
    } else {
        states[g_gid].phase = PHASE_LIVESET;
        states[g_gid].current_player = first_p;
    }
}

fn get_board_heart(p_idx: u32, color: u32) -> u32 {
    if (color >= 8u) { return 0u; }
    if (p_idx == 0u) { return g_board_hearts[0][color]; }
    else { return g_board_hearts[1][color]; }
}

fn set_board_heart(p_idx: u32, color: u32, val: u32) {
    if (color >= 8u) { return; }
    if (p_idx == 0u) { g_board_hearts[0][color] = val; }
    else { g_board_hearts[1][color] = val; }
}

fn add_board_heart(p_idx: u32, color: u32, amount: u32) {
    if (color >= 8u) { return; }
    if (p_idx == 0u) { g_board_hearts[0][color] += amount; }
    else { g_board_hearts[1][color] += amount; }
}

fn recalculate_board_stats(p_idx: u32) {
    var total_hearts = array<u32, 8>(0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u);
    var total_blades = 0u;
    for (var s = 0u; s < 3u; s = s + 1u) {
        let cid = get_stage_card(p_idx, s);
        if (cid > 0u && cid < arrayLength(&card_stats)) {
            let stats = card_stats[cid];
            total_hearts[0] += (stats.hearts_lo >> 0u) & 0xFFu;
            total_hearts[1] += (stats.hearts_lo >> 8u) & 0xFFu;
            total_hearts[2] += (stats.hearts_lo >> 16u) & 0xFFu;
            total_hearts[3] += (stats.hearts_lo >> 24u) & 0xFFu;
            total_hearts[4] += (stats.hearts_hi >> 0u) & 0xFFu;
            total_hearts[5] += (stats.hearts_hi >> 8u) & 0xFFu;
            total_hearts[6] += (stats.hearts_hi >> 16u) & 0xFFu;
            total_blades += stats.blades;
        }
    }
    // Add buffs
    if (p_idx == 0u) {
        for (var i = 0u; i < 8u; i = i + 1u) { total_hearts[i] += states[g_gid].player0.heart_buffs[i]; }
        total_blades += states[g_gid].player0.blade_buffs[0] + states[g_gid].player0.blade_buffs[1] + states[g_gid].player0.blade_buffs[2];
    } else {
        for (var i = 0u; i < 8u; i = i + 1u) { total_hearts[i] += states[g_gid].player1.heart_buffs[i]; }
        total_blades += states[g_gid].player1.blade_buffs[0] + states[g_gid].player1.blade_buffs[1] + states[g_gid].player1.blade_buffs[2];
    }
    for (var i = 0u; i < 8u; i = i + 1u) { set_board_heart(p_idx, i, total_hearts[i]); }
    if (p_idx == 0u) {
        states[g_gid].player0.board_blades = total_blades;
    } else {
        states[g_gid].player1.board_blades = total_blades;
    }
}

fn calculate_live_success_prob(p_idx: u32, lid: u32) -> f32 {
    if (lid == 0u || lid >= arrayLength(&card_stats)) { return 0.0; }
    let ls = card_stats[lid];
    
    var req = array<i32, 7>(0,0,0,0,0,0,0);
    req[0] = i32((ls.hearts_lo >> 0u) & 0xFFu);
    req[1] = i32((ls.hearts_lo >> 8u) & 0xFFu);
    req[2] = i32((ls.hearts_lo >> 16u) & 0xFFu);
    req[3] = i32((ls.hearts_lo >> 24u) & 0xFFu);
    req[4] = i32((ls.hearts_hi >> 0u) & 0xFFu);
    req[5] = i32((ls.hearts_hi >> 8u) & 0xFFu);
    req[6] = i32((ls.hearts_hi >> 16u) & 0xFFu);

    var rlo = 0u; var rhi = 0u; var alo = 0u; var ahi = 0u;
    if (p_idx == 0u) {
        rlo = states[g_gid].player0.heart_req_reductions[0];
        rhi = states[g_gid].player0.heart_req_reductions[1];
        alo = states[g_gid].player0.heart_req_additions[0];
        ahi = states[g_gid].player0.heart_req_additions[1];
    } else {
        rlo = states[g_gid].player1.heart_req_reductions[0];
        rhi = states[g_gid].player1.heart_req_reductions[1];
        alo = states[g_gid].player1.heart_req_additions[0];
        ahi = states[g_gid].player1.heart_req_additions[1];
    }

    req[0] = max(0, req[0] - i32((rlo >> 0u) & 0xFFu) + i32((alo >> 0u) & 0xFFu));
    req[1] = max(0, req[1] - i32((rlo >> 8u) & 0xFFu) + i32((alo >> 8u) & 0xFFu));
    req[2] = max(0, req[2] - i32((rlo >> 16u) & 0xFFu) + i32((alo >> 16u) & 0xFFu));
    req[3] = max(0, req[3] - i32((rlo >> 24u) & 0xFFu) + i32((alo >> 24u) & 0xFFu));
    req[4] = max(0, req[4] - i32((rhi >> 0u) & 0xFFu) + i32((ahi >> 0u) & 0xFFu));
    req[5] = max(0, req[5] - i32((rhi >> 8u) & 0xFFu) + i32((ahi >> 8u) & 0xFFu));
    req[6] = max(0, req[6] - i32((rhi >> 16u) & 0xFFu) + i32((ahi >> 16u) & 0xFFu));

    var missing: i32 = 0;
    for (var i = 0u; i < 7u; i = i + 1u) {
        let board_h = get_board_heart(p_idx, i);
        let diff = req[i] - i32(board_h);
        if (diff > 0) { missing += diff; }
    }
    
    var board_blades = 0u;
    var yell_red = 0u;
    if (p_idx == 0u) {
        board_blades = states[g_gid].player0.board_blades;
        yell_red = states[g_gid].player0.yell_count_reduction;
    } else {
        board_blades = states[g_gid].player1.board_blades;
        yell_red = states[g_gid].player1.yell_count_reduction;
    }

    let b_hearts = get_board_heart(p_idx, 7u); 
    let total_blades = board_blades + b_hearts;
    if (i32(total_blades) >= missing) { return 1.0; }
    
    let needed = u32(missing - i32(total_blades));
    let k_yells = max(0i, i32(ls.volume_icons) - i32(yell_red));
    if (k_yells <= 0) { return 0.0; }

    var d_len = 0u; var disc_len = 0u;
    if (p_idx == 0u) {
        d_len = states[g_gid].player0.deck_len;
        disc_len = states[g_gid].player0.discard_pile_len;
    } else {
        d_len = states[g_gid].player1.deck_len;
        disc_len = states[g_gid].player1.discard_pile_len;
    }

    let total_pool = d_len + disc_len;
    let actual_yells = min(u32(k_yells), total_pool);
    let N = total_pool;
    let n = actual_yells;

    // Calculate successes K in pool N
    var total_avg_yield: f32 = 0.0;
    if (p_idx == 0u) {
        for (var j = 0u; j < 8u; j = j + 1u) { total_avg_yield += f32(states[g_gid].player0.avg_hearts[j]) / 255.0; }
    } else {
        for (var j = 0u; j < 8u; j = j + 1u) { total_avg_yield += f32(states[g_gid].player1.avg_hearts[j]) / 255.0; }
    }
    let K = u32(f32(N) * total_avg_yield + 0.5);

    if (needed > n || needed > K) { return 0.0; }
    if (needed == 0u) { return 1.0; }

    // Start with PMF(0) = combinations(N-K, n) / combinations(N, n)
    var current_pmf: f32 = 1.0;
    if (N - K < n) {
        current_pmf = 0.0; // Impossible to have 0 successes if n > N-K
    } else {
        for (var i = 1u; i <= n; i = i + 1u) {
            current_pmf = current_pmf * f32(N - K - n + i) / f32(N - n + i);
        }
    }
    
    var prob: f32 = 0.0;
    if (0u >= needed) { prob += current_pmf; }

    for (var k = 0u; k < n; k = k + 1u) {
        if (k >= K) { break; }
        let num = f32(K - k) * f32(n - k);
        let den = f32(k + 1u) * f32(N - K - n + (k + 1u));
        if (den > 0.0) {
            current_pmf = current_pmf * num / den;
        } else {
            current_pmf = 0.0;
        }
        if ((k + 1u) >= needed) { prob += current_pmf; }
    }
    return clamp(prob, 0.0, 1.0);
}

fn resolve_performance_gpu() {
    var p0_success = true;
    var p0_score = 0u;
    var p0_live_count = 0u;
    for (var i = 0u; i < 3u; i = i + 1u) {
        let lid = get_live_card(0u, i);
        if (lid > 0u) {
            p0_live_count += 1u;
            let prob = calculate_live_success_prob(0u, lid);
            if ((f32(rng_jump() % 1000u) / 1000.0) >= prob) { p0_success = false; }
            else { p0_score += card_stats[lid].extra_val; }
        }
    }
    if (p0_live_count > 0u && p0_success) { p0_score += states[g_gid].player0.board_blades; } 
    else { p0_score = 0u; p0_success = false; }

    var p1_success = true;
    var p1_score = 0u;
    var p1_live_count = 0u;
    for (var i = 0u; i < 3u; i = i + 1u) {
        let lid = get_live_card(1u, i);
        if (lid > 0u) {
            p1_live_count += 1u;
            let prob = calculate_live_success_prob(1u, lid);
            if ((f32(rng_jump() % 1000u) / 1000.0) >= prob) { p1_success = false; }
            else { p1_score += card_stats[lid].extra_val; }
        }
    }
    if (p1_live_count > 0u && p1_success) { p1_score += states[g_gid].player1.board_blades; }
    else { p1_score = 0u; p1_success = false; }

    if (p0_score > 0u || p1_score > 0u) {
        if (p0_score >= p1_score) { add_to_success_pile(0u, 999u); } 
        if (p1_score >= p0_score) { add_to_success_pile(1u, 999u); }
        
        states[g_gid].player0.live_zone[0] = 0u;
        states[g_gid].player0.live_zone[1] = 0u;
        states[g_gid].player1.live_zone[0] = 0u;
        states[g_gid].player1.live_zone[1] = 0u;
    }
}
