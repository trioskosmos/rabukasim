fn resolve_target_slot(target_slot: u32, ctx_slot: u32) -> u32 {
    if (target_slot == 4u && ctx_slot < 3u) { return ctx_slot; }
    if (target_slot >= 3u) { return 0u; } 
    return target_slot;
}

struct TriggerRequest {
    card_id: u32,
    slot_idx: u32,
    trigger_filter: i32,
    ab_filter: i32,
    choice: i32,
}

fn push_trigger(card_id: u32, slot_idx: u32, trigger_filter: i32, ab_filter: i32, choice: i32) {
    let tail = states[g_gid].queue_tail;
    if (tail < 8u) {
        states[g_gid].trigger_queue[tail].card_id = card_id;
        states[g_gid].trigger_queue[tail].slot_idx = slot_idx;
        states[g_gid].trigger_queue[tail].trigger_filter = trigger_filter;
        states[g_gid].trigger_queue[tail].ab_filter = ab_filter;
        states[g_gid].trigger_queue[tail].choice = choice;
        states[g_gid].queue_tail = tail + 1u;
    }
}

fn match_filter(cid: u32, a_lo: u32, a_hi: u32) -> bool {
    if (cid == 0u || cid >= arrayLength(&card_stats)) { return false; }
    let s = card_stats[cid];

    // Cost Filter (bits 24-30 of a_lo)
    if ((a_lo & 0x01000000u) != 0u) {
        let cost_value = (a_lo >> 25u) & 0x1Fu;
        let is_le = (a_lo & 0x40000000u) != 0u;
        if (is_le) {
            if (s.cost > cost_value) { return false; }
        } else {
            if (s.cost < cost_value) { return false; }
        }
    }

    // Group Filter (a_lo bits 5-11)
    if ((a_lo & 0x10u) != 0u) {
        let gid = (a_lo >> 5u) & 0x7Fu;
        let g = s.groups;
        if (((g >> 0u) & 0xFFu) != gid && ((g >> 8u) & 0xFFu) != gid && 
            ((g >> 16u) & 0xFFu) != gid && ((g >> 24u) & 0xFFu) != gid) { return false; }
    }

    // Unit Filter (a_lo bits 17-23)
    if ((a_lo & 0x10000u) != 0u) {
        let uid = (a_lo >> 17u) & 0x7Fu;
        let u = s.units;
        if (((u >> 0u) & 0xFFu) != uid && ((u >> 8u) & 0xFFu) != uid && 
            ((u >> 16u) & 0xFFu) != uid && ((u >> 24u) & 0xFFu) != uid) { return false; }
    }

    // Color Filter (a_hi bits 28-31)
    if ((a_hi & 0x10000000u) != 0u) {
        let c_mask = (a_hi >> 29u) & 0x07u;
        var found_color = false;
        // Check first 3 colors (as per compiler's color_mask & 0x07)
        for (var c = 1u; c <= 3u; c = c + 1u) {
            if ((c_mask & (1u << (c - 1u))) != 0u) {
                let h_val = (s.hearts_lo >> ((c - 1u) * 8u)) & 0xFFu;
                if (h_val > 0u) { found_color = true; break; }
            }
        }
        if (!found_color) { return false; }
    }

    // Character Filter (a_hi)
    if ((a_hi & 0x00000400u) != 0u) { // FILTER_CHARACTER_ENABLE (Bit 10 of a_hi)
        let cid1 = a_hi & 0x7Fu;
        let cid2 = (a_hi >> 11u) & 0x7Fu;
        let cid3 = (a_hi >> 18u) & 0x7Fu;
        var char_matched = (s.char_id == cid1);
        if (cid2 > 0u && s.char_id == cid2) { char_matched = true; }
        if (cid3 > 0u && s.char_id == cid3) { char_matched = true; }
        if (!char_matched) { return false; }
    }

    // Attribute requirements (a_lo bits 12-14)
    if ((a_lo & 0x1000u) != 0u) { // is_tapped requirement
         // match_filter is usually used for selecting from zones, where tapped state might be relevant
         // But in rollout it's simplified. For now we ignore it to avoid false negatives.
    }

    // Type Filter (a_lo >> 2 & 0x03)
    let tf = (a_lo >> 2u) & 0x03u;
    if (tf == 1u && s.card_type != 1u) { return false; }
    if (tf == 2u && s.card_type != 2u) { return false; }
    return true;
}

fn add_heart_req_reduction(p_idx: u32, color: u32, amount: u32) {
    if (color >= 7u) { return; }
    let word_idx = color / 4u;
    let shift = (color % 4u) * 8u;
    if (p_idx == 0u) {
        let current = (states[g_gid].player0.heart_req_reductions[word_idx] >> shift) & 0xFFu;
        let new_val = min(current + amount, 255u);
        states[g_gid].player0.heart_req_reductions[word_idx] = (states[g_gid].player0.heart_req_reductions[word_idx] & ~(0xFFu << shift)) | (new_val << shift);
    } else {
        let current = (states[g_gid].player1.heart_req_reductions[word_idx] >> shift) & 0xFFu;
        let new_val = min(current + amount, 255u);
        states[g_gid].player1.heart_req_reductions[word_idx] = (states[g_gid].player1.heart_req_reductions[word_idx] & ~(0xFFu << shift)) | (new_val << shift);
    }
}

fn add_heart_req_addition(p_idx: u32, color: u32, amount: u32) {
    if (color >= 7u) { return; }
    let word_idx = color / 4u;
    let shift = (color % 4u) * 8u;
    if (p_idx == 0u) {
        let current = (states[g_gid].player0.heart_req_additions[word_idx] >> shift) & 0xFFu;
        let new_val = min(current + amount, 255u);
        states[g_gid].player0.heart_req_additions[word_idx] = (states[g_gid].player0.heart_req_additions[word_idx] & ~(0xFFu << shift)) | (new_val << shift);
    } else {
        let current = (states[g_gid].player1.heart_req_additions[word_idx] >> shift) & 0xFFu;
        let new_val = min(current + amount, 255u);
        states[g_gid].player1.heart_req_additions[word_idx] = (states[g_gid].player1.heart_req_additions[word_idx] & ~(0xFFu << shift)) | (new_val << shift);
    }
}

