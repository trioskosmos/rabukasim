//! # Logic Constants
//!
//! Consolidated constants for game logic, action spaces, and interpreter flags.

pub const ACTION_SPACE: usize = 16384;

// Heuristic flags (matches generated_constants.rs types)
pub use crate::core::generated_constants::*;

// --- Filter Bitfield Shifts (Revision 5) ---
// These shifts define the "A" parameter (attribute/filter) in the bytecode.
// Alignment: This uses the `A_STANDARD` layout from `generated_layout.rs`.
//
// Layout Mapping (Revision 5):
pub const FILTER_TARGET_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_TARGET_PLAYER_SHIFT as u64;
pub const FILTER_TYPE_SHIFT_R5: u64 = crate::core::generated_layout::A_STANDARD_CARD_TYPE_SHIFT as u64;
pub const FILTER_GROUP_ENABLE_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_GROUP_ENABLED_SHIFT as u64;
pub const FILTER_GROUP_ID_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_GROUP_ID_SHIFT as u64;
pub const FILTER_STATE_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_IS_TAPPED_SHIFT as u64;
pub const FILTER_UNIT_ENABLE_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_UNIT_ENABLED_SHIFT as u64;
pub const FILTER_UNIT_ID_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_UNIT_ID_SHIFT as u64;
pub const FILTER_VALUE_ENABLE_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_VALUE_ENABLED_SHIFT as u64;
pub const FILTER_VALUE_THRESHOLD_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_VALUE_THRESHOLD_SHIFT as u64;
pub const FILTER_VALUE_LE_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_IS_LE_SHIFT as u64;
pub const FILTER_VALUE_TYPE_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_IS_COST_TYPE_SHIFT as u64;
pub const FILTER_COLOR_SHIFT_R5: u64 = crate::core::generated_layout::A_STANDARD_COLOR_MASK_SHIFT as u64;
pub const FILTER_CHAR_1_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_CHAR_ID_1_SHIFT as u64;
pub const FILTER_CHAR_2_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_CHAR_ID_2_SHIFT as u64;
pub const FILTER_ZONE_MASK_SHIFT_R5: u64 = crate::core::generated_layout::A_STANDARD_ZONE_MASK_SHIFT as u64;
pub const FILTER_SPECIAL_ID_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_SPECIAL_ID_SHIFT as u64;
pub const FILTER_SETSUNA_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_IS_SETSUNA_SHIFT as u64;
pub const FILTER_DYNAMIC_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_COMPARE_ACCUMULATED_SHIFT as u64;
pub const FILTER_OPTIONAL_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_IS_OPTIONAL_SHIFT as u64;
pub const FILTER_KW_ENERGY_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_KEYWORD_ENERGY_SHIFT as u64;
pub const FILTER_KW_MEMBER_SHIFT: u64 = crate::core::generated_layout::A_STANDARD_KEYWORD_MEMBER_SHIFT as u64;

// NOTE: Some opcodes (e.g., O_SET_HEART_COST) use A_HEART_COST layout.
// Use `crate::core::generated_layout::A_HEART_COST_...` for those.

// --- Interpreter / Filter Constants ---
pub const OPCODE_NEGATION_OFFSET: i32 = 1000;

pub const CONDITION_START_1: i32 = 200;
pub const CONDITION_END_1: i32 = 255;
pub const CONDITION_START_2: i32 = 301;
pub const CONDITION_END_2: i32 = 399;

/// Mask for the 7-bit color flags (Standardized to 32).
pub const FILTER_COLOR_MASK: u64 = 545460846592; // 0x7F << 32

// Standardized Value Flags (Matches A_STANDARD layout)
pub const FILTER_VALUE_ENABLE_FLAG: u64 = 16777216; // 1 << 24
pub const FILTER_VALUE_LE_FLAG: u64 = 1073741824; // 1 << 30
pub const FILTER_VALUE_TYPE_FLAG: u64 = 2147483648; // 1 << 31

/// Special choice index for "Done" or "Cancel".
pub const CHOICE_DONE: i16 = 99;
/// Special choice index for "All" or "Everything".
pub const CHOICE_ALL: i16 = 999;

/// Mask for all filter type flags (Member, Live, Group, Unit, Cost, Blade).
pub const FILTER_TYPE_MASK: u64 = 16842780; // 0x101001C - CardType, Group, Unit, Value enable flags

// --- A Word (attr) Target Flags (Bits 0-1) ---

/// Flag indicating targeting Player/Self (A word bit 0)
pub const FILTER_TARGET_PLAYER_FLAG: u64 = 0x01;
/// Flag indicating targeting Opponent (A word bit 1)
pub const FILTER_TARGET_OPPONENT_FLAG: u64 = 0x02;
