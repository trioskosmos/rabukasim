struct GpuPlayerState {
    heart_buffs: array<u32, 8>,
    heart_req_reductions: array<u32, 2>,
    deck: array<u32, 32>,
    hand: array<u32, 32>,
    discard_pile: array<u32, 32>,
    stage: array<u32, 2>,
    live_zone: array<u32, 2>,
    score: u32,
    flags: u32,
    hand_added_mask: u32,
    hand_len: u32,
    deck_len: u32,
    discard_pile_len: u32,
    current_turn_volume: u32,
    baton_touch_count: u32,
    energy_count: u32,
    pending_draws: u32,
    tapped_energy_count: u32,
    used_abilities_mask: u32,
    board_blades: u32,
    lives_cleared_count: u32,
    avg_hearts: array<u32, 7>,
    mcts_reward: f32,
    baton_touch_limit: u32,
    moved_flags: u32,
    energy_deck_len: u32,
    _pad_inner: u32,
}

struct GpuGameState {
    players: array<GpuPlayerState, 2>,
    current_player: u32,
    phase: i32,
    turn: u32,
    active_count: u32,
    winner: i32,
    prev_card_id: i32,
    forced_action: i32,
    is_debug: u32,
    rng_state_lo: u32,
    rng_state_hi: u32,
    first_player: u32,
}

struct GpuCardStats {
    ability_flags_lo: u32,
    ability_flags_hi: u32,
    cost: u32,
    blades: u32,
    card_type: u32,
    bytecode_start: u32,
    bytecode_len: u32,
    volume_icons: u32,
    extra_val: u32,
    hearts_lo: u32,
    hearts_hi: u32,
    blade_hearts_lo: u32,
    blade_hearts_hi: u32,
    groups: u32,
    units: u32,
    char_id: u32,
    synergy_flags: u32,
    _pad_card: u32,
}

@group(0) @binding(0) var<storage, read_write> states: array<GpuGameState>;
@group(0) @binding(1) var<storage, read> card_stats: array<GpuCardStats>;
@group(0) @binding(2) var<storage, read> bytecode: array<i32>;

var<private> local_state: GpuGameState;
var<private> g_board_hearts: array<array<u32, 8>, 2>;
var<private> g_rng: vec2<u32>;
var<private> g_gid: u32;

// --- OPCODES (Core) ---
const O_RETURN: i32 = 1;
const O_JUMP: i32 = 2;
const O_JUMP_F: i32 = 3;
const O_DRAW: i32 = 10;
const O_HEARTS: i32 = 12;
const O_REDUCE_COST: i32 = 13;
const O_BOOST: i32 = 16;
const O_CHARGE: i32 = 23;
const O_SELECT_MODE: i32 = 30;
const O_LOOK_AND_CHOOSE: i32 = 41;
const O_ACTIVATE_ENERGY: i32 = 81;

// --- Helper Functions ---

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

fn get_hand_card(p_idx: u32, h_idx: u32) -> u32 {
    let word_idx = h_idx / 2u;
    let shift = (h_idx % 2u) * 16u;
    var word = 0u;
    if (p_idx == 0u) {
        word = local_state.players[0].hand[word_idx];
    } else {
        word = local_state.players[1].hand[word_idx];
    }
    return (word >> shift) & 0xFFFFu;
}

fn get_discard_card(p_idx: u32, idx: u32) -> u32 {
    if (idx >= local_state.players[p_idx].discard_pile_len) { return 0u; }
    let word_idx = idx / 2u;
    let shift = (idx % 2u) * 16u;
    var word = 0u;
    if (p_idx == 0u) {
        word = local_state.players[0].discard_pile[word_idx];
    } else {
        word = local_state.players[1].discard_pile[word_idx];
    }
    return (word >> shift) & 0xFFFFu;
}

fn get_live_card(p_idx: u32, slot: u32) -> u32 {
    let word_idx = slot / 2u;
    let shift = (slot % 2u) * 16u;
    return (local_state.players[p_idx].live_zone[word_idx] >> shift) & 0xFFFFu;
}