fn check_condition_opcode(p_idx: u32, op: i32, v: i32, a_lo: u32, a_hi: u32, target_slot: u32, ctx_cid: u32) -> bool {
    let cid = select(u32(states[g_gid].prev_card_id), ctx_cid, ctx_cid != 0u);
    switch (op) {
        case 200: { return states[g_gid].turn == 1u; }
        case 201: { 
            var count = 0u;
            for (var s = 0u; s < 3u; s = s + 1u) {
                if (get_stage_card(p_idx, s) == a_lo) { count = count + 1u; }
            }
            return count >= u32(v);
        }
        case 203: { 
            var count = 0u;
            for (var s = 0u; s < 3u; s = s + 1u) {
                if (get_stage_card(p_idx, s) > 0u) { count = count + 1u; }
            }
            return count >= u32(v);
        }
        case 204: {
            var h_len = 0u;
            if (p_idx == 0u) { h_len = states[g_gid].player0.hand_len; }
            else { h_len = states[g_gid].player1.hand_len; }
            return h_len >= u32(v);
        }
        case 202: { 
            let color_idx = a_lo;
            if (color_idx > 0u && color_idx < 7u) {
                for (var s = 0u; s < 3u; s = s + 1u) {
                    let s_cid = get_stage_card(p_idx, s);
                    if (s_cid > 0u && s_cid < arrayLength(&card_stats)) {
                        let hearts_lo = card_stats[s_cid].hearts_lo;
                        let hearts_hi = card_stats[s_cid].hearts_hi;
                        var val = 0u;
                        if (color_idx < 5u) { val = (hearts_lo >> ((color_idx - 1u) * 8u)) & 0xFFu; }
                        else { val = (hearts_hi >> ((color_idx - 5u) * 8u)) & 0xFFu; }
                        if (val > 0u) { return true; }
                    }
                }
            }
            return false;
        }
        case 207: { 
            var p_score = 0u; var o_score = 0u;
            if (p_idx == 0u) {
                p_score = states[g_gid].player0.score;
                o_score = states[g_gid].player1.score;
            } else {
                p_score = states[g_gid].player1.score;
                o_score = states[g_gid].player0.score;
            }
            return p_score > o_score;
        }
        case 208: { 
            var count = 0u;
            let group_id = a_lo;
            for (var s = 0u; s < 3u; s = s + 1u) {
                let s_cid = get_stage_card(p_idx, s);
                if (s_cid > 0u && s_cid < arrayLength(&card_stats)) {
                    let groups = card_stats[s_cid].groups;
                    if (((groups >> 0u) & 0xFFu) == group_id) { count = count + 1u; }
                    else if (((groups >> 8u) & 0xFFu) == group_id) { count = count + 1u; }
                    else if (((groups >> 16u) & 0xFFu) == group_id) { count = count + 1u; }
                    else if (((groups >> 24u) & 0xFFu) == group_id) { count = count + 1u; }
                }
            }
            return count >= u32(v);
        }
        case 209: { // C_GROUP_FILTER
            if (cid != 0u && cid < arrayLength(&card_stats)) {
                return match_filter(cid, a_lo, a_hi);
            }
            return false;
        }
        case 210: { // C_OPPONENT_HAS
             let filter_attr = a_lo;
             let o_idx = 1u - p_idx;
             for (var s = 0u; s < 3u; s = s + 1u) {
                 let s_cid = get_stage_card(o_idx, s);
                 if (s_cid > 0u) {
                     if (s_cid == u32(v)) { return true; }
                     if (filter_attr != 0u && match_filter(s_cid, filter_attr, a_hi)) { return true; }
                 }
             }
             return false;
        }
        case 211: { 
            var c_cid = 0u;
            if (target_slot < 3u) { c_cid = get_stage_card(p_idx, target_slot); }
            if (c_cid > 0u && c_cid < arrayLength(&card_stats)) {
                let groups = card_stats[c_cid].groups;
                if (((groups >> 0u) & 0xFFu) == a_lo) { return true; }
                if (((groups >> 8u) & 0xFFu) == a_lo) { return true; }
                if (((groups >> 16u) & 0xFFu) == a_lo) { return true; }
                if (((groups >> 24u) & 0xFFu) == a_lo) { return true; }
            }
            return false;
        }
        case 213: {
            var e_count = 0u;
            if (p_idx == 0u) { e_count = states[g_gid].player0.energy_count; }
            else { e_count = states[g_gid].player1.energy_count; }
            return e_count >= u32(v);
        }
        case 215: { 
            var avail = 0u;
            if (p_idx == 0u) {
                avail = states[g_gid].player0.energy_count - states[g_gid].player0.tapped_energy_count;
            } else {
                avail = states[g_gid].player1.energy_count - states[g_gid].player1.tapped_energy_count;
            }
            return avail >= u32(v);
        }
        case 216: { // C_RARITY_CHECK
             if (cid != 0u && cid < arrayLength(&card_stats)) {
                 return card_stats[cid].rarity == u32(v);
             }
             return false;
        }
        case 218: { // C_COUNT_SUCCESS_LIVE
             let filter_attr = a_lo;
             var count = 0u;
             let l_count = select(states[g_gid].player1.lives_cleared_count, states[g_gid].player0.lives_cleared_count, p_idx == 0u);
             // On GPU we don't store success pile, but we track count. 
             // If we need filtered count, we might need to store success pile IDs.
             // LL!SIC cards usually count ALL success lives regardless of filter for C_COUNT_SUCCESS_LIVE (limit 3).
             // However, for now we match the count directly.
             return l_count >= u32(v);
        }
        case 220: { 
            var my_val = 0i; var opp_val = 0i;
            if (p_idx == 0u) {
                my_val = i32(states[g_gid].player0.score);
                opp_val = i32(states[g_gid].player1.score);
            } else {
                my_val = i32(states[g_gid].player1.score);
                opp_val = i32(states[g_gid].player0.score);
            }
            let comp_op = (target_slot >> 4u) & 0x0Fu;
            switch (comp_op) {
                case 0u: { return my_val >= opp_val; }
                case 1u: { return my_val <= opp_val; }
                case 2u: { return my_val > opp_val; } 
                case 3u: { return my_val < opp_val; } 
                case 4u: { return my_val == opp_val; }
                default: { return my_val >= opp_val; }
            }
        }
        case 223: { 
            var total = 0u;
            for (var j = 0u; j < 7u; j = j + 1u) { total += get_board_heart(p_idx, j); }
            return total >= u32(v);
        }
        case 224: {
            var b_blades = 0u;
            if (p_idx == 0u) { b_blades = states[g_gid].player0.board_blades; }
            else { b_blades = states[g_gid].player1.board_blades; }
            return b_blades >= u32(v);
        }
        case 231: { 
            if (states[g_gid].prev_card_id >= 0) {
                let pcid = u32(states[g_gid].prev_card_id);
                if (pcid < arrayLength(&card_stats)) {
                    return card_stats[pcid].char_id == u32(v);
                }
            }
            var b_count = 0u;
            if (p_idx == 0u) { b_count = states[g_gid].player0.baton_touch_count; }
            else { b_count = states[g_gid].player1.baton_touch_count; }
            return b_count >= u32(v);
        }
        case 232: { // C_TYPE_CHECK
            if (cid != 0u && cid < arrayLength(&card_stats)) {
                let s_type = card_stats[cid].card_type;
                if ((v & 1) == 1) { return s_type == 2u; } // Live
                if ((v & 1) == 0) { return s_type == 1u; } // Member
            }
            return false;
        }
        case 233: { // C_IS_IN_DISCARD
            var d_len = 0u;
            if (p_idx == 0u) { d_len = states[g_gid].player0.discard_pile_len; }
            else { d_len = states[g_gid].player1.discard_pile_len; }
            for (var i = 0u; i < d_len; i = i + 1u) {
                if (get_discard_card(p_idx, i) == a_lo) { return true; }
            }
            return false;
        }
        case 205: { // C_COUNT_DISCARD
            var d_len = 0u;
            if (p_idx == 0u) { d_len = states[g_gid].player0.discard_pile_len; }
            else { d_len = states[g_gid].player1.discard_pile_len; }
            return d_len >= u32(v);
        }
        case 206: { // C_IS_CENTER
            // target_slot == 1 means center position
            return target_slot == 1u;
        }
        case 212: { // C_MODAL_ANSWER
            // Check if ctx_choice matches v
            // In GPU, we use choice from resolve_bytecode context
            return false; // Simplified: requires ctx_choice which is passed differently
        }
        case 214: { // C_HAS_LIVE_CARD
            // Check if player has any live cards in live zone
            // live_zone is array<u32, 2>, each holding 2 cards (4 cards max)
            // Check if any slot has a card (non-zero)
            if (p_idx == 0u) { 
                return states[g_gid].player0.live_zone[0] != 0u || states[g_gid].player0.live_zone[1] != 0u;
            }
            else { 
                return states[g_gid].player1.live_zone[0] != 0u || states[g_gid].player1.live_zone[1] != 0u;
            }
        }
        case 217: { // C_HAND_HAS_NO_LIVE
            // Check if hand contains no live cards
            var h_len = 0u;
            if (p_idx == 0u) { h_len = states[g_gid].player0.hand_len; }
            else { h_len = states[g_gid].player1.hand_len; }
            for (var i = 0u; i < h_len; i = i + 1u) {
                let h_cid = get_hand_card(p_idx, i);
                if (h_cid > 0u && h_cid < arrayLength(&card_stats)) {
                    if (card_stats[h_cid].card_type == 2u) { return false; } // Found a live
                }
            }
            return true;
        }
        case 219: { // C_OPPONENT_HAND_DIFF
            var my_h_len = 0u; var opp_h_len = 0u;
            if (p_idx == 0u) {
                my_h_len = states[g_gid].player0.hand_len;
                opp_h_len = states[g_gid].player1.hand_len;
            } else {
                my_h_len = states[g_gid].player1.hand_len;
                opp_h_len = states[g_gid].player0.hand_len;
            }
            return i32(opp_h_len) - i32(my_h_len) >= v;
        }
        case 221: { // C_HAS_CHOICE
            // Check if there's a pending interaction/choice
            // In GPU rollout, we typically don't have interaction stack
            return false;
        }
        case 222: { // C_OPPONENT_CHOICE
            // Check if the current choice is from opponent
            return false;
        }
        case 225: { // C_OPPONENT_ENERGY_DIFF
            var my_e = 0u; var opp_e = 0u;
            if (p_idx == 0u) {
                my_e = states[g_gid].player0.energy_count;
                opp_e = states[g_gid].player1.energy_count;
            } else {
                my_e = states[g_gid].player1.energy_count;
                opp_e = states[g_gid].player0.energy_count;
            }
            return i32(opp_e) - i32(my_e) >= v;
        }
        case 226: { // C_HAS_KEYWORD
            // Check for keywords like PLAYED_THIS_TURN, YELL_COUNT, HAS_LIVE_SET
            let keyword_flags = a_lo;
            if ((keyword_flags & 0x01u) != 0u) { // PLAYED_THIS_TURN
                // played_group_mask not in GpuPlayerState, use used_abilities_mask as proxy
                // This is a simplification - may not be 100% accurate
                var used_mask = 0u;
                if (p_idx == 0u) { used_mask = states[g_gid].player0.used_abilities_mask; }
                else { used_mask = states[g_gid].player1.used_abilities_mask; }
                if (used_mask == 0u) { return false; }
            }
            if ((keyword_flags & 0x02u) != 0u) { // YELL_COUNT
                // yell_count is not stored directly, use yell_count_reduction as proxy
                var yell_cnt = 0u;
                if (p_idx == 0u) { yell_cnt = states[g_gid].player0.yell_count_reduction; }
                else { yell_cnt = states[g_gid].player1.yell_count_reduction; }
                if (i32(yell_cnt) < v) { return false; }
            }
            if ((keyword_flags & 0x04u) != 0u) { // HAS_LIVE_SET
                if (p_idx == 0u) { 
                    if (states[g_gid].player0.live_zone[0] == 0u && states[g_gid].player0.live_zone[1] == 0u) { return false; }
                } else {
                    if (states[g_gid].player1.live_zone[0] == 0u && states[g_gid].player1.live_zone[1] == 0u) { return false; }
                }
            }
            return true;
        }
        case 227: { // C_DECK_REFRESHED
            // Check if deck was refreshed this game
            // deck_refreshed is not stored in GpuPlayerState, use heuristic
            // If deck_len is 0 and we're checking for refresh, return false
            return false; // Simplified: not tracked in GPU state
        }
        case 228: { // C_HAS_MOVED
            // Check if a card has moved this turn
            // moved_flags is the field name in GpuPlayerState
            if (target_slot < 3u) {
                if (p_idx == 0u) { return (states[g_gid].player0.moved_flags & (1u << target_slot)) != 0u; }
                else { return (states[g_gid].player1.moved_flags & (1u << target_slot)) != 0u; }
            }
            return false;
        }
        case 230: { // C_COUNT_LIVE_ZONE
            // Count live cards in live_zone (array<u32, 2>, each holding 2 cards)
            var count = 0u;
            if (p_idx == 0u) {
                let lz0 = states[g_gid].player0.live_zone[0];
                let lz1 = states[g_gid].player0.live_zone[1];
                if ((lz0 & 0xFFFFu) != 0u) { count += 1u; }
                if ((lz0 >> 16u) != 0u) { count += 1u; }
                if ((lz1 & 0xFFFFu) != 0u) { count += 1u; }
                if ((lz1 >> 16u) != 0u) { count += 1u; }
            } else {
                let lz0 = states[g_gid].player1.live_zone[0];
                let lz1 = states[g_gid].player1.live_zone[1];
                if ((lz0 & 0xFFFFu) != 0u) { count += 1u; }
                if ((lz0 >> 16u) != 0u) { count += 1u; }
                if ((lz1 & 0xFFFFu) != 0u) { count += 1u; }
                if ((lz1 >> 16u) != 0u) { count += 1u; }
            }
            return count >= u32(v);
        }
        case 234: { // C_AREA_CHECK
            // Check if card is in specific area
            // a encodes the area type
            return false; // Simplified
        }
        case 235: { // C_COST_LEAD
            // Compare costs between players
            return false; // Simplified
        }
        case 236: { // C_SCORE_LEAD
            var my_score = 0u; var opp_score = 0u;
            if (p_idx == 0u) {
                my_score = states[g_gid].player0.score;
                opp_score = states[g_gid].player1.score;
            } else {
                my_score = states[g_gid].player1.score;
                opp_score = states[g_gid].player0.score;
            }
            return i32(my_score) - i32(opp_score) >= v;
        }
        case 237: { // C_HEART_LEAD
            var my_hearts = 0u; var opp_hearts = 0u;
            for (var j = 0u; j < 7u; j = j + 1u) {
                my_hearts += get_board_heart(p_idx, j);
                opp_hearts += get_board_heart(1u - p_idx, j);
            }
            return i32(my_hearts) - i32(opp_hearts) >= v;
        }
        case 238: { // C_HAS_EXCESS_HEART
            // Check if player has more hearts than needed
            return false; // Simplified
        }
        case 239: { // C_NOT_HAS_EXCESS_HEART
            // Check if player does NOT have excess hearts
            return true; // Simplified
        }
        case 240: { // C_TOTAL_BLADES
            var total = 0u;
            if (p_idx == 0u) { total = states[g_gid].player0.board_blades; }
            else { total = states[g_gid].player1.board_blades; }
            return total >= u32(v);
        }
        case 241: { // C_COST_COMPARE
            return false; // Simplified
        }
        case 242: { // C_BLADE_COMPARE
            var my_blades = 0u; var opp_blades = 0u;
            if (p_idx == 0u) {
                my_blades = states[g_gid].player0.board_blades;
                opp_blades = states[g_gid].player1.board_blades;
            } else {
                my_blades = states[g_gid].player1.board_blades;
                opp_blades = states[g_gid].player0.board_blades;
            }
            let comp_op = (target_slot >> 4u) & 0x0Fu;
            if (comp_op == 0u) { return my_blades >= opp_blades; }
            if (comp_op == 1u) { return my_blades <= opp_blades; }
            if (comp_op == 2u) { return my_blades > opp_blades; }
            if (comp_op == 3u) { return my_blades < opp_blades; }
            return my_blades >= opp_blades;
        }
        case 243: { // C_HEART_COMPARE
            var my_hearts = 0u; var opp_hearts = 0u;
            for (var j = 0u; j < 7u; j = j + 1u) {
                my_hearts += get_board_heart(p_idx, j);
                opp_hearts += get_board_heart(1u - p_idx, j);
            }
            let comp_op = (target_slot >> 4u) & 0x0Fu;
            if (comp_op == 0u) { return my_hearts >= opp_hearts; }
            if (comp_op == 1u) { return my_hearts <= opp_hearts; }
            if (comp_op == 2u) { return my_hearts > opp_hearts; }
            if (comp_op == 3u) { return my_hearts < opp_hearts; }
            return my_hearts >= opp_hearts;
        }
        case 244: { // C_OPPONENT_HAS_WAIT
            // Check if opponent has cards in wait state
            return false; // Simplified
        }
        case 245: { // C_IS_TAPPED
            if (target_slot < 3u) {
                if (p_idx == 0u) { return (states[g_gid].player0.flags & (1u << (3u + target_slot))) != 0u; }
                else { return (states[g_gid].player1.flags & (1u << (3u + target_slot))) != 0u; }
            }
            return false;
        }
        case 246: { // C_IS_ACTIVE
            if (target_slot < 3u) {
                if (p_idx == 0u) { return (states[g_gid].player0.flags & (1u << (3u + target_slot))) == 0u; }
                else { return (states[g_gid].player1.flags & (1u << (3u + target_slot))) == 0u; }
            }
            return false;
        }
        case 247: { // C_LIVE_PERFORMED
            // Check if live was performed this turn
            return false; // Simplified
        }
        case 248: { // C_IS_PLAYER
            // Check if current player matches
            return true; // Simplified: always true for current player
        }
        case 249: { // C_IS_OPPONENT
            // Check if target is opponent
            return false; // Simplified
        }
        default: { return false; }
    }
}

