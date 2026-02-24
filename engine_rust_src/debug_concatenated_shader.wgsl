struct GpuTriggerRequest {
    card_id: u32,
    slot_idx: u32,
    trigger_filter: i32,
    ab_filter: i32,
    choice: i32,
    _pad: array<u32, 3>,
}

struct GpuPlayerState {
    heart_buffs: array<u32, 8>,           // 32
    heart_req_reductions: array<u32, 2>,  // 8
    deck: array<u32, 32>,                 // 128
    hand: array<u32, 32>,                 // 128
    discard_pile: array<u32, 32>,         // 128
    stage: array<u32, 2>,                 // 8
    live_zone: array<u32, 2>,             // 8
    score: u32,                           // 4
    flags: u32,                           // 4
    hand_added_mask: u32,                 // 4
    hand_len: u32,                        // 4
    deck_len: u32,                        // 4
    discard_pile_len: u32,                // 4
    current_turn_volume: u32,             // 4
    baton_touch_count: u32,               // 4
    energy_count: u32,                    // 4
    pending_draws: u32,                   // 4
    tapped_energy_count: u32,             // 4
    used_abilities_mask: u32,             // 4
    blade_buffs: array<u32, 4>,           // 16
    board_blades: u32,                    // 4
    lives_cleared_count: u32,             // 4
    avg_hearts: array<u32, 8>,            // 32
    mcts_reward: f32,                     // 4
    baton_touch_limit: u32,               // 4
    moved_flags: u32,                     // 4
    energy_deck_len: u32,                 // 4
    heart_req_additions: array<u32, 2>,   // 8
    yell_count_reduction: u32,            // 4
    prevent_activate: u32,                // 4
    prevent_baton_touch: u32,             // 4
    prevent_success_pile_set: u32,        // 4
    prevent_play_to_slot_mask: u32,       // 4
    cost_reduction: i32,                  // 4
    success_lives: array<u32, 4>,         // 16
    granted_abilities: array<u32, 16>,    // 64
} // Total: 672 bytes

struct GpuGameState {
    player0: GpuPlayerState,
    player1: GpuPlayerState,
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
    trigger_queue: array<GpuTriggerRequest, 8>,
    queue_head: u32,
    queue_tail: u32,
    _pad_game: array<u32, 3>,
} // Total: 1664 bytes

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
    rarity: u32,
    _pad_card: array<u32, 2>,
} // Total: 80 bytes

@group(0) @binding(0) var<storage, read_write> states: array<GpuGameState>;
@group(0) @binding(1) var<storage, read> card_stats: array<GpuCardStats>;
@group(0) @binding(2) var<storage, read> bytecode: array<i32>;
@group(0) @binding(3) var<storage, read_write> scores: array<f32>;

var<private> g_board_hearts: array<array<u32, 8>, 2>;
var<private> g_rng: vec2<u32>;
var<private> g_gid: u32;

