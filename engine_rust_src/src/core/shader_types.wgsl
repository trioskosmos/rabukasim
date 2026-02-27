struct GpuTriggerRequest {
    card_id: u32,
    slot_idx: u32,
    trigger_filter: i32,
    ab_filter: i32,
    choice: i32,
    _pad: array<u32, 3>,
}

// Interaction types for Response phase
const INTERACTION_LOOK_AND_CHOOSE: u32 = 1u;
const INTERACTION_COLOR_SELECT: u32 = 2u;
const INTERACTION_SELECT_DISCARD: u32 = 3u;
const INTERACTION_SELECT_HAND: u32 = 4u;
const INTERACTION_SELECT_STAGE: u32 = 5u;
const INTERACTION_OPPONENT_CHOOSE: u32 = 6u;

// Interaction stack entry for suspending bytecode execution
struct GpuInteraction {
    card_id: u32,           // Card that triggered the interaction
    slot_idx: u32,          // Slot index of the card
    trigger_filter: i32,    // Trigger type being processed
    ab_filter: i32,         // Ability index being processed
    original_phase: i32,    // Phase to return to after interaction
    choice_type: u32,       // Type of interaction (LOOK_AND_CHOOSE, etc.)
    param_v: i32,           // Original v parameter
    param_a_lo: u32,        // Original a_lo parameter
    param_a_hi: u32,        // Original a_hi parameter
    param_s: i32,           // Original s parameter
    bytecode_start: u32,    // Start of bytecode for resume
    bytecode_len: u32,      // Length of bytecode
    ip_offset: u32,         // Instruction pointer offset for resume
    _pad: array<u32, 3>,    // Padding for alignment (64 bytes total)
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
    live_score_bonus: i32,                // 4
    hand_increased_this_turn: u32,        // 4
    played_group_mask: u32,               // 4
    excess_hearts: u32,                   // 4
    granted_abilities: array<u32, 16>,    // 64
} // Total: 688 bytes

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
    // Interaction stack for Response phase
    interaction_stack: array<GpuInteraction, 4>,
    interaction_depth: u32,
    _pad_game: array<u32, 2>,
} // Total: updated with interaction stack

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
const O_LOOK_DECK_DYNAMIC: i32 = 91;
const O_REDUCE_SCORE: i32 = 92;
const O_REPEAT_ABILITY: i32 = 93;
const O_LOSE_EXCESS_HEARTS: i32 = 94;
const O_SKIP_ACTIVATE_PHASE: i32 = 95;
const O_PAY_ENERGY_DYNAMIC: i32 = 96;
const O_PLACE_ENERGY_UNDER_MEMBER: i32 = 97;

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
