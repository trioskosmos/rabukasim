//! # Logic Constants
//!
//! Consolidated constants for game logic, action spaces, and interpreter flags.

pub const ACTION_SPACE: usize = 16384;

// Heuristic flags (matches generated_constants.rs types)
pub use crate::core::generated_constants::*;

// --- Interpreter / Filter Constants ---

/// Mask for the 7-bit color flags (uses FILTER_COLOR_SHIFT from generated_constants).
pub const FILTER_COLOR_MASK: u64 = 0x7F << 32; // 32 = FILTER_COLOR_SHIFT

/// Special choice index for "Done" or "Cancel".
pub const CHOICE_DONE: i16 = 99;
/// Special choice index for "All" or "Everything".
pub const CHOICE_ALL: i16 = 999;

/// Mask for all filter type flags (Member, Live, Group, Unit, Cost, Blade).
pub const FILTER_TYPE_MASK: u64 = FILTER_TYPE_MEMBER
    | FILTER_TYPE_LIVE
    | FILTER_GROUP_ENABLE
    | FILTER_UNIT_ENABLE
    | FILTER_COST_ENABLE
    | FILTER_BLADE_FILTER_FLAG;





// --- A Word (attr) Target Flags (Bits 0-1) ---

/// Flag indicating targeting Player/Self (A word bit 0)
pub const FILTER_TARGET_PLAYER: u64 = 0x01;
/// Flag indicating targeting Opponent (A word bit 1)
pub const FILTER_TARGET_OPPONENT: u64 = 0x02;