// --- OPCODES (Synced with generated_constants.rs) ---
// --- OPCODES (Synced with generated_constants.rs) ---
const O_NOP: i32 = 0;
const O_RETURN: i32 = 1;
const O_JUMP: i32 = 2;
const O_JUMP_IF_FALSE: i32 = 3;
const O_DRAW: i32 = 10;
const O_ADD_BLADES: i32 = 11;
const O_ADD_HEARTS: i32 = 12;
const O_REDUCE_COST: i32 = 13;
const O_LOOK_DECK: i32 = 14;
const O_RECOVER_LIVE: i32 = 15;
const O_BOOST_SCORE: i32 = 16;
const O_RECOVER_MEMBER: i32 = 17;
const O_BUFF_POWER: i32 = 18;
const O_IMMUNITY: i32 = 19;
const O_MOVE_MEMBER: i32 = 20;
const O_SWAP_CARDS: i32 = 21;
const O_SEARCH_DECK: i32 = 22;
const O_ENERGY_CHARGE: i32 = 23;
const O_SET_BLADES: i32 = 24;
const O_SET_HEARTS: i32 = 25;
const O_FORMATION_CHANGE: i32 = 26;
const O_NEGATE_EFFECT: i32 = 27;
const O_ORDER_DECK: i32 = 28;
const O_META_RULE: i32 = 29;
const O_SELECT_MODE: i32 = 30;
const O_MOVE_TO_DECK: i32 = 31;
const O_TAP_OPPONENT: i32 = 32;
const O_PLACE_UNDER: i32 = 33;
const O_RESTRICTION: i32 = 35;
const O_BATON_TOUCH_MOD: i32 = 36;
const O_SET_SCORE: i32 = 37;
const O_SWAP_ZONE: i32 = 38;
const O_TRANSFORM_COLOR: i32 = 39;
const O_REVEAL_CARDS: i32 = 40;
const O_LOOK_AND_CHOOSE: i32 = 41;
const O_CHEER_REVEAL: i32 = 42;
const O_ACTIVATE_MEMBER: i32 = 43;
const O_ADD_TO_HAND: i32 = 44;
const O_COLOR_SELECT: i32 = 45;
const O_REPLACE_EFFECT: i32 = 46;
const O_TRIGGER_REMOTE: i32 = 47;
const O_REDUCE_HEART_REQ: i32 = 48;
const O_MODIFY_SCORE_RULE: i32 = 49;
const O_ADD_STAGE_ENERGY: i32 = 50;
const O_SET_TAPPED: i32 = 51;
const O_ADD_CONTINUOUS: i32 = 52;
const O_TAP_MEMBER: i32 = 53;
const O_PLAY_MEMBER_FROM_HAND: i32 = 57;
const O_MOVE_TO_DISCARD: i32 = 58;
const O_GRANT_ABILITY: i32 = 60;
const O_INCREASE_HEART_COST: i32 = 61;
const O_REDUCE_YELL_COUNT: i32 = 62;
const O_PLAY_MEMBER_FROM_DISCARD: i32 = 63;
const O_PAY_ENERGY: i32 = 64;
const O_SELECT_MEMBER: i32 = 65;
const O_DRAW_UNTIL: i32 = 66;
const O_SELECT_PLAYER: i32 = 67;
const O_SELECT_LIVE: i32 = 68;
const O_REVEAL_UNTIL: i32 = 69;
const O_INCREASE_COST: i32 = 70;
const O_PREVENT_PLAY_TO_SLOT: i32 = 71;
const O_SWAP_AREA: i32 = 72;
const O_TRANSFORM_HEART: i32 = 73;
const O_SELECT_CARDS: i32 = 74;
const O_OPPONENT_CHOOSE: i32 = 75;
const O_PLAY_LIVE_FROM_DISCARD: i32 = 76;
const O_REDUCE_LIVE_SET_LIMIT: i32 = 77;
const O_ACTIVATE_ENERGY: i32 = 81;
const O_PREVENT_ACTIVATE: i32 = 82;
const O_SET_HEART_COST: i32 = 83;
const O_PREVENT_SET_TO_SUCCESS_PILE: i32 = 80;
const O_PREVENT_BATON_TOUCH: i32 = 90;

// --- CONDITIONS (Synced with generated_constants.rs) ---
const C_TURN_1: i32 = 200;
const C_HAS_MEMBER: i32 = 201;
const C_HAS_COLOR: i32 = 202;
const C_COUNT_STAGE: i32 = 203;
const C_COUNT_HAND: i32 = 204;
const C_COUNT_DISCARD: i32 = 205;
const C_IS_CENTER: i32 = 206;
const C_LIFE_LEAD: i32 = 207;
const C_COUNT_GROUP: i32 = 208;
const C_GROUP_FILTER: i32 = 209;
const C_OPPONENT_HAS: i32 = 210;
const C_SELF_IS_GROUP: i32 = 211;
const C_MODAL_ANSWER: i32 = 212;
const C_COUNT_ENERGY: i32 = 213;
const C_HAS_LIVE_CARD: i32 = 214;
const C_COST_CHECK: i32 = 215;
const C_RARITY_CHECK: i32 = 216;
const C_HAND_HAS_NO_LIVE: i32 = 217;
const C_COUNT_SUCCESS_LIVE: i32 = 218;
const C_OPPONENT_HAND_DIFF: i32 = 219;
const C_SCORE_COMPARE: i32 = 220;
const C_HAS_CHOICE: i32 = 221;
const C_OPPONENT_CHOICE: i32 = 222;
const C_COUNT_HEARTS: i32 = 223;
const C_COUNT_BLADES: i32 = 224;
const C_OPPONENT_ENERGY_DIFF: i32 = 225;
const C_HAS_KEYWORD: i32 = 226;
const C_DECK_REFRESHED: i32 = 227;
const C_HAS_MOVED: i32 = 228;
const C_HAND_INCREASED: i32 = 229;
const C_COUNT_LIVE_ZONE: i32 = 230;
const C_BATON: i32 = 231;
const C_TYPE_CHECK: i32 = 232;
const C_IS_IN_DISCARD: i32 = 233;
const C_AREA_CHECK: i32 = 234;