fn remove_from_hand(p_idx: u32, hand_idx: u32) {
    let p_hand_len = local_state.players[p_idx].hand_len;
    if (p_hand_len == 0u || hand_idx >= p_hand_len) { return; }
    for (var i = hand_idx; i < 63u; i = i + 1u) {
        if (i >= p_hand_len - 1u) { break; }
        let next_card = get_hand_card(p_idx, i + 1u);
        let t_shift = (i % 2u) * 16u;
        local_state.players[p_idx].hand[i / 2u] = (local_state.players[p_idx].hand[i / 2u] & ~(0xFFFFu << t_shift)) | (next_card << t_shift);
    }
    let last_idx = p_hand_len - 1u;
    local_state.players[p_idx].hand[last_idx / 2u] &= ~(0xFFFFu << ((last_idx % 2u) * 16u));
    local_state.players[p_idx].hand_len -= 1u;
}

fn get_stage_card(p_idx: u32, s_idx: u32) -> u32 {
    let word_idx = s_idx / 2u;
    let shift = (s_idx % 2u) * 16u;
    return (local_state.players[p_idx].stage[word_idx] >> shift) & 0xFFFFu;
}

fn get_deck_card(p_idx: u32, d_idx: u32) -> u32 {
    let word_idx = d_idx / 2u;
    let shift = (d_idx % 2u) * 16u;
    return (local_state.players[p_idx].deck[word_idx] >> shift) & 0xFFFFu;
}

fn is_moved(p_idx: u32, slot: u32) -> bool {
    return (local_state.players[p_idx].moved_flags & (1u << slot)) != 0u;
}

fn add_to_discard(p_idx: u32, card_id: u32) {
    if (card_id == 0u) { return; }
    let disc_len = local_state.players[p_idx].discard_pile_len;
    if (disc_len < 32u) {
        local_state.players[p_idx].discard_pile[disc_len] = card_id;
        local_state.players[p_idx].discard_pile_len = disc_len + 1u;
    }
}