fn resolve_bytecode(p_idx: u32, card_id: u32, slot_idx: u32, trigger_filter: i32, ab_filter: i32, start: u32, total_len: u32, choice: i32) {
    if (total_len == 0u) { return; }
    var pool_ip = start;
    let pool_end = start + total_len;
    let num_abilities = u32(bytecode[pool_ip]);
    pool_ip = pool_ip + 1u;
    
    for (var ab_idx = 0u; ab_idx < num_abilities; ab_idx = ab_idx + 1u) {
        if (pool_ip + 3u >= pool_end) { break; }
        let ab_trigger = bytecode[pool_ip];
        let is_once = bytecode[pool_ip + 1u] == 1;
        let internal_idx = u32(bytecode[pool_ip + 2u]);
        let ab_len = u32(bytecode[pool_ip + 3u]);
        pool_ip = pool_ip + 4u;
        
        if (trigger_filter >= 0 && ab_trigger != trigger_filter) { pool_ip = pool_ip + ab_len; continue; }
        if (ab_filter >= 0 && i32(ab_idx) != ab_filter) { pool_ip = pool_ip + ab_len; continue; }
        
        if (is_once) {
            let mask = 1u << (slot_idx * 4u + internal_idx);
            var used_mask = 0u;
            if (p_idx == 0u) { used_mask = states[g_gid].player0.used_abilities_mask; }
            else { used_mask = states[g_gid].player1.used_abilities_mask; }
            if ((used_mask & mask) != 0u) { pool_ip = pool_ip + ab_len; continue; }
            if (p_idx == 0u) { states[g_gid].player0.used_abilities_mask |= mask; }
            else { states[g_gid].player1.used_abilities_mask |= mask; }
        }

        var ip = pool_ip;
        let end = pool_ip + ab_len;
        var cond = true;
        var ctx_choice = choice;
        
        while (ip < end) {
            if (ip + 5u > end) { break; }
            let op = bytecode[ip]; let v = bytecode[ip + 1]; let a_lo = u32(bytecode[ip + 2]); let a_hi = u32(bytecode[ip + 3]); let s = bytecode[ip + 4];
            ip = ip + 5;
            let target_raw = u32(s);
            let target_slot = target_raw & 0xFFu;
            
            if (op <= 0) { continue; }
            if (op == O_RETURN) { break; }
            
            var real_op = op; var is_negated = false;
            if (real_op >= 1000) { real_op = real_op - 1000; is_negated = true; }
            
            if (real_op >= 200 && real_op <= 299) {
                let passed = check_condition_opcode(p_idx, real_op, v, a_lo, a_hi, target_slot, card_id);
                cond = passed; if (is_negated) { cond = !cond; }
                continue;
            }
            if (real_op == O_JUMP) { ip = u32(i32(ip) + v * 5); continue; }
            if (real_op == O_JUMP_IF_FALSE) { if (!cond) { ip = u32(i32(ip) + v * 5); } continue; }
            
            if (real_op >= 10 && real_op < 100) {
                switch (real_op) {
                    case O_DRAW: { for (var d = 0; d < v; d = d + 1) { draw_card(p_idx); } }
                    case 11, 18: { // O_ADD_BLADES / O_BUFF_POWER
                        let ab_t_slot = resolve_target_slot(target_slot, slot_idx);
                        if (p_idx == 0u) { states[g_gid].player0.blade_buffs[ab_t_slot] += u32(v); }
                        else { states[g_gid].player1.blade_buffs[ab_t_slot] += u32(v); }
                    }
                    case O_ADD_HEARTS: {
                        var color = a_lo;
                        if (color == 0u) { color = u32(ctx_choice); }
                        if (color < 8u) { add_board_heart(p_idx, color, u32(v)); }
                    }
                    case O_REDUCE_COST: {
                        if (p_idx == 0u) { states[g_gid].player0.cost_reduction += i32(v); }
                        else { states[g_gid].player1.cost_reduction += i32(v); }
                    }
                    case O_BOOST_SCORE: {
                         if (p_idx == 0u) { states[g_gid].player0.score += u32(v); }
                         else { states[g_gid].player1.score += u32(v); }
                    }
                    case O_RESTRICTION: {
                        if (a_lo == 1u) { // FLAG_CANNOT_LIVE
                            if (p_idx == 0u) { states[g_gid].player0.flags |= 1u; }
                            else { states[g_gid].player1.flags |= 1u; }
                        }
                    }
                    case O_BATON_TOUCH_MOD: {
                        if (p_idx == 0u) { states[g_gid].player0.baton_touch_limit = u32(i32(states[g_gid].player0.baton_touch_limit) + v); }
                        else { states[g_gid].player1.baton_touch_limit = u32(i32(states[g_gid].player1.baton_touch_limit) + v); }
                    }

                     case O_ENERGY_CHARGE: {
                          let count = u32(v);
                          if (p_idx == 0u) {
                              let real_add = min(count, states[g_gid].player0.energy_deck_len);
                              states[g_gid].player0.energy_count += real_add;
                              states[g_gid].player0.energy_deck_len -= real_add;
                          } else {
                              let real_add = min(count, states[g_gid].player1.energy_deck_len);
                              states[g_gid].player1.energy_count += real_add;
                              states[g_gid].player1.energy_deck_len -= real_add;
                          }
                     }
                    case O_IMMUNITY: {
                         let imm_t_slot = resolve_target_slot(target_slot, slot_idx);
                         if (p_idx == 0u) {
                             if (v != 0) { states[g_gid].player0.flags |= (1u << 2u); }
                             else { states[g_gid].player0.flags &= ~(1u << 2u); }
                         } else {
                             if (v != 0) { states[g_gid].player1.flags |= (1u << 2u); }
                             else { states[g_gid].player1.flags &= ~(1u << 2u); }
                         }
                    }
                    case O_SET_BLADES: {
                         let sb_t_slot = resolve_target_slot(target_slot, slot_idx);
                         if (p_idx == 0u) { states[g_gid].player0.blade_buffs[sb_t_slot] = u32(v); }
                         else { states[g_gid].player1.blade_buffs[sb_t_slot] = u32(v); }
                    }
                    case O_SET_HEARTS: {
                        let color = a_lo;
                        if (color < 8u) {
                            if (p_idx == 0u) { states[g_gid].player0.heart_buffs[color] = u32(v); }
                            else { states[g_gid].player1.heart_buffs[color] = u32(v); }
                        }
                    }
                    case O_MOVE_MEMBER, 26: { // O_MOVE_MEMBER / O_FORMATION_CHANGE
                        var mv_src = slot_idx;
                        if (real_op != O_MOVE_MEMBER || mv_src >= 3u) {
                             mv_src = resolve_target_slot(target_slot, slot_idx);
                        }
                        let mv_dst = a_lo;
                        if (mv_src < 3u && mv_dst < 3u && mv_src != mv_dst) {
                            var src_cid = 0u; var dst_cid = 0u;
                            if (p_idx == 0u) {
                                set_stage_card(0u, mv_src, dst_cid);
                                set_stage_card(0u, mv_dst, src_cid);
                                set_moved(0u, mv_src);
                                set_moved(0u, mv_dst);
                            } else {
                                src_cid = get_stage_card(1u, mv_src); dst_cid = get_stage_card(1u, mv_dst);
                                set_stage_card(1u, mv_src, dst_cid);
                                set_stage_card(1u, mv_dst, src_cid);
                                set_moved(1u, mv_src);
                                set_moved(1u, mv_dst);
                            }
                        }
                    }
                    case O_SWAP_CARDS: {
                         let count = u32(v);
                         for (var i = 0u; i < count; i = i + 1u) {
                             let cid = pop_deck(p_idx);
                             if (cid == 0u) { break; }
                             if (target_slot == 6u) { add_to_hand(p_idx, cid); }
                             else { add_to_discard(p_idx, cid); }
                         }
                    }
                    case O_SEARCH_DECK: {
                         // Simplify for GPU: just draw count if not interactive
                         draw_card(p_idx);
                    }
                    case O_SELECT_MODE: { ctx_choice = choice; }
                    case O_LOOK_DECK: {
                         // Basic reveal logic: move v cards from deck to discard (simplified, GPU doesn't have looked_cards)
                         let count = u32(v);
                         for (var i = 0u; i < count; i = i + 1u) {
                             let cid = pop_deck(p_idx);
                             if (cid == 0u) { break; }
                             add_to_discard(p_idx, cid);
                         }
                    }
                    case O_REVEAL_UNTIL: {
                        let cond_v = i32(v);
                        var found_cid = 0u; var r_idx = 0u;
                        var cards = array<u32, 60>(0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 
                                                   0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u, 0u,0u,0u);
                        let rev_t_slot = u32(s) & 0xFFu;
                        for (var i = 0u; i < 60u; i = i + 1u) {
                            let cid = pop_deck(p_idx);
                            if (cid == 0u) { break; }
                            cards[i] = cid;
                            if (check_condition_opcode(p_idx, cond_v, i32(a_lo), a_lo, a_hi, rev_t_slot, cid)) {
                                found_cid = cid; r_idx = i; break;
                            }
                        }
                        if (found_cid != 0u) {
                            if (rev_t_slot == 6u) { add_to_hand(p_idx, found_cid); }
                            else { add_to_discard(p_idx, found_cid); }
                            cards[r_idx] = 0u;
                        }
                        let rem_dest = (u32(s) >> 8u) & 0xFFu;
                        for (var i = 0u; i < 60u; i = i + 1u) {
                            if (cards[i] != 0u) {
                                if (rem_dest == 8u) { add_to_deck_bottom(p_idx, cards[i]); }
                                else { add_to_discard(p_idx, cards[i]); }
                            }
                        }
                    }
                    case O_RECOVER_LIVE, O_RECOVER_MEMBER: {
                        let is_live = real_op == 15i;
                        var match_count = 0u;
                        var found_cid = 0u;
                        var d_idx = 0u;
                        var d_len = 0u;
                        if (p_idx == 0u) { d_len = states[g_gid].player0.discard_pile_len; }
                        else { d_len = states[g_gid].player1.discard_pile_len; }
                        
                        for (var i = 0u; i < d_len; i = i + 1u) {
                            let cid = get_discard_card(p_idx, i);
                            let s_type = card_stats[cid].card_type;
                            if ((is_live && s_type == 2u) || (!is_live && s_type == 1u)) {
                                if (i32(match_count) == ctx_choice) {
                                    found_cid = cid;
                                    d_idx = i;
                                    break;
                                }
                                match_count += 1u;
                            }
                        }
                        if (found_cid != 0u) {
                            add_to_hand(p_idx, found_cid);
                            remove_from_discard(p_idx, d_idx);
                        }
                    }
                    case O_LOOK_AND_CHOOSE: {
                        let look_count = u32(v & 0xFFi);
                        var cards = array<u32, 10>(0u,0u,0u,0u,0u,0u,0u,0u,0u,0u);
                        let actual_look = min(look_count, 10u);
                        for (var i = 0u; i < actual_look; i = i + 1u) {
                            cards[i] = pop_deck(p_idx);
                        }
                        let safe_choice = select(0u, u32(ctx_choice), ctx_choice >= 0);
                        let lc_t_slot = u32(s) & 0xFFu;
                        let rem_dest = (u32(s) >> 8u) & 0xFFu;
                        if (safe_choice < actual_look) {
                            let picked = cards[safe_choice];
                            cards[safe_choice] = 0u;
                            // lc_t_slot: 1=HAND (legacy), 6=HAND, 4=STAGE, 7=DISCARD
                            if (lc_t_slot == 6u || lc_t_slot == 1u) { add_to_hand(p_idx, picked); }
                            else if (lc_t_slot == 4u) { 
                                // Stage - place in slot 0 for now (simplified)
                                set_stage_card(p_idx, 0u, picked);
                            }
                            else { add_to_discard(p_idx, picked); }
                        }
                        for (var i = 0u; i < actual_look; i = i + 1u) {
                            if (cards[i] != 0u) {
                                if (rem_dest == 8u) { add_to_deck_bottom(p_idx, cards[i]); }
                                else { add_to_discard(p_idx, cards[i]); }
                            }
                        }
                    }
                    case O_MOVE_TO_DECK: {
                        // v = count, a_lo/a_hi = attr (filter), s = target
                        // source zone in bits 16-23 of s
                        let source_zone = (u32(s) >> 16u) & 0x1Fu;
                        let count = u32(v);
                        
                        // Determine destination: deck_top (s bit 0) or deck_bottom
                        let to_top = (u32(s) & 0x01u) == 0u;
                        
                        for (var k = 0u; k < count; k = k + 1u) {
                            var card_id = 0u;
                            
                            // Remove from source zone
                            if (source_zone == 6u) { // Hand
                                var h_len = 0u;
                                if (p_idx == 0u) { h_len = states[g_gid].player0.hand_len; }
                                else { h_len = states[g_gid].player1.hand_len; }
                                if (h_len > 0u) {
                                    let choice_idx = select(u32(ctx_choice), h_len - 1u, ctx_choice >= 0i);
                                    if (choice_idx < h_len) {
                                        card_id = get_hand_card(p_idx, choice_idx);
                                        remove_from_hand(p_idx, choice_idx);
                                    }
                                }
                            } else if (source_zone == 4u) { // Stage
                                let stage_slot = u32(s) & 0x0Fu;
                                if (stage_slot < 3u) {
                                    card_id = get_stage_card(p_idx, stage_slot);
                                    if (card_id > 0u) {
                                        set_stage_card(p_idx, stage_slot, 0u);
                                    }
                                }
                            } else if (source_zone == 13u) { // Discard
                                var d_len = 0u;
                                if (p_idx == 0u) { d_len = states[g_gid].player0.discard_pile_len; }
                                else { d_len = states[g_gid].player1.discard_pile_len; }
                                if (d_len > 0u) {
                                    card_id = get_discard_card(p_idx, d_len - 1u);
                                    remove_from_discard(p_idx, d_len - 1u);
                                }
                            }
                            
                            // Add to deck
                            if (card_id > 0u) {
                                if (to_top) {
                                    add_to_deck_top(p_idx, card_id);
                                } else {
                                    add_to_deck_bottom(p_idx, card_id);
                                }
                            }
                        }
                    }
                    case O_TAP_OPPONENT: {
                        let o_idx = 1u - p_idx;
                        let target_slot_val = u32(choice);
                        if (target_slot_val < 3u) {
                             if (o_idx == 0u) { states[g_gid].player0.flags |= (1u << (3u + target_slot_val)); }
                             else { states[g_gid].player1.flags |= (1u << (3u + target_slot_val)); }
                        }
                    }
                    case O_COLOR_SELECT: { ctx_choice = choice; }
                    case O_DRAW_UNTIL: {
                        let limit = u32(v);
                        for (var d = 0u; d < 10u; d = d + 1u) { 
                            var du_h_len = 0u;
                            if (p_idx == 0u) { du_h_len = states[g_gid].player0.hand_len; }
                            else { du_h_len = states[g_gid].player1.hand_len; }
                            if (du_h_len >= limit) { break; }
                            draw_card(p_idx);
                        }
                    }
                    case O_PAY_ENERGY: {
                        let cost = u32(v);
                        if (p_idx == 0u) { states[g_gid].player0.tapped_energy_count += cost; }
                        else { states[g_gid].player1.tapped_energy_count += cost; }
                    }
                    case O_ACTIVATE_ENERGY: {
                        let count = u32(v);
                        if (p_idx == 0u) {
                            let t_count = states[g_gid].player0.tapped_energy_count;
                            states[g_gid].player0.tapped_energy_count = select(t_count - count, 0u, count >= t_count);
                        } else {
                            let t_count = states[g_gid].player1.tapped_energy_count;
                            states[g_gid].player1.tapped_energy_count = select(t_count - count, 0u, count >= t_count);
                        }
                    }
                    case O_SET_SCORE: {
                        if (p_idx == 0u) { states[g_gid].player0.score = u32(v); }
                        else { states[g_gid].player1.score = u32(v); }
                    }
                    case O_ACTIVATE_MEMBER: {
                        let resolved_target = resolve_target_slot(target_slot, slot_idx);
                        if (target_slot == 1u) { // Special: ALL
                             if (p_idx == 0u) { states[g_gid].player0.flags &= ~(0x7u << 3u); }
                             else { states[g_gid].player1.flags &= ~(0x7u << 3u); }
                        } else if (resolved_target < 3u) {
                             if (p_idx == 0u) { states[g_gid].player0.flags &= ~(1u << (3u + resolved_target)); }
                             else { states[g_gid].player1.flags &= ~(1u << (3u + resolved_target)); }
                        }
                    }
                    case O_TAP_MEMBER: {
                        let tap_target = resolve_target_slot(target_slot, slot_idx);
                        if (tap_target < 3u) {
                             if (p_idx == 0u) { states[g_gid].player0.flags |= (1u << (3u + tap_target)); }
                             else { states[g_gid].player1.flags |= (1u << (3u + tap_target)); }
                        }
                    }
                    case O_SET_TAPPED: {
                        let set_t_target = resolve_target_slot(target_slot, slot_idx);
                        if (set_t_target < 3u) {
                             if (v != 0) {
                                 if (p_idx == 0u) { states[g_gid].player0.flags |= (1u << (3u + set_t_target)); }
                                 else { states[g_gid].player1.flags |= (1u << (3u + set_t_target)); }
                             } else {
                                 if (p_idx == 0u) { states[g_gid].player0.flags &= ~(1u << (3u + set_t_target)); }
                                 else { states[g_gid].player1.flags &= ~(1u << (3u + set_t_target)); }
                             }
                        }
                    }
                    case O_REDUCE_HEART_REQ: {
                         // CPU uses s as color index, v as amount
                         let color = u32(s);
                         if (color < 7u) {
                             add_heart_req_reduction(p_idx, color, u32(v));
                         }
                    }
                    case O_INCREASE_HEART_COST: {
                         add_heart_req_addition(p_idx, u32(s), u32(v));
                    }
                    case O_SET_HEART_COST: {
                         // Set heart cost for a specific color (s = color index, v = amount)
                         let color = u32(s);
                         if (color < 7u) {
                             let word_idx = color / 4u;
                             let shift = (color % 4u) * 8u;
                             let new_val = min(u32(v), 255u);
                             if (p_idx == 0u) {
                                 states[g_gid].player0.heart_req_additions[word_idx] = 
                                     (states[g_gid].player0.heart_req_additions[word_idx] & ~(0xFFu << shift)) | (new_val << shift);
                             } else {
                                 states[g_gid].player1.heart_req_additions[word_idx] = 
                                     (states[g_gid].player1.heart_req_additions[word_idx] & ~(0xFFu << shift)) | (new_val << shift);
                             }
                         }
                    }
                    case O_INCREASE_COST: {
                        if (p_idx == 0u) { states[g_gid].player0.cost_reduction -= i32(v); }
                        else { states[g_gid].player1.cost_reduction -= i32(v); }
                    }
                    case O_REDUCE_YELL_COUNT: {
                        if (p_idx == 0u) { states[g_gid].player0.yell_count_reduction = u32(v); }
                        else { states[g_gid].player1.yell_count_reduction = u32(v); }
                    }
                    case O_REDUCE_LIVE_SET_LIMIT: {
                        if (p_idx == 0u) { states[g_gid].player0.prevent_success_pile_set += u32(v); }
                        else { states[g_gid].player1.prevent_success_pile_set += u32(v); }
                    }
                    case O_PREVENT_ACTIVATE: {
                        if (p_idx == 0u) { states[g_gid].player0.prevent_activate += u32(v); }
                        else { states[g_gid].player1.prevent_activate += u32(v); }
                    }
                    case O_PREVENT_SET_TO_SUCCESS_PILE: {
                        if (p_idx == 0u) { states[g_gid].player0.prevent_success_pile_set += u32(v); }
                        else { states[g_gid].player1.prevent_success_pile_set += u32(v); }
                    }
                    case O_PREVENT_BATON_TOUCH: {
                        if (p_idx == 0u) { states[g_gid].player0.prevent_baton_touch += u32(v); }
                        else { states[g_gid].player1.prevent_baton_touch += u32(v); }
                    }
                    case 58: { // O_MOVE_TO_DISCARD
                        let zone = select(target_slot, (u32(s) >> 16u) & 0xFFu, ((u32(s) >> 16u) & 0xFFu) != 0u);
                        if (zone == 6u || target_slot == 6u) { // Hand
                            let count = u32(v);
                            for (var k = 0u; k < count; k = k + 1u) {
                                 var md_h_len = 0u;
                                 if (p_idx == 0u) { md_h_len = states[g_gid].player0.hand_len; }
                                 else { md_h_len = states[g_gid].player1.hand_len; }
                                 if (md_h_len == 0u) { break; }
                                 
                                 let r_cid = get_hand_card(p_idx, md_h_len - 1u);
                                 add_to_discard(p_idx, r_cid);
                                 remove_from_hand(p_idx, md_h_len - 1u);
                            }
                        }
                    }
                    case O_PLAY_MEMBER_FROM_HAND: {
                        let filter_lo = a_lo;
                        let filter_hi = a_hi;
                        let dst_slot = u32(s) & 0x0Fu;
                        let choice_card_idx = u32(choice);
                        var pm_h_len = 0u;
                        if (p_idx == 0u) { pm_h_len = states[g_gid].player0.hand_len; }
                        else { pm_h_len = states[g_gid].player1.hand_len; }

                        if (choice_card_idx < pm_h_len && dst_slot < 3u) {
                            let pm_cid = get_hand_card(p_idx, choice_card_idx);
                            if (pm_cid != 0u && match_filter(pm_cid, filter_lo, filter_hi)) {
                                let target_cid = get_stage_card(p_idx, dst_slot);
                                if (target_cid > 0u) { add_to_discard(p_idx, target_cid); }
                                remove_from_hand(p_idx, choice_card_idx);
                                set_stage_card(p_idx, dst_slot, pm_cid);
                                set_moved(p_idx, dst_slot);
                                 let pm_stats = card_stats[pm_cid];
                                 if (pm_stats.bytecode_len > 0u) { push_trigger(pm_cid, dst_slot, 1i, -1i, -1i); }
                             }
                        }
                    }
                    case O_PLAY_MEMBER_FROM_DISCARD: {
                        let filter_lo_d = a_lo;
                        let filter_hi_d = a_hi;
                        let dst_slot_d = u32(s) & 0x0Fu;
                        let choice_disc_idx = u32(choice);
                        var pmd_d_len = 0u;
                        if (p_idx == 0u) { pmd_d_len = states[g_gid].player0.discard_pile_len; }
                        else { pmd_d_len = states[g_gid].player1.discard_pile_len; }

                        if (choice_disc_idx < pmd_d_len && dst_slot_d < 3u) {
                            let pmd_cid = get_discard_card(p_idx, choice_disc_idx);
                            if (pmd_cid != 0u && match_filter(pmd_cid, filter_lo_d, filter_hi_d)) {
                                let target_cid_d = get_stage_card(p_idx, dst_slot_d);
                                if (target_cid_d > 0u) { add_to_discard(p_idx, target_cid_d); }
                                remove_from_discard(p_idx, choice_disc_idx);
                                set_stage_card(p_idx, dst_slot_d, pmd_cid);
                                set_moved(p_idx, dst_slot_d);
                                 let pmd_stats = card_stats[pmd_cid];
                                 if (pmd_stats.bytecode_len > 0u) { push_trigger(pmd_cid, dst_slot_d, 1i, -1i, -1i); }
                             }
                        }
                    }
                    case O_GRANT_ABILITY: {
                        let ga_t_slot = resolve_target_slot(target_slot, slot_idx);
                        let ga_target_cid = get_stage_card(p_idx, ga_t_slot);
                        if (ga_target_cid != 0u) {
                             for (var i = 0u; i < 8u; i = i + 1u) {
                                 let word0_idx = i * 2u;
                                 let word1_idx = i * 2u + 1u;
                                 var ga_entry = 0u;
                                 if (p_idx == 0u) { ga_entry = states[g_gid].player0.granted_abilities[word0_idx]; }
                                 else { ga_entry = states[g_gid].player1.granted_abilities[word0_idx]; }
                                 
                                 if (ga_entry == 0u) {
                                     let packed0 = (ga_target_cid & 0xFFFFu) | (u32(card_id) << 16u);
                                     let packed1 = u32(v);
                                     if (p_idx == 0u) {
                                         states[g_gid].player0.granted_abilities[word0_idx] = packed0;
                                         states[g_gid].player0.granted_abilities[word1_idx] = packed1;
                                     } else {
                                         states[g_gid].player1.granted_abilities[word0_idx] = packed0;
                                         states[g_gid].player1.granted_abilities[word1_idx] = packed1;
                                     }
                                     break;
                                 }
                             }
                        }
                    }
                    case O_TRANSFORM_HEART: {
                        let src_color = a_lo; let dst_color = u32(s);
                        let amt = u32(abs(v));
                        let s_word = src_color / 4u; let s_shift = (src_color % 4u) * 8u;
                        let d_word = dst_color / 4u; let d_shift = (dst_color % 4u) * 8u;
                        if (p_idx == 0u) {
                             let src_red = (states[g_gid].player0.heart_req_reductions[s_word] >> s_shift) & 0xFFu;
                             let actual_amt = min(amt, src_red);
                             states[g_gid].player0.heart_req_reductions[s_word] &= ~(0xFFu << s_shift);
                             states[g_gid].player0.heart_req_reductions[s_word] |= (src_red - actual_amt) << s_shift;
                             let dst_red = (states[g_gid].player0.heart_req_reductions[d_word] >> d_shift) & 0xFFu;
                             states[g_gid].player0.heart_req_reductions[d_word] &= ~(0xFFu << d_shift);
                             states[g_gid].player0.heart_req_reductions[d_word] |= min(dst_red + actual_amt, 255u) << d_shift;
                        } else {
                             let src_red = (states[g_gid].player1.heart_req_reductions[s_word] >> s_shift) & 0xFFu;
                             let actual_amt = min(amt, src_red);
                             states[g_gid].player1.heart_req_reductions[s_word] &= ~(0xFFu << s_shift);
                             states[g_gid].player1.heart_req_reductions[s_word] |= (src_red - actual_amt) << s_shift;
                             let dst_red = (states[g_gid].player1.heart_req_reductions[d_word] >> d_shift) & 0xFFu;
                             states[g_gid].player1.heart_req_reductions[d_word] &= ~(0xFFu << d_shift);
                             states[g_gid].player1.heart_req_reductions[d_word] |= min(dst_red + actual_amt, 255u) << d_shift;
                        }
                    }
                    case O_PLAY_LIVE_FROM_DISCARD: {
                         let choice_disc_idx = u32(choice);
                         var d_len = 0u;
                         if (p_idx == 0u) { d_len = states[g_gid].player0.discard_pile_len; }
                         else { d_len = states[g_gid].player1.discard_pile_len; }
                         if (choice_disc_idx < d_len) {
                             let cid = get_discard_card(p_idx, choice_disc_idx);
                             if (cid != 0u && card_stats[cid].card_type == 2u) {
                                 for (var i = 0u; i < 3u; i = i + 1u) {
                                     if (get_live_card(p_idx, i) == 0u) {
                                         remove_from_discard(p_idx, choice_disc_idx);
                                         set_live_card(p_idx, i, cid);
                                         break;
                                     }
                                 }
                             }
                         }
                    }
                    case O_TRANSFORM_COLOR: {
                         let src = a_lo; let dst = u32(v);
                         if (src < 8u && dst < 8u) {
                             let h = get_board_heart(p_idx, src);
                             add_board_heart(p_idx, dst, h);
                         }
                    }

                    case O_ADD_TO_HAND: {
                        let t = a_lo;
                        if (t == 1u) { // From Deck
                            var d_len = 0u;
                            if (p_idx == 0u) { d_len = states[g_gid].player0.deck_len; }
                            else { d_len = states[g_gid].player1.deck_len; }
                            if (d_len > 0u) {
                                let cid = get_deck_card(p_idx, d_len - 1u);
                                add_to_hand(p_idx, cid);
                                if (p_idx == 0u) { states[g_gid].player0.deck_len -= 1u; }
                                else { states[g_gid].player1.deck_len -= 1u; }
                            }
                        }
                    }
                    case O_SELECT_MEMBER, O_SELECT_LIVE, O_SELECT_PLAYER, O_SELECT_CARDS: {
                         if (ctx_choice >= 0) {
                             // Map choice to prev_card_id so conditions can check it
                             if (real_op == O_SELECT_MEMBER) {
                                 let s_cid = get_stage_card(p_idx, u32(ctx_choice));
                                 states[g_gid].prev_card_id = i32(s_cid);
                             }
                         }
                    }
                    case O_SWAP_AREA: {
                        let sa_src = resolve_target_slot(target_slot, slot_idx);
                        let sa_dst = a_lo;
                        if (sa_src < 3u && sa_dst < 3u && sa_src != sa_dst) {
                            let sa_src_cid = get_stage_card(p_idx, sa_src);
                            let sa_dst_cid = get_stage_card(p_idx, sa_dst);
                            let sa_s_word = sa_src / 2u; let sa_s_shift = (sa_src % 2u) * 16u;
                            let sa_d_word = sa_dst / 2u; let sa_d_shift = (sa_dst % 2u) * 16u;
                            if (p_idx == 0u) {
                                set_stage_card(0u, sa_src, sa_dst_cid);
                                set_stage_card(0u, sa_dst, sa_src_cid);
                            } else {
                                set_stage_card(1u, sa_src, sa_dst_cid);
                                set_stage_card(1u, sa_dst, sa_src_cid);
                            }
                            set_moved(p_idx, sa_src);
                            set_moved(p_idx, sa_dst);
                        }
                    }
                     case O_SWAP_ZONE: {
                         let success_idx = u32(ctx_choice);
                         let hand_idx = 0u; 
                         var sz_h_len = 0u; var sz_s_len = 0u;
                         if (p_idx == 0u) { sz_h_len = states[g_gid].player0.hand_len; sz_s_len = states[g_gid].player0.lives_cleared_count; }
                         else { sz_h_len = states[g_gid].player1.hand_len; sz_s_len = states[g_gid].player1.lives_cleared_count; }
                         
                         if (success_idx < sz_s_len && sz_h_len > 0u) {
                             let scid = get_success_card(p_idx, success_idx);
                             let hcid = get_hand_card(p_idx, hand_idx);
                             remove_from_hand(p_idx, hand_idx);
                             add_to_hand(p_idx, scid);
                             let word_idx = success_idx / 2u;
                             let shift = (success_idx % 2u) * 16u;
                             if (p_idx == 0u) {
                                 states[g_gid].player0.success_lives[word_idx] = (states[g_gid].player0.success_lives[word_idx] & ~(0xFFFFu << shift)) | (hcid << shift);
                             } else {
                                 states[g_gid].player1.success_lives[word_idx] = (states[g_gid].player1.success_lives[word_idx] & ~(0xFFFFu << shift)) | (hcid << shift);
                             }
                         }
                    }

                    case O_META_RULE: {
                        // v = flag state (1=on, 0=off, etc.)
                        // a_lo = rule type
                        if (a_lo == 8u) { // SCORE_RULE
                            if (v == 1i) { // 1 = ALL_ENERGY_ACTIVE
                                var e_count = 0u; var t_count = 0u;
                                if (p_idx == 0u) {
                                    e_count = states[g_gid].player0.energy_count;
                                    t_count = states[g_gid].player0.tapped_energy_count;
                                } else {
                                    e_count = states[g_gid].player1.energy_count;
                                    t_count = states[g_gid].player1.tapped_energy_count;
                                }
                                cond = (t_count == 0u && e_count > 0u);
                            } else {
                                // Default/unhandled score rule types
                                cond = false;
                            }
                        }
                    }
                    // === MISSING OPCODES FOR PARITY ===
                    case O_LOOK_DECK_DYNAMIC: {
                        // Look at cards from deck equal to live score + v
                        // Used by cards like PL!-bp5-001-AR: "look at cards equal to live score + 2"
                        let base_score = select(states[g_gid].player0.score, states[g_gid].player1.score, p_idx == 0u);
                        // Note: live_score_bonus not in GPU state, using score only
                        let count = base_score + u32(v);
                        // For GPU, we just draw the cards (simplified - no looked_cards pile)
                        for (var d = 0u; d < count; d = d + 1u) {
                            var ldd_d_len = 0u;
                            if (p_idx == 0u) { ldd_d_len = states[g_gid].player0.deck_len; }
                            else { ldd_d_len = states[g_gid].player1.deck_len; }
                            if (ldd_d_len == 0u) { break; }
                            // In GPU, we don't track looked_cards - just skip
                            if (p_idx == 0u) { states[g_gid].player0.deck_len -= 1u; }
                            else { states[g_gid].player1.deck_len -= 1u; }
                        }
                    }
                    case O_REDUCE_SCORE: {
                        // Reduce live score bonus by v
                        // Note: GPU uses score directly (no live_score_bonus field)
                        let reduction = min(u32(v), select(states[g_gid].player0.score, states[g_gid].player1.score, p_idx == 0u));
                        if (p_idx == 0u) { states[g_gid].player0.score -= reduction; }
                        else { states[g_gid].player1.score -= reduction; }
                    }
                    case O_REPEAT_ABILITY: {
                        // Repeat the current ability from the beginning
                        // v = max repeat count (0 = infinite, N = repeat N more times)
                        // In GPU compute shader, we reset ip to pool_ip (start of ability bytecode)
                        // Note: This requires a repeat_count variable in the ability execution scope
                        // For simplicity in GPU model, we use a static repeat limit check
                        // Real implementation would need loop state tracking
                        let max_repeats = u32(v);
                        if (max_repeats == 0u) {
                            // Infinite repeat - jump back to start (pool_ip)
                            ip = pool_ip;
                        } else if (max_repeats > 0u) {
                            // Limited repeat - for GPU simplicity, just jump back once
                            // Full implementation would track repeat_count in function scope
                            ip = pool_ip;
                        }
                    }
                    case O_LOSE_EXCESS_HEARTS: {
                        // Lose excess hearts beyond what's required for the live
                        // v = number of excess hearts to lose (0 = lose all excess)
                        // Placeholder - actual implementation would compare current vs required hearts
                        // For now, this is a no-op in GPU as it requires complex heart board state
                    }
                    case O_SKIP_ACTIVATE_PHASE: {
                        // Skip the next activate phase
                        // Used by cards that prevent member activation
                        // Store in flags (bit 31 = skip_next_activate)
                        if (p_idx == 0u) { states[g_gid].player0.flags |= 0x80000000u; }
                        else { states[g_gid].player1.flags |= 0x80000000u; }
                    }
                    case O_PAY_ENERGY_DYNAMIC: {
                        // Pay energy equal to card score + v
                        let base_score = select(states[g_gid].player0.score, states[g_gid].player1.score, p_idx == 0u);
                        let total_cost = base_score + u32(v);
                        var ped_energy = 0u; var ped_tapped = 0u;
                        if (p_idx == 0u) { ped_energy = states[g_gid].player0.energy_count; ped_tapped = states[g_gid].player0.tapped_energy_count; }
                        else { ped_energy = states[g_gid].player1.energy_count; ped_tapped = states[g_gid].player1.tapped_energy_count; }
                        let available = ped_energy - ped_tapped;
                        if (available >= total_cost) {
                            if (p_idx == 0u) { states[g_gid].player0.tapped_energy_count += total_cost; }
                            else { states[g_gid].player1.tapped_energy_count += total_cost; }
                        }
                    }
                    case O_PLACE_ENERGY_UNDER_MEMBER: {
                        // Place energy card under a member
                        // Used by cards that attach energy to members for special effects
                        // s parameter contains the slot index
                        let slot = u32(s) & 0xFFu;
                        if (slot < 3u) {
                            var pem_energy = 0u; var pem_tapped = 0u;
                            if (p_idx == 0u) { pem_energy = states[g_gid].player0.energy_count; pem_tapped = states[g_gid].player0.tapped_energy_count; }
                            else { pem_energy = states[g_gid].player1.energy_count; pem_tapped = states[g_gid].player1.tapped_energy_count; }
                            let available = pem_energy - pem_tapped;
                            if (available > 0u) {
                                // Find an untapped energy to move (simplified - just increment stage_energy_count)
                                // In GPU, we track count via stage_energy arrays
                                if (p_idx == 0u) { 
                                    states[g_gid].player0.tapped_energy_count += 1u;
                                    // stage_energy[slot] would need proper implementation
                                } else { 
                                    states[g_gid].player1.tapped_energy_count += 1u;
                                }
                            }
                        }
                    }
                    default: {}
                }
            }
        }
        pool_ip = pool_ip + ab_len;
    }
}