// --- PHASES (Synced with enums.rs) ---
const PHASE_SETUP: i32 = -4;
const PHASE_RPS: i32 = -3;
const PHASE_TURN_CHOICE: i32 = -2;
const PHASE_MULLIGAN_P1: i32 = -1;
const PHASE_MULLIGAN_P2: i32 = 0;
const PHASE_ACTIVE: i32 = 1;
const PHASE_ENERGY: i32 = 2;
const PHASE_DRAW: i32 = 3;
const PHASE_MAIN: i32 = 4;
const PHASE_LIVESET: i32 = 5;
const PHASE_PERFORMANCE_P1: i32 = 6;
const PHASE_PERFORMANCE_P2: i32 = 7;
const PHASE_LIVE_RESULT: i32 = 8;
const PHASE_TERMINAL: i32 = 9;
const PHASE_RESPONSE: i32 = 10;

// --- ACTION ID BASES ---
const ACTION_BASE_PASS: u32 = 0u;
const ACTION_BASE_MODE: u32 = 500u;
const ACTION_BASE_LIVESET: u32 = 400u;
const ACTION_BASE_COLOR: u32 = 580u;
const ACTION_BASE_STAGE_SLOTS: u32 = 600u;
const ACTION_BASE_HAND: u32 = 1000u;
const ACTION_BASE_HAND_CHOICE: u32 = 1200u;
const ACTION_BASE_HAND_SELECT: u32 = 2000u;
const ACTION_BASE_STAGE: u32 = 4000u;
const ACTION_BASE_STAGE_CHOICE: u32 = 4300u;
const ACTION_BASE_DISCARD_ACTIVATE: u32 = 6000u;
const ACTION_BASE_CHOICE: u32 = 8000u;
// ACTION_BASE_TRIGGER: Format = 9000 + slot_idx * 1000 + trigger_type * 100 + ab_idx * 10 + choice
// This allows testing any trigger type with proper trigger_filter
const ACTION_BASE_TRIGGER: u32 = 9000u;

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

