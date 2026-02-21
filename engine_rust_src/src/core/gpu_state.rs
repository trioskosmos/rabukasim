use bytemuck::{Pod, Zeroable};

// Fixed constants for GPU memory alignment
pub const MAX_HAND: usize = 64;
pub const MAX_DECK: usize = 64;
pub const MAX_DISCARD: usize = 64;

/// GPU-compatible player state with fixed-size arrays.
/// All fields are u32 for maximum Pod compatibility and alignment safety.
#[repr(C)]
#[derive(Copy, Clone, Debug, Pod, Zeroable, Default)]
pub struct GpuPlayerState {
    pub heart_buffs: [u32; 8],           // 32 bytes
    pub heart_req_reductions: [u32; 2],  // 8 bytes
    pub deck: [u32; 32],                 // 128 bytes
    pub hand: [u32; 32],                 // 128 bytes
    pub discard_pile: [u32; 32],         // 128 bytes
    pub stage: [u32; 2],                 // 8 bytes
    pub live_zone: [u32; 2],             // 8 bytes
    pub score: u32,                      // 4 bytes
    pub flags: u32,                      // 4 bytes
    pub hand_added_mask: u32,            // 4 bytes
    pub hand_len: u32,                   // 4 bytes
    pub deck_len: u32,                   // 4 bytes
    pub discard_pile_len: u32,           // 4 bytes
    pub current_turn_volume: u32,        // 4 bytes
    pub baton_touch_count: u32,          // 4 bytes
    pub energy_count: u32,               // 4 bytes
    pub pending_draws: u32,             // 4 bytes
    pub tapped_energy_count: u32,        // 4 bytes
    pub used_abilities_mask: u32,        // 4 bytes
    pub blade_buffs: [u32; 4],           // 16 bytes (per-slot buffs + 1 padding)
    pub board_blades: u32,               // 4 bytes
    pub lives_cleared_count: u32,        // 4 bytes
    pub avg_hearts: [u32; 8],            // 32 bytes
    pub mcts_reward: f32,                // 4 bytes
    pub baton_touch_limit: u32,          // 4 bytes
    pub moved_flags: u32,                // 4 bytes
    pub energy_deck_len: u32,            // 4 bytes
    pub heart_req_additions: [u32; 2],   // 8 bytes
    pub yell_count_reduction: u32,       // 4 bytes
    pub prevent_activate: u32,           // 4 bytes
    pub prevent_baton_touch: u32,        // 4 bytes
    pub prevent_success_pile_set: u32,   // 4 bytes
    pub prevent_play_to_slot_mask: u32,  // 4 bytes
    pub _pad_player: u32,                // 4 bytes
    pub success_lives: [u32; 4],         // 16 bytes -> Total 608 bytes
}

#[repr(C)]
#[derive(Copy, Clone, Debug, Pod, Zeroable)]
pub struct GpuGameState {
    pub player0: GpuPlayerState,          // 608 bytes
    pub player1: GpuPlayerState,          // 608 bytes
    pub current_player: u32,             // 4 bytes
    pub phase: i32,                      // 4 bytes
    pub turn: u32,                       // 4 bytes
    pub active_count: u32,               // 4 bytes
    pub winner: i32,                     // 4 bytes
    pub prev_card_id: i32,               // 4 bytes
    pub forced_action: i32,              // 4 bytes
    pub is_debug: u32,                   // 4 bytes
    pub rng_state_lo: u32,               // 4 bytes
    pub rng_state_hi: u32,               // 4 bytes
    pub first_player: u32,               // 4 bytes
    pub _pad_game: [u32; 5],             // 20 bytes -> Total 1280 bytes (multiple of 16)
}

impl Default for GpuGameState {
    fn default() -> Self {
        Self {
            player0: GpuPlayerState::default(),
            player1: GpuPlayerState::default(),
            rng_state_lo: 0,
            rng_state_hi: 0,
            current_player: 0,
            phase: 0,
            turn: 0,
            active_count: 0,
            winner: 0,
            prev_card_id: 0,
            forced_action: -1,
            is_debug: 0,
            first_player: 0,
            _pad_game: [0; 5],
        }
    }
}

pub const GPU_GAME_STATE_SIZE: usize = 1280;

#[repr(C)]
#[derive(Copy, Clone, Debug, Pod, Zeroable, Default)]
pub struct GpuCardStats {
    pub ability_flags_lo: u32,           // 4 bytes
    pub ability_flags_hi: u32,           // 4 bytes
    pub cost: u32,                       // 4 bytes
    pub blades: u32,                     // 4 bytes
    pub card_type: u32,                  // 4 bytes
    pub bytecode_start: u32,             // 4 bytes
    pub bytecode_len: u32,               // 4 bytes
    pub volume_icons: u32,               // 4 bytes
    pub extra_val: u32,                  // 4 bytes
    pub hearts_lo: u32,                  // 4 bytes
    pub hearts_hi: u32,                  // 4 bytes
    pub blade_hearts_lo: u32,            // 4 bytes
    pub blade_hearts_hi: u32,            // 4 bytes
    pub groups: u32,                     // 4 bytes
    pub units: u32,                      // 4 bytes
    pub char_id: u32,                    // 4 bytes
    pub synergy_flags: u32,              // 4 bytes
    pub rarity: u32,                     // 4 bytes
    pub _pad_card: [u32; 2],             // 8 bytes -> Total 80 bytes (multiple of 16)
}