fn select_random_legal_action(p_idx: u32) -> u32 {
    var chosen_action = 0u;
    var legal_count = 1u;
    var e_count = 0u; var t_count = 0u; var b_limit = 0u; var b_count = 0u; var h_len = 0u;
    if (p_idx == 0u) {
        e_count = states[g_gid].player0.energy_count;
        t_count = states[g_gid].player0.tapped_energy_count;
        b_limit = states[g_gid].player0.baton_touch_limit;
        b_count = states[g_gid].player0.baton_touch_count;
        h_len = states[g_gid].player0.hand_len;
    } else {
        e_count = states[g_gid].player1.energy_count;
        t_count = states[g_gid].player1.tapped_energy_count;
        b_limit = states[g_gid].player1.baton_touch_limit;
        b_count = states[g_gid].player1.baton_touch_count;
        h_len = states[g_gid].player1.hand_len;
    }
    let avail_energy = e_count - t_count;
    let hand_len = h_len;
    let phase = states[g_gid].phase;

    if (phase == PHASE_LIVESET) {
        for (var h = 0u; h < 32u; h = h + 1u) {
            if (h >= hand_len) { break; }
            let cid = get_hand_card(p_idx, h);
            if (cid > 0u && cid < arrayLength(&card_stats)) {
                let stats = card_stats[cid];
                if (stats.card_type == 1u) {
                    var live_count = 0u;
                    for (var s = 0u; s < 3u; s = s + 1u) { if (get_live_card(p_idx, s) > 0u) { live_count += 1u; } }
                    if (live_count < 3u) {
                        let action = ACTION_BASE_LIVESET + h;
                        legal_count = legal_count + 1u;
                        if ((rng_jump() % legal_count) == 0u) { chosen_action = action; }
                    }
                }
            }
        }
        return chosen_action;
    }

    if (phase == PHASE_MAIN) {
        for (var h = 0u; h < 32u; h = h + 1u) {
            if (h >= hand_len) { break; }
            let cid = get_hand_card(p_idx, h);
            if (cid == 0u || cid >= arrayLength(&card_stats)) { continue; }
            let stats = card_stats[cid];
            if (stats.card_type != 1u) { continue; }

            for (var slot = 0u; slot < 3u; slot = slot + 1u) {
                if (is_moved(p_idx, slot)) { continue; }
                var cost = stats.cost;
                let reduction = select(states[g_gid].player1.cost_reduction, states[g_gid].player0.cost_reduction, p_idx == 0u);
                if (i32(cost) > reduction) { cost = u32(i32(cost) - reduction); } else { cost = 0u; }
                
                let existing_cid = get_stage_card(p_idx, slot);
                if (existing_cid > 0u) {
                    if (b_count >= b_limit) { continue; }
                    let ext_cost = card_stats[existing_cid].cost;
                    if (ext_cost <= cost) { cost -= ext_cost; } else { cost = 0u; }
                }
                if (cost <= avail_energy) {
                    let action = ACTION_BASE_HAND + h * 3u + slot;
                    legal_count = legal_count + 1u;
                    if ((rng_jump() % legal_count) == 0u) { chosen_action = action; }
                }
            }
        }
    }
    
    // PHASE_RESPONSE: Handle interaction choices (LOOK_AND_CHOOSE, SELECT_DISCARD, etc.)
    // Action 0 = Skip/Pass, Action 1+ = Select option
    if (phase == PHASE_RESPONSE) {
        // For interactions, we can either skip (action 0) or select an option (action 1+)
        // Default to selecting the first available option (action 1) for deterministic testing
        // This matches the CPU behavior in semantic tests
        legal_count = legal_count + 1u;
        if ((rng_jump() % legal_count) == 0u) { chosen_action = 1u; }  // Select first option
        legal_count = legal_count + 1u;
        if ((rng_jump() % legal_count) == 0u) { chosen_action = 0u; }  // Skip option
    }
    
    return chosen_action;
}