fn add_to_hand(p_idx: u32, card_id: u32) {
    let h_idx = local_state.players[p_idx].hand_len;
    if (h_idx >= 32u) { return; }
    let word_idx = h_idx / 2u;
    let shift = (h_idx % 2u) * 16u;
    local_state.players[p_idx].hand[word_idx] = (local_state.players[p_idx].hand[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
    local_state.players[p_idx].hand_len += 1u;
}

fn draw_card(p_idx: u32) {
    let d_len = local_state.players[p_idx].deck_len;
    if (d_len == 0u) { return; }
    let card_id = get_deck_card(p_idx, d_len - 1u);
    local_state.players[p_idx].deck_len -= 1u;
    add_to_hand(p_idx, card_id);
}

fn draw_energy(p_idx: u32) {
    if (local_state.players[p_idx].energy_deck_len > 0u) {
        local_state.players[p_idx].energy_deck_len -= 1u;
        local_state.players[p_idx].energy_count += 1u;
    }
}

fn end_main_phase() {
    let p_idx = local_state.current_player;
    let first_p = local_state.first_player;
    if (p_idx == first_p) {
        // CPU: Main → Active (opponent's turn starts)
        let other_p = 1u - first_p;
        local_state.current_player = other_p;
        local_state.phase = 1; // Active (will auto-advance to Energy → Draw → Main)
    } else {
        // Both players finished their turns → LiveSet
        local_state.phase = 5; // LiveSet
        local_state.current_player = first_p;
    }
}

fn recalculate_board_stats(p_idx: u32) {
    var total_hearts: array<u32, 8>;
    total_hearts[0] = 0u; total_hearts[1] = 0u; total_hearts[2] = 0u; total_hearts[3] = 0u;
    total_hearts[4] = 0u; total_hearts[5] = 0u; total_hearts[6] = 0u; total_hearts[7] = 0u;
    var total_blades = 0u;
    for (var s = 0u; s < 3u; s++) {
        let cid = get_stage_card(p_idx, s);
        if (cid > 0u && cid < arrayLength(&card_stats)) {
            let stats = card_stats[cid];
            let h_lo = stats.hearts_lo; let h_hi = stats.hearts_hi;
            total_hearts[0] += (h_lo >> 0u) & 0xFFu; total_hearts[1] += (h_lo >> 8u) & 0xFFu; total_hearts[2] += (h_lo >> 16u) & 0xFFu; total_hearts[3] += (h_lo >> 24u) & 0xFFu;
            total_hearts[4] += (h_hi >> 0u) & 0xFFu; total_hearts[5] += (h_hi >> 8u) & 0xFFu; total_hearts[6] += (h_hi >> 16u) & 0xFFu;
            total_blades += stats.blades;
        }
    }
    for (var i = 0u; i < 8u; i++) { g_board_hearts[p_idx][i] = total_hearts[i]; }
    local_state.players[p_idx].board_blades = total_blades;
}

fn match_filter(cid: u32, attr: u32) -> bool {
    if (cid == 0u || cid >= arrayLength(&card_stats)) { return false; }
    let s = card_stats[cid];

    // Group Filter (attr >> 5 & 0x7F)
    if ((attr & 0x10u) != 0u) {
        let gid = (attr >> 5u) & 0x7Fu;
        let g = s.groups;
        if (((g >> 0u) & 0xFFu) != gid && ((g >> 8u) & 0xFFu) != gid && 
            ((g >> 16u) & 0xFFu) != gid && ((g >> 24u) & 0xFFu) != gid) { return false; }
    }

    // Type Filter (attr >> 2 & 0x03)
    let tf = (attr >> 2u) & 0x03u;
    if (tf == 1u && s.card_type != 1u) { return false; }
    if (tf == 2u && s.card_type != 2u) { return false; } // Assuming 2=Live, though GPU stats use 0=Spell/Event

    // NOTE: Color/Unit filters skipped due to 32-bit attr limitation in shader bytecode
    return true;
}

fn check_condition_opcode(p_idx: u32, op: i32, v: i32, a: u32, target_slot: u32) -> bool {
    switch (op) {
        case 200: { return local_state.turn == 1u; }
        case 201: { // C_HAS_MEMBER
            var count = 0u;
            for (var s = 0u; s < 3u; s = s + 1u) {
                let cid = get_stage_card(p_idx, s);
                // IF 'v' matches strict ID, check it. OR if filter matches.
                // NOTE: WGSL condition matching logic:
                // If val > 0, we treat it as strict ID match (or threshold?)
                // Rust: (id == val || id == (attr as i32)) || (filter_attr != 0 && matches...)
                // Here we simplify: If a != 0, use filter. Else use val as ID.
                var m = false;
                if (a != 0u) { m = match_filter(cid, a); }
                else if (cid == u32(v)) { m = true; }
                
                if (m) { count = count + 1u; }
            }
            // Rust C_HAS_MEMBER returns true if count >= 1. Wait, Rust is .any().
            // So if count >= 1, we are good.
            return count > 0u;
        }
        case 203: { // C_COUNT_STAGE
             var count = 0u;
             for (var s = 0u; s < 3u; s = s + 1u) {
                 let cid = get_stage_card(p_idx, s);
                 if (match_filter(cid, a)) { count = count + 1u; }
             }
             return count >= u32(v);
        }
        case 204: { return local_state.players[p_idx].hand_len >= u32(v); }
        case 202: { // C_CLR
            let color_idx = a;
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
        case 206: { return target_slot == 1u; }
        case 207: { // C_LLD (Life Lead)
            let o_idx = 1u - p_idx;
            // FIX: Check lives_cleared_count, not score
            let my_lives = i32(local_state.players[p_idx].lives_cleared_count);
            let opp_lives = i32(local_state.players[o_idx].lives_cleared_count);
            return (my_lives - opp_lives) >= v;
        }
        case 208: { // C_GRP
            // Implemented via match_filter logic? Or raw Check
            // Rust C_GRP checks if stage count >= val
            var count = 0u;
            // Construct attr for Group check: bit 4 (0x10) + GroupID << 5
            let filter = 0x10u | ((a & 0x7Fu) << 5u);
            for (var s = 0u; s < 3u; s = s + 1u) {
                let cid = get_stage_card(p_idx, s);
                if (match_filter(cid, filter)) { count = count + 1u; }
            }
            return count >= u32(v);
        }
        case 211: { // C_SLF_GRP
            var cid = 0u;
            if (target_slot < 3u) { cid = get_stage_card(p_idx, target_slot); }
            let filter = 0x10u | ((a & 0x7Fu) << 5u);
            return match_filter(cid, filter);
        }
        case 213: { // C_ENR (Count Energy)
            return local_state.players[p_idx].energy_count >= u32(v);
        }
        case 215: { // C_COST_CHK (Cost Check)
             // FIX: Check card Cost, not Energy
             // Problem: We need context card. Shader check_condition signature lacks 'ctx'.
             // We use 'target_slot' as proxy.
             if (target_slot < 3u) {
                 let cid = get_stage_card(p_idx, target_slot);
                 if (cid > 0u && cid < arrayLength(&card_stats)) {
                     return i32(card_stats[cid].cost) >= v;
                 }
             }
             return false;
        }
        case 220: { // C_CMP
            var my_val = i32(local_state.players[p_idx].score);
            var opp_val = i32(local_state.players[1u - p_idx].score);
            let comp_op = (target_slot >> 4u) & 0x0Fu;
            switch (comp_op) {
                case 0u: { return my_val >= opp_val; }
                case 1u: { return my_val <= opp_val; }
                case 2u: { return my_val > opp_val; } 
                case 3u: { return my_val < opp_val; } 
                case 4u: { return my_val == opp_val; }
                default: { return my_val > opp_val; }
            }
        }
        case 223: { // C_HRT
            var total = 0u;
            for (var j = 0u; j < 7u; j = j + 1u) { total += g_board_hearts[p_idx][j]; }
            return total >= u32(v);
        }
        case 224: { return local_state.players[p_idx].board_blades >= u32(v); }
        case 231: { // C_BATON
            if (local_state.prev_card_id >= 0) {
                let pcid = u32(local_state.prev_card_id);
                if (pcid < arrayLength(&card_stats)) {
                    return card_stats[pcid].char_id == u32(v);
                }
            }
            return local_state.players[p_idx].baton_touch_count >= u32(v);
        }
        default: { return false; }
    }
}

// Select a random legal action (Pure Uniform Random)
fn select_random_legal_action(p_idx: u32) -> u32 {
    var chosen_action = 0u;
    var legal_count = 1u;
    let avail_energy = local_state.players[p_idx].energy_count - local_state.players[p_idx].tapped_energy_count;
    let baton_limit = local_state.players[p_idx].baton_touch_limit;
    let baton_count = local_state.players[p_idx].baton_touch_count;
    let hand_len = local_state.players[p_idx].hand_len;

    for (var h = 0u; h < 60u; h = h + 1u) {
        if (h >= hand_len) { break; }
        let cid = get_hand_card(p_idx, h);
        if (cid == 0u || cid >= arrayLength(&card_stats)) { continue; }
        let stats = card_stats[cid];
        if (stats.card_type != 1u) { continue; }

        for (var slot = 0u; slot < 3u; slot = slot + 1u) {
            if (is_moved(p_idx, slot)) { continue; }
            var cost = stats.cost;
            let existing_cid = get_stage_card(p_idx, slot);
            if (existing_cid > 0u) {
                if (baton_count >= baton_limit) { continue; }
                let ext_cost = card_stats[existing_cid].cost;
                if (ext_cost <= cost) { cost -= ext_cost; } else { cost = 0u; }
            }
            if (cost <= avail_energy) {
                let action = 1u + h * 3u + slot;
                legal_count = legal_count + 1u;
                if ((rng_jump() % legal_count) == 0u) { chosen_action = action; }
            }
        }
    }
    return chosen_action;
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
            if ((local_state.players[p_idx].used_abilities_mask & mask) != 0u) { pool_ip = pool_ip + ab_len; continue; }
            local_state.players[p_idx].used_abilities_mask |= mask;
        }
        var ip = pool_ip;
        let end = pool_ip + ab_len;
        var cond = true;
        var ctx_choice = choice;
        while (ip < end) {
            if (ip + 4u > end) { break; }
            let op = bytecode[ip]; let v = bytecode[ip + 1]; let a = bytecode[ip + 2]; let s_op = bytecode[ip + 3];
            ip = ip + 4;
            if (op <= 0) { continue; }
            if (op == 1) { break; }
            var real_op = op; var is_negated = false;
            if (real_op >= 1000) { real_op = real_op - 1000; is_negated = true; }
            if (real_op >= 200 && real_op <= 299) {
                let passed = check_condition_opcode(p_idx, real_op, v, u32(a), slot_idx);
                cond = passed; if (is_negated) { cond = !cond; }
                continue;
            }
            if (real_op == 2) { ip = u32(i32(ip) + v * 4); continue; }
            if (real_op == 3) { if (!cond) { ip = u32(i32(ip) + v * 4); } continue; }
            if (real_op >= 10 && real_op < 100) {
                switch (real_op) {
                    case 10: { for (var d = 0; d < v; d = d + 1) { draw_card(p_idx); } }
                    case 11: { local_state.players[p_idx].board_blades += u32(v); }
                    case 12: {
                        var color = u32(a);
                        if (color == 0u) { color = u32(ctx_choice); }
                        if (color < 8u) { g_board_hearts[p_idx][color] += u32(v); }
                    }
                    case 13: { local_state.players[p_idx].baton_touch_limit += u32(v); }
                    case 16: { local_state.players[p_idx].score += u32(v); }
                    case 23: { if (local_state.players[p_idx].tapped_energy_count >= u32(v)) { local_state.players[p_idx].tapped_energy_count -= u32(v); } else { local_state.players[p_idx].tapped_energy_count = 0u; } }
                    case 30: { }
                    case 31: {
                        let t = u32(a) & 0xFDu;
                        let count = u32(v);
                        if (t == 6u && ctx_choice != -1i) {
                             let h_idx = u32(ctx_choice);
                             remove_from_hand(p_idx, h_idx);
                        }
                    }
                    case 32: {
                        let o_idx = 1u - p_idx;
                        let target_slot = u32(choice);
                        if (target_slot < 3u) {
                             local_state.players[o_idx].flags |= (1u << (3u + target_slot));
                        }
                    }
                    case 45: { ctx_choice = choice; }
                    default: {}
                }
            }
        }
        pool_ip = pool_ip + ab_len;
    }
}

fn step_state(action: u32) -> u32 {
    let p_idx = local_state.current_player;
    let phase = local_state.phase;

    if (phase == 9) { return 0u; } 
    if (phase == 1) { local_state.phase = 2; return 1u; }
    if (phase == 2) { draw_energy(p_idx); local_state.phase = 3; return 1u; }
    if (phase == 3) { draw_card(p_idx); local_state.phase = 4; return 1u; }
    if (phase == 5) {
        if (action == 0u) {
            var draws = local_state.players[p_idx].pending_draws;
            local_state.players[p_idx].pending_draws = 0u;
            if (draws > 0u) { draw_card(p_idx); }
            if (draws > 1u) { draw_card(p_idx); }
            if (draws > 2u) { draw_card(p_idx); }

            let first_p = local_state.first_player;
            if (p_idx == first_p) {
                local_state.current_player = 1u - first_p;
            } else {
                local_state.phase = 6;
                local_state.current_player = first_p;
            }
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
                        local_state.players[p_idx].live_zone[word_idx] |= (card_id << shift);
                        found = true; break;
                    }
                }
                if (found) {
                    remove_from_hand(p_idx, hand_idx);
                    local_state.players[p_idx].pending_draws += 1u;
                }
            }
            return 1u;
        }
    }
    if (phase == 6) {
        local_state.phase = 7;
        local_state.current_player = 1u - local_state.first_player;
        return 1u;
    }
    if (phase == 7) {
        local_state.phase = 8;
        local_state.current_player = local_state.first_player;
        return 1u;
    }
    if (phase == 8) {
        // LiveResult: Process performance results and advance turn
        // This mirrors CPU's do_live_result which auto-advances to Active
        local_state.turn += 1u;
        local_state.first_player = 1u - local_state.first_player;
        local_state.current_player = local_state.first_player;
        local_state.phase = 1; // Active (will auto-advance to Energy → Draw → Main)
        local_state.players[0].live_zone[0] = 0u;
        local_state.players[0].live_zone[1] = 0u;
        local_state.players[1].live_zone[0] = 0u;
        local_state.players[1].live_zone[1] = 0u;
        recalculate_board_stats(local_state.current_player);
        return 1u;
    }

    if (phase == 4) {
        if (action == 0u) {
            end_main_phase();
            recalculate_board_stats(local_state.current_player);
            return 1u;
        }

        var hand_idx = 99u;
        var slot_idx = 99u;
        var choice = -1i;
        var trigger = 0i;

        if (action >= 1u && action <= 180u) {
            let adj = action - 1u;
            hand_idx = adj / 3u;
            slot_idx = adj % 3u;
            trigger = 1i;
        } else if (action >= 1000u && action < 2000u) {
            let adj = action - 1000u;
            hand_idx = adj / 100u;
            let rem = adj % 100u;
            slot_idx = rem / 10u;
            choice = i32(rem % 10u);
            trigger = 1i;
        }

        if (trigger == 1i) {
            let card_id = get_hand_card(p_idx, hand_idx);
            let stats = card_stats[card_id];
            var cost = stats.cost;
            let existing_cid = get_stage_card(p_idx, slot_idx);
            if (existing_cid > 0u) {
                let baton_limit = local_state.players[p_idx].baton_touch_limit;
                let baton_count = local_state.players[p_idx].baton_touch_count;
                if (baton_count >= baton_limit) { return 0u; }
                let ext_cost = card_stats[existing_cid].cost;
                if (ext_cost <= cost) { cost = cost - existing_cost; } else { cost = 0u; }
                add_to_discard(p_idx, existing_cid);
                local_state.players[p_idx].baton_touch_count += 1u;
            }

            let avail_energy = local_state.players[p_idx].energy_count - local_state.players[p_idx].tapped_energy_count;
            if (cost <= avail_energy) {
                local_state.players[p_idx].tapped_energy_count += cost;
                remove_from_hand(p_idx, hand_idx);
                if (stats.card_type == 1u) {
                    let word_idx = slot_idx / 2u;
                    let shift = (slot_idx % 2u) * 16u;
                    local_state.players[p_idx].stage[word_idx] = (local_state.players[p_idx].stage[word_idx] & ~(0xFFFFu << shift)) | (card_id << shift);
                    local_state.players[p_idx].moved_flags |= (1u << slot_idx);
                    if (stats.bytecode_len > 0u) {
                        resolve_bytecode(p_idx, card_id, slot_idx, 1i, -1i, stats.bytecode_start, stats.bytecode_len, choice);
                    }
                } else {
                    if (stats.bytecode_len > 0u) {
                        resolve_bytecode(p_idx, card_id, 99u, 1i, -1i, stats.bytecode_start, stats.bytecode_len, choice);
                    }
                    add_to_discard(p_idx, card_id);
                }
                recalculate_board_stats(p_idx);
                return 1u;
            } else { return 0u; }
        }

        if (action >= 550u && action < 850u) {
            let adj = action - 550u;
            let s_idx = adj / 100u;
            let ab_rem = adj % 100u;
            let ab_idx = i32(ab_rem / 10u);
            let c = i32(ab_rem % 10u);
            let card_id = get_stage_card(p_idx, s_idx);
            let stats = card_stats[card_id];
            if (stats.bytecode_len > 0u) {
                resolve_bytecode(p_idx, card_id, s_idx, 2i, ab_idx, stats.bytecode_start, stats.bytecode_len, c);
            }
            recalculate_board_stats(p_idx);
            return 1u;
        }

        if (action >= 200u && action < 230u) {
            let adj = action - 200u;
            let s_idx = adj / 10u;
            let ab_idx = i32(adj % 10u);
            let card_id = get_stage_card(p_idx, s_idx);
            let stats = card_stats[card_id];
            if (stats.bytecode_len > 0u) {
                resolve_bytecode(p_idx, card_id, s_idx, 2i, ab_idx, stats.bytecode_start, stats.bytecode_len, -1i);
            }
            recalculate_board_stats(p_idx);
            return 1u;
        }
        
        if (action >= 2000u && action < 3000u) {
            let adj = action - 2000u;
            let discard_idx = adj / 10u;
            let ab_idx = i32(adj % 10u);
            let card_id = get_discard_card(p_idx, discard_idx);
            if (card_id > 0u && card_id < arrayLength(&card_stats)) {
                let stats = card_stats[card_id];
                if (stats.bytecode_len > 0u) {
                    resolve_bytecode(p_idx, card_id, 99u, 2i, ab_idx, stats.bytecode_start, stats.bytecode_len, -1i);
                }
            }
            recalculate_board_stats(p_idx);
            return 1u;
        }
    }

    return 3u;
}
