use bytemuck::{Pod, Zeroable};

// Fixed constants for GPU memory alignment
pub const MAX_HAND: usize = 64;
pub const MAX_DECK: usize = 64;
pub const MAX_DISCARD: usize = 64;
pub const MAX_TRIGGER_QUEUE: usize = 8;
pub const MAX_INTERACTION_STACK: usize = 4;

// Interaction types for Response phase
pub const INTERACTION_LOOK_AND_CHOOSE: u32 = 1;
pub const INTERACTION_COLOR_SELECT: u32 = 2;
pub const INTERACTION_SELECT_DISCARD: u32 = 3;
pub const INTERACTION_SELECT_HAND: u32 = 4;
pub const INTERACTION_SELECT_STAGE: u32 = 5;
pub const INTERACTION_OPPONENT_CHOOSE: u32 = 6;

/// GPU-compatible player state with fixed-size arrays.
/// All fields are u32 for maximum Pod compatibility and alignment safety.
#[repr(C)]
#[derive(Copy, Clone, Debug, Pod, Zeroable, Default)]
pub struct GpuTriggerRequest {
    pub card_id: u32,
    pub slot_idx: u32,
    pub trigger_filter: i32,
    pub ab_filter: i32,
    pub choice: i32,
    pub _pad: [u32; 3], // Align to 32 bytes
}

/// Interaction stack entry for suspending bytecode execution during Response phase
#[repr(C)]
#[derive(Copy, Clone, Debug, Pod, Zeroable, Default)]
pub struct GpuInteraction {
    pub card_id: u32,           // Card that triggered the interaction
    pub slot_idx: u32,          // Slot index of the card
    pub trigger_filter: i32,    // Trigger type being processed
    pub ab_filter: i32,         // Ability index being processed
    pub original_phase: i32,    // Phase to return to after interaction
    pub choice_type: u32,       // Type of interaction (LOOK_AND_CHOOSE, etc.)
    pub param_v: i32,           // Original v parameter
    pub param_a_lo: u32,        // Original a_lo parameter
    pub param_a_hi: u32,        // Original a_hi parameter
    pub param_s: i32,           // Original s parameter
    pub bytecode_start: u32,    // Start of bytecode for resume
    pub bytecode_len: u32,      // Length of bytecode
    pub ip_offset: u32,         // Instruction pointer offset for resume
    pub _pad: [u32; 2],         // Padding for alignment
}

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
    pub cost_reduction: i32,             // 4 bytes
    pub success_lives: [u32; 4],         // 16 bytes
    pub live_score_bonus: i32,           // 4 bytes
    pub hand_increased_this_turn: u32,   // 4 bytes
    pub played_group_mask: u32,          // 4 bytes
    pub excess_hearts: u32,              // 4 bytes
    pub granted_abilities: [u32; 16],    // 64 bytes -> Total 688 bytes
}

#[repr(C)]
#[derive(Copy, Clone, Debug, Pod, Zeroable)]
pub struct GpuGameState {
    pub player0: GpuPlayerState,          // 688 bytes
    pub player1: GpuPlayerState,          // 688 bytes
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
    pub trigger_queue: [GpuTriggerRequest; 8], // 256 bytes
    pub queue_head: u32,                 // 4 bytes
    pub queue_tail: u32,                 // 4 bytes
    // Interaction stack for Response phase
    pub interaction_stack: [GpuInteraction; 4], // 4 * 56 = 224 bytes
    pub interaction_depth: u32,          // 4 bytes
    pub _pad_game: [u32; 2],             // 8 bytes
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
            trigger_queue: [GpuTriggerRequest::default(); 8],
            queue_head: 0,
            queue_tail: 0,
            interaction_stack: [GpuInteraction::default(); 4],
            interaction_depth: 0,
            _pad_game: [0; 2],
        }
    }
}

pub const GPU_GAME_STATE_SIZE: usize = 1936; // Updated for new fields in GpuPlayerState (688 * 2 + 560)

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

#[cfg(test)]
mod tests {
    use super::*;
    use std::mem::{size_of, align_of, offset_of};

    #[test]
    fn test_layout_consistency() {
        // GpuPlayerState (688 bytes)
        assert_eq!(size_of::<GpuPlayerState>(), 688);
        assert_eq!(align_of::<GpuPlayerState>(), 4);
        assert_eq!(offset_of!(GpuPlayerState, heart_buffs), 0);
        assert_eq!(offset_of!(GpuPlayerState, flags), 444);
        assert_eq!(offset_of!(GpuPlayerState, energy_count), 472);
        assert_eq!(offset_of!(GpuPlayerState, avg_hearts), 512);
        assert_eq!(offset_of!(GpuPlayerState, success_lives), 592);

        // GpuGameState (1936 bytes) - updated for interaction_stack
        assert_eq!(size_of::<GpuGameState>(), 1936);
        assert_eq!(align_of::<GpuGameState>(), 4);
        assert_eq!(offset_of!(GpuGameState, player0), 0);
        assert_eq!(offset_of!(GpuGameState, player1), 688);
        assert_eq!(offset_of!(GpuGameState, current_player), 1376);
        assert_eq!(offset_of!(GpuGameState, phase), 1380);
        assert_eq!(offset_of!(GpuGameState, winner), 1392);
        assert_eq!(offset_of!(GpuGameState, rng_state_lo), 1408);
        // trigger_queue offset: 1376 + 44 bytes = 1420
        assert_eq!(offset_of!(GpuGameState, trigger_queue), 1420);
        // trigger_queue is 8 * 32 = 256 bytes, so 1420 + 256 = 1676
        assert_eq!(offset_of!(GpuGameState, queue_head), 1676);
        assert_eq!(offset_of!(GpuGameState, queue_tail), 1680);
        // interaction_stack is at 1684
        assert_eq!(offset_of!(GpuGameState, interaction_stack), 1684);
        // interaction_stack is 4 * 60 = 240 bytes, so 1684 + 240 = 1924
        assert_eq!(offset_of!(GpuGameState, interaction_depth), 1924);

        // GpuCardStats (80 bytes)
        assert_eq!(size_of::<GpuCardStats>(), 80);
        assert_eq!(offset_of!(GpuCardStats, bytecode_start), 20);
        assert_eq!(offset_of!(GpuCardStats, hearts_lo), 36);
        assert_eq!(offset_of!(GpuCardStats, synergy_flags), 64);
    }
}