fn add_to_deck_top(p_idx: u32, card_id: u32) {
    // Add card to top of deck (position 0, drawn first)
    if (card_id == 0u) { return; }
    var d_len = 0u;
    if (p_idx == 0u) { d_len = states[g_gid].player0.deck_len; }
    else { d_len = states[g_gid].player1.deck_len; }
    if (d_len >= 64u) { return; }
    
    // Shift all cards down by one position
    for (var i = d_len; i > 0u; i = i - 1u) {
        let prev_card = get_deck_card(p_idx, i - 1u);
        set_deck_card(p_idx, i, prev_card);
    }
    // Place new card at position 0 (top)
    set_deck_card(p_idx, 0u, card_id);
    if (p_idx == 0u) {
        states[g_gid].player0.deck_len += 1u;
    } else {
        states[g_gid].player1.deck_len += 1u;
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
        // CPU: Main → Active (opponent's turn starts)
        let other_p = 1u - first_p;
        states[g_gid].current_player = other_p;
        states[g_gid].phase = PHASE_ACTIVE; // Will auto-advance to Energy → Draw → Main
    } else {
        // Both players finished their turns → LiveSet
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
    
    // Process Granted Abilities (Constant Effects)
    for (var i = 0u; i < 8u; i = i + 1u) {
        let word0_idx = i * 2u;
        let word1_idx = i * 2u + 1u;
        var entry0 = 0u; var entry1 = 0u;
        if (p_idx == 0u) {
            entry0 = states[g_gid].player0.granted_abilities[word0_idx];
            entry1 = states[g_gid].player0.granted_abilities[word1_idx];
        } else {
            entry0 = states[g_gid].player1.granted_abilities[word0_idx];
            entry1 = states[g_gid].player1.granted_abilities[word1_idx];
        }
        if (entry0 == 0u) { continue; }
        
        let t_cid = entry0 & 0xFFFFu;
        let s_cid = entry0 >> 16u;
        let ab_idx = entry1;
        
        // Find if target is still on board
        var target_on_board = false;
        var t_slot = 99u;
        for (var sl = 0u; sl < 3u; sl = sl + 1u) {
            if (get_stage_card(p_idx, sl) == t_cid) { target_on_board = true; t_slot = sl; break; }
        }
        if (!target_on_board) { continue; }

        if (s_cid < arrayLength(&card_stats)) {
            let s_stats = card_stats[s_cid];
            var pool_ip = s_stats.bytecode_start;
            let pool_end = s_stats.bytecode_start + s_stats.bytecode_len;
            if (pool_ip < arrayLength(&bytecode)) {
                let num_ab = u32(bytecode[pool_ip]);
                pool_ip += 1u;
                for (var j = 0u; j < num_ab; j += 1u) {
                    if (pool_ip + 3u >= pool_end) { break; }
                    let trigger = bytecode[pool_ip];
                    let ab_len = u32(bytecode[pool_ip + 3u]);
                    pool_ip += 4u;
                    if (j == ab_idx) {
                        // Very basic constant effect execution
                        var ip = pool_ip; let end = pool_ip + ab_len;
                        while (ip + 3u < end) {
                            let op = bytecode[ip]; let v = bytecode[ip+1]; let a = bytecode[ip+2]; let s = bytecode[ip+3];
                            ip += 4u;
                            if (op == 11 || op == 18) { // O_ADD_BLADES / O_BUFF_POWER
                                total_blades += u32(v);
                            } else if (op == 12) { // O_ADD_HEARTS
                                let color = min(u32(a), 7u);
                                total_hearts[color] += u32(v);
                            }
                        }
                        break;
                    }
                    pool_ip += ab_len;
                }
            }
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

fn match_filter(cid: u32, attr: u32) -> bool {
    if (cid == 0u || cid >= arrayLength(&card_stats)) { return false; }
    let s = card_stats[cid];

    // Cost Filter (bits 24-30)
    // Bit 24: Enable (0x01000000)
    // Bits 25-30: Value (cost << 25)
    // Bit 30: is_le flag (0x40000000) - if set, check cost <= value, else cost >= value
    if ((attr & 0x01000000u) != 0u) {
        let cost_value = (attr >> 25u) & 0x3Fu;
        let is_le = (attr & 0x40000000u) != 0u;
        if (is_le) {
            if (s.cost > cost_value) { return false; }
        } else {
            if (s.cost < cost_value) { return false; }
        }
    }

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

fn check_condition_opcode(p_idx: u32, op: i32, v: i32, a: u32, target_slot: u32, ctx_cid: u32) -> bool {
    let cid = select(u32(states[g_gid].prev_card_id), ctx_cid, ctx_cid != 0u);
    switch (op) {
        case 200: { return states[g_gid].turn == 1u; }
        case 201: { 
            var count = 0u;
            for (var s = 0u; s < 3u; s = s + 1u) {
                if (get_stage_card(p_idx, s) == u32(a)) { count = count + 1u; }
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
            let group_id = a;
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
                var f_filter = u32(a);
                if ((f_filter & 0x10u) == 0u && f_filter != 0u && f_filter < 300u) {
                    f_filter = 0x10u | (f_filter << 5u);
                } else if ((f_filter & 0x10u) == 0u && v != 0) {
                    f_filter = 0x10u | (u32(v) << 5u);
                }
                return match_filter(cid, f_filter);
            }
            return false;
        }
        case 210: { // C_OPPONENT_HAS
             let filter_attr = u32(a);
             let o_idx = 1u - p_idx;
             for (var s = 0u; s < 3u; s = s + 1u) {
                 let s_cid = get_stage_card(o_idx, s);
                 if (s_cid > 0u) {
                     if (s_cid == u32(v)) { return true; }
                     if (filter_attr != 0u && match_filter(s_cid, filter_attr)) { return true; }
                 }
             }
             return false;
        }
        case 211: { 
            var c_cid = 0u;
            if (target_slot < 3u) { c_cid = get_stage_card(p_idx, target_slot); }
            if (c_cid > 0u && c_cid < arrayLength(&card_stats)) {
                let groups = card_stats[c_cid].groups;
                if (((groups >> 0u) & 0xFFu) == a) { return true; }
                if (((groups >> 8u) & 0xFFu) == a) { return true; }
                if (((groups >> 16u) & 0xFFu) == a) { return true; }
                if (((groups >> 24u) & 0xFFu) == a) { return true; }
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
             let filter_attr = u32(a);
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
                if (get_discard_card(p_idx, i) == u32(a)) { return true; }
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
            let keyword_flags = u32(a);
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
            if (ip + 4u > end) { break; }
            let op = bytecode[ip]; let v = bytecode[ip + 1]; let a = bytecode[ip + 2]; let s = bytecode[ip + 3];
            ip = ip + 4;
            let target_raw = u32(s);
            let target_slot = target_raw & 0xFFu;
            
            if (op <= 0) { continue; }
            if (op == O_RETURN) { break; }
            
            var real_op = op; var is_negated = false;
            if (real_op >= 1000) { real_op = real_op - 1000; is_negated = true; }
            
            if (real_op >= 200 && real_op <= 299) {
                let passed = check_condition_opcode(p_idx, real_op, v, u32(a), target_slot, card_id);
                cond = passed; if (is_negated) { cond = !cond; }
                continue;
            }
            if (real_op == O_JUMP) { ip = u32(i32(ip) + v * 4); continue; }
            if (real_op == O_JUMP_IF_FALSE) { if (!cond) { ip = u32(i32(ip) + v * 4); } continue; }
            
            if (real_op >= 10 && real_op < 100) {
                switch (real_op) {
                    case O_DRAW: { for (var d = 0; d < v; d = d + 1) { draw_card(p_idx); } }
                    case 11, 18: { // O_ADD_BLADES / O_BUFF_POWER
                        let ab_t_slot = resolve_target_slot(target_slot, slot_idx);
                        if (p_idx == 0u) { states[g_gid].player0.blade_buffs[ab_t_slot] += u32(v); }
                        else { states[g_gid].player1.blade_buffs[ab_t_slot] += u32(v); }
                    }
                    case O_ADD_HEARTS: {
                        var color = u32(a);
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
                        if (u32(a) == 1u) { // FLAG_CANNOT_LIVE
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
                        let color = u32(a);
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
                        let mv_dst = u32(a);
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
                            if (check_condition_opcode(p_idx, cond_v, i32(a), 0u, rev_t_slot, cid)) {
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
                        // v = count, a = attr (zone info in upper bits), s = target
                        // a bits 12-15: source zone (6=hand, 4=stage, 13=discard)
                        let source_zone = (u32(a) >> 12u) & 0x0Fu;
                        let count = u32(v);
                        
                        // Determine destination: deck_top (a bit 0) or deck_bottom
                        let to_top = (u32(a) & 0x01u) == 0u;
                        
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
                        let zone = select(target_slot, u32(a >> 12u) & 0x0Fu, (u32(a >> 12u) & 0x0Fu) != 0u);
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
                        let filter_attr = u32(a);
                        let dst_slot = u32(s) & 0x0Fu;
                        let choice_card_idx = u32(choice);
                        var pm_h_len = 0u;
                        if (p_idx == 0u) { pm_h_len = states[g_gid].player0.hand_len; }
                        else { pm_h_len = states[g_gid].player1.hand_len; }

                        if (choice_card_idx < pm_h_len && dst_slot < 3u) {
                            let pm_cid = get_hand_card(p_idx, choice_card_idx);
                            if (pm_cid != 0u && match_filter(pm_cid, filter_attr)) {
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
                        let filter_attr_d = u32(a);
                        let dst_slot_d = u32(s) & 0x0Fu;
                        let choice_disc_idx = u32(choice);
                        var pmd_d_len = 0u;
                        if (p_idx == 0u) { pmd_d_len = states[g_gid].player0.discard_pile_len; }
                        else { pmd_d_len = states[g_gid].player1.discard_pile_len; }

                        if (choice_disc_idx < pmd_d_len && dst_slot_d < 3u) {
                            let pmd_cid = get_discard_card(p_idx, choice_disc_idx);
                            if (pmd_cid != 0u && match_filter(pmd_cid, filter_attr_d)) {
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
                        let src_color = u32(a); let dst_color = u32(s);
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
                         // Simplify: often used for "Treat Color X as Y". 
                         // For now, we add hearts to Y if X exists.
                         let src = u32(a); let dst = u32(v);
                         if (src < 8u && dst < 8u) {
                             let h = get_board_heart(p_idx, src);
                             add_board_heart(p_idx, dst, h);
                         }
                    }

                    case O_ADD_TO_HAND: {
                        let t = u32(a);
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
                        let sa_dst = u32(a);
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
    if (phase == PHASE_RPS) { states[g_gid].phase = PHASE_ENERGY; return 1u; }
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

fn select_rollout_action(p_idx: u32) -> u32 {
    return select_random_legal_action(p_idx);
}

fn evaluate_terminal(tactical_score: array<u32, 2>) -> f32 {
    let p0_lc = states[g_gid].player0.lives_cleared_count;
    let p1_lc = states[g_gid].player1.lives_cleared_count;
    if (p0_lc >= 3u) { return 1.0; }
    if (p1_lc >= 3u) { return 0.0; }
    return 0.5; // Unfinished game or draw
}

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    g_gid = gid.x;
    if (g_gid >= arrayLength(&states)) { return; }
    
    // Initialize RNG state
    g_rng = vec2<u32>(states[g_gid].rng_state_lo, states[g_gid].rng_state_hi);
    if (g_rng.x == 0u && g_rng.y == 0u) { g_rng.x = g_gid + 1u; }
    
    let phase = states[g_gid].phase;
    if (phase == PHASE_TERMINAL) { return; }
    
    // Single Rollout Step
    var action = 0u;
    if (states[g_gid].forced_action != -1) {
        action = u32(states[g_gid].forced_action);
        states[g_gid].forced_action = -1; // Consume it
    } else {
        if (phase == PHASE_MAIN || phase == PHASE_LIVESET || phase == PHASE_RESPONSE || phase == PHASE_MULLIGAN_P1 || phase == PHASE_MULLIGAN_P2) {
            action = select_random_legal_action(states[g_gid].current_player);
        } else {
            action = 0u;
        }
    }
    
    let res = step_state(action);
    
    // Update step count telemetry (stored in _pad_game[0])
    if (res != 0u) {
        states[g_gid]._pad_game[0] = states[g_gid]._pad_game[0] + 1u;
    }
    
    // AUTO-PHASE ADVANCE: Continue stepping through non-interactive phases
    // This mirrors CPU's step() which auto-advances Active→Energy→Draw→Main
    var current_phase = states[g_gid].phase;
    var safety = 0u;
    while (current_phase != PHASE_TERMINAL && 
           current_phase != PHASE_MAIN && 
           current_phase != PHASE_LIVESET && 
           current_phase != PHASE_RESPONSE && 
           current_phase != PHASE_MULLIGAN_P1 && 
           current_phase != PHASE_MULLIGAN_P2 &&
           current_phase != PHASE_LIVE_RESULT &&
           current_phase != PHASE_ENERGY &&
           safety < 10u) {
        let auto_res = step_state(0u);
        if (auto_res == 0u) { break; }
        current_phase = states[g_gid].phase;
        safety += 1u;
    }
    
    // Final evaluation if we just hit terminal
    if (states[g_gid].phase == PHASE_TERMINAL) {
        let p0_lc = states[g_gid].player0.lives_cleared_count;
        let p1_lc = states[g_gid].player1.lives_cleared_count;
        var score = 0.5;
        if (p0_lc >= 3u) { score = 1.0; }
        else if (p1_lc >= 3u) { score = 0.0; }
        else { score = 0.5 + f32(p0_lc) * 0.1 - f32(p1_lc) * 0.1; }
        scores[g_gid] = score;
    }

    // Persist RNG state for next dispatch
    states[g_gid].rng_state_lo = g_rng.x;
    states[g_gid].rng_state_hi = g_rng.y;
}