fn step_state(action: u32) -> u32 {
    let p_idx = states[g_gid].current_player;
    let phase = states[g_gid].phase;

    if (phase == PHASE_TERMINAL) { return 0u; } 
    if (phase == PHASE_RPS) { states[g_gid].phase = PHASE_TURN_CHOICE; return 1u; }
    if (phase == PHASE_TURN_CHOICE) {
        // Determine first player based on RPS result or random
        // In LL!SIC, winner of RPS chooses who goes first
        // For GPU, we use first_player flag which was set during RPS
        states[g_gid].phase = PHASE_ACTIVE;
        states[g_gid].current_player = states[g_gid].first_player;
        return 1u;
    }
    if (phase == PHASE_ACTIVE) {
        // Active phase: determine active player for the turn
        // Auto-advance to Energy phase
        states[g_gid].phase = PHASE_ENERGY;
        return 1u;
    }
    if (phase == PHASE_ENERGY) { draw_energy(p_idx); states[g_gid].phase = PHASE_DRAW; return 1u; }
    if (phase == PHASE_DRAW) { draw_card(p_idx); states[g_gid].phase = PHASE_MAIN; return 1u; }
    if (phase == PHASE_LIVESET) {
        if (action == 0u) {
            var draws = 0u;
            if (p_idx == 0u) {
                draws = states[g_gid].player0.pending_draws;
                states[g_gid].player0.pending_draws = 0u;
            } else {
                draws = states[g_gid].player1.pending_draws;
                states[g_gid].player1.pending_draws = 0u;
            }
            if (draws > 0u) { draw_card(p_idx); }
            if (draws > 1u) { draw_card(p_idx); }
            if (draws > 2u) { draw_card(p_idx); }
            let first_p = states[g_gid].first_player;
            if (p_idx == first_p) { states[g_gid].current_player = 1u - first_p; }
            else { states[g_gid].phase = 6; states[g_gid].current_player = first_p; }
            return 1u;
        } else if (action >= 400u && action < 500u) {
            let hand_idx = action - 400u;
            let card_id = get_hand_card(p_idx, hand_idx);
            if (card_id > 0u) {
                var found = false;
                for (var s = 0u; s < 3u; s = s + 1u) {
                    if (get_live_card(p_idx, s) == 0u) {
                        let word_idx = s / 2u;
                        let shift = (s % 2u) * 16u;
                        if (p_idx == 0u) {
                            states[g_gid].player0.live_zone[word_idx] |= (card_id << shift);
                        } else {
                            states[g_gid].player1.live_zone[word_idx] |= (card_id << shift);
                        }
                        found = true; break;
                    }
                }
                if (found) {
                    remove_from_hand(p_idx, hand_idx);
                    if (p_idx == 0u) { states[g_gid].player0.pending_draws += 1u; }
                    else { states[g_gid].player1.pending_draws += 1u; }
                }
            }
            return 1u;
        }
    }
    if (phase == PHASE_PERFORMANCE_P1) { states[g_gid].phase = PHASE_PERFORMANCE_P2; states[g_gid].current_player = 1u - states[g_gid].first_player; return 1u; }
    if (phase == PHASE_PERFORMANCE_P2) {
        resolve_performance_gpu();
        states[g_gid].phase = PHASE_LIVE_RESULT;
        states[g_gid].current_player = states[g_gid].first_player;
        return 1u;
    }
    if (phase == PHASE_LIVE_RESULT) {
        let p0_lives = states[g_gid].player0.lives_cleared_count;
        let p1_lives = states[g_gid].player1.lives_cleared_count;
        
        if (p0_lives >= 3u || p1_lives >= 3u) {
            states[g_gid].phase = PHASE_TERMINAL;
            if (p0_lives >= 3u && p1_lives < 3u) { states[g_gid].winner = 0; }
            else if (p1_lives >= 3u && p0_lives < 3u) { states[g_gid].winner = 1; }
            else { states[g_gid].winner = -1; } // Draw
            return 1u;
        }
        
        states[g_gid].turn += 1u;
        // In LL!SIC, first player only flips if a live card was cleared. 
        // For now, we use a simplified check: did score increase? 
        if (states[g_gid].player0.score > 0u || states[g_gid].player1.score > 0u) {
            states[g_gid].first_player = 1u - states[g_gid].first_player;
        }
        
        states[g_gid].current_player = states[g_gid].first_player;
        states[g_gid].phase = PHASE_RPS;
        states[g_gid].player0.live_zone[0] = 0u; states[g_gid].player0.live_zone[1] = 0u;
        states[g_gid].player1.live_zone[0] = 0u; states[g_gid].player1.live_zone[1] = 0u;
        recalculate_board_stats(states[g_gid].current_player);
        return 1u;
    }

    if (phase == PHASE_MAIN) {
        if (action == 0u) { end_main_phase(); recalculate_board_stats(states[g_gid].current_player); return 1u; }
        var hand_idx = 99u; var slot_idx = 99u; var choice = -1i; var trigger = 0i;
        if (action >= ACTION_BASE_HAND && action < ACTION_BASE_HAND_CHOICE) {
            let adj = action - ACTION_BASE_HAND; hand_idx = adj / 3u;
            slot_idx = adj % 3u; trigger = 1i;
        }
        else if (action >= ACTION_BASE_HAND_CHOICE && action < ACTION_BASE_HAND_SELECT) {
            let adj = action - ACTION_BASE_HAND_CHOICE; hand_idx = adj / 100u;
            let rem = adj % 100u; slot_idx = rem / 10u; choice = i32(rem % 10u); trigger = 1i;
        }
        if (trigger == 1i) {
            let card_id = get_hand_card(p_idx, hand_idx); let stats = card_stats[card_id];
            var cost = stats.cost;
            let reduction = select(states[g_gid].player1.cost_reduction, states[g_gid].player0.cost_reduction, p_idx == 0u);
            if (i32(cost) > reduction) { cost = u32(i32(cost) - reduction); } else { cost = 0u; }
            
            let existing_cid = get_stage_card(p_idx, slot_idx);
            if (existing_cid > 0u) {
                var b_count = 0u; var b_limit = 0u;
                if (p_idx == 0u) {
                    b_count = states[g_gid].player0.baton_touch_count;
                    b_limit = states[g_gid].player0.baton_touch_limit;
                } else {
                    b_count = states[g_gid].player1.baton_touch_count;
                    b_limit = states[g_gid].player1.baton_touch_limit;
                }
                if (b_count >= b_limit) { return 0u; }
                let ext_cost = card_stats[existing_cid].cost;
                if (ext_cost <= cost) { cost -= ext_cost; } else { cost = 0u; }
                add_to_discard(p_idx, existing_cid);
                if (p_idx == 0u) { states[g_gid].player0.baton_touch_count += 1u; }
                else { states[g_gid].player1.baton_touch_count += 1u; }
            }

            var p_energy = 0u; var p_tapped = 0u;
            if (p_idx == 0u) {
                p_energy = states[g_gid].player0.energy_count;
                p_tapped = states[g_gid].player0.tapped_energy_count;
            } else {
                p_energy = states[g_gid].player1.energy_count;
                p_tapped = states[g_gid].player1.tapped_energy_count;
            }
            let avail_energy = p_energy - p_tapped;
            if (cost <= avail_energy) {
                if (p_idx == 0u) { states[g_gid].player0.tapped_energy_count += cost; }
                else { states[g_gid].player1.tapped_energy_count += cost; }
                
                remove_from_hand(p_idx, hand_idx);
                if (stats.card_type == 1u) {
                    let word_idx = slot_idx / 2u; let shift = (slot_idx % 2u) * 16u;
                    if (p_idx == 0u) {
                        set_stage_card(p_idx, slot_idx, card_id);
                        set_moved(p_idx, slot_idx);
                    } else {
                        set_stage_card(p_idx, slot_idx, card_id);
                        set_moved(p_idx, slot_idx);
                    }
                    if (stats.bytecode_len > 0u) { push_trigger(card_id, slot_idx, 1i, -1i, choice); }
                } else {
                    if (stats.bytecode_len > 0u) { push_trigger(card_id, 99u, 1i, -1i, choice); }
                    add_to_discard(p_idx, card_id);
                }
                process_trigger_queue(p_idx);
                recalculate_board_stats(p_idx); return 1u;
            } else { return 0u; }
        }
        if (action >= ACTION_BASE_STAGE && action < ACTION_BASE_STAGE_CHOICE) {
            let adj = action - ACTION_BASE_STAGE; let s_idx = adj / 100u; let ab_rem = adj % 100u;
            let ab_idx = i32(ab_rem / 10u); let c = i32(ab_rem % 10u);
            let card_id = get_stage_card(p_idx, s_idx); let stats = card_stats[card_id];
            if (stats.bytecode_len > 0u) { push_trigger(card_id, s_idx, 2i, ab_idx, c); }
            process_trigger_queue(p_idx);
            recalculate_board_stats(p_idx); return 1u;
        }
        if (action >= ACTION_BASE_HAND_SELECT && action < ACTION_BASE_HAND_SELECT + 1000u) {
        }
        if (action >= ACTION_BASE_DISCARD_ACTIVATE && action < ACTION_BASE_DISCARD_ACTIVATE + 1000u) {
            let adj = action - ACTION_BASE_DISCARD_ACTIVATE; let disc_idx = adj / 10u; let ab_idx = i32(adj % 10u);
            let card_id = get_discard_card(p_idx, disc_idx);
            if (card_id > 0u && card_id < arrayLength(&card_stats)) {
                let stats = card_stats[card_id];
                if (stats.bytecode_len > 0u) { push_trigger(card_id, 99u, 2i, ab_idx, -1i); }
            }
            process_trigger_queue(p_idx);
            recalculate_board_stats(p_idx); return 1u;
        }
        // ACTION_BASE_TRIGGER: Format = 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
        // This allows testing any trigger type with proper trigger_filter
        if (action >= ACTION_BASE_TRIGGER && action < ACTION_BASE_TRIGGER + 10000u) {
            let adj = action - ACTION_BASE_TRIGGER;
            let s_idx = adj / 1000u;
            let rem1 = adj % 1000u;
            let trigger_type = i32(rem1 / 100u);
            let rem2 = rem1 % 100u;
            let ab_idx = i32(rem2 / 10u);
            let c = i32(rem2 % 10u);
            let card_id = get_stage_card(p_idx, s_idx);
            if (card_id > 0u && card_id < arrayLength(&card_stats)) {
                let stats = card_stats[card_id];
                if (stats.bytecode_len > 0u) { push_trigger(card_id, s_idx, trigger_type, ab_idx, c); }
            }
            process_trigger_queue(p_idx);
            recalculate_board_stats(p_idx); return 1u;
        }
    }
    return 3u;
}

fn process_trigger_queue(p_idx: u32) {
    while (states[g_gid].queue_head < states[g_gid].queue_tail) {
        let head = states[g_gid].queue_head;
        let req = states[g_gid].trigger_queue[head];
        states[g_gid].queue_head = head + 1u;
        
        let req_card_id = req.card_id;
        if (req_card_id < arrayLength(&card_stats)) {
            let req_stats = card_stats[req_card_id];
            resolve_bytecode(p_idx, req_card_id, req.slot_idx, req.trigger_filter, req.ab_filter, req_stats.bytecode_start, req_stats.bytecode_len, req.choice);
        }
    }
    // Reset queue for next activity
    states[g_gid].queue_head = 0u;
    states[g_gid].queue_tail = 0u;
}
