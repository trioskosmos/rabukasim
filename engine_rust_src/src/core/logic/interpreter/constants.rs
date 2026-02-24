//! # Interpreter Constants
//!
//! Defined bitmasks and flags used by the interpreter's filtering and condition logic.

/// Mask for the lower 32 bits of the attribute, often used for basic filters.
pub const FILTER_MASK_LOWER: u64 = 0x00000000FFFFFFFF;

/* 
 * BYTECODE LAYOUT (S Word - 32 bits)
 * ----------------------------------
 * Bits 0-7:   Target Slot / Player ID (Mask: 0xFF)
 * Bits 8-15:  Destination Zone (Mask: 0xFF << 8)
 * Bits 16-23: Source Zone (Mask: 0xFF << 16)
 * Bits 24-31: Reserved / Flags (Mask: 0xFF << 24)
 *
 * ZONES (Values for Bits 8-15, 16-23):
 * 0: Default, 1: Deck Top, 2: Deck Bottom, 3: Energy Zone, 4: Stage, 6: Hand, 7: Discard, 13: Live Set, 15: Yell Cards
 */

/// Flag indicating the card must be a Member.
pub const FILTER_TYPE_MEMBER: u64 = 0x04;
/// Flag indicating the card must be a Live card.
pub const FILTER_TYPE_LIVE: u64 = 0x08;
/// Flag indicating the effect/cost is optional (may).
pub const FILTER_IS_OPTIONAL: u64 = 0x01;
/// Flag indicating the value should be multiplied by a count (Dynamic Value).
pub const DYNAMIC_VALUE: u64 = 0x02;

/// Flag indicating a specific Group ID filter is active.
pub const FILTER_GROUP_FLAG: u64 = 0x10;
/// Bit shift for the Group ID value.
pub const FILTER_GROUP_SHIFT: u64 = 5;

/// Flag indicating the card must be Tapped.
pub const FILTER_TAPPED: u64 = 0x1000; // Bit 12
/// Flag indicating the card must have a Blade Heart.
pub const FILTER_HAS_BLADE_HEART: u64 = 0x2000; // Bit 13
/// Flag indicating the card must NOT have a Blade Heart.
pub const FILTER_NOT_HAS_BLADE_HEART: u64 = 0x4000; // Bit 14
/// Flag indicating unique names should be counted instead of total instances.
pub const FILTER_UNIQUE_NAMES: u64 = 0x8000; // Bit 15 - COLLIDES with Source Zone if using 'a' word!

/// Flag indicating a specific Unit ID filter is active.
pub const FILTER_UNIT_FLAG: u64 = 0x10000;
/// Bit shift for the Unit ID value.
pub const FILTER_UNIT_SHIFT: u64 = 17;

/// Flag indicating a Cost-based filter is active.
pub const FILTER_COST_FLAG: u64 = 0x01000000;
/// Flag indicating a Blade-based filter is active.
pub const FILTER_BLADE_FILTER_FLAG: u64 = 0x02000000;

/// Bit shift for thresholds (Cost, Blade count, etc.).
pub const FILTER_VALUE_SHIFT: u64 = 25;

/// Bit shift for color masks.
pub const FILTER_COLOR_SHIFT: u64 = 32;
/// Mask for the 7-bit color flags.
pub const FILTER_COLOR_MASK: u64 = 0x7F << FILTER_COLOR_SHIFT;

/// Less-than-or-Equal (LE) threshold flag.
pub const FILTER_IS_LE: u64 = 0x40000000;

/// Flag for checking all stage slots (Any Stage).
pub const FILTER_ANY_STAGE: u64 = 1u64 << 40;
/// Flag for explicitly checking the opponent's zones.
pub const FILTER_OPPONENT: u64 = 1u64 << 41;
/// Flag for checking cards in the "Revealed" context.
pub const FILTER_REVEALED_CONTEXT: u64 = 1u64 << 43;

/// Flag for checking if any cards were played this turn.
pub const KEYWORD_PLAYED_THIS_TURN: u64 = 1u64 << 44;
/// Flag for checking Yell-related counts.
pub const KEYWORD_YELL_COUNT: u64 = 1u64 << 45;
/// Flag for checking if a Live card is set.
pub const KEYWORD_HAS_LIVE_SET: u64 = 1u64 << 46;

/// Bit shift for special ID tags (names, unique IDs, etc.).
pub const FILTER_SPECIAL_ID_SHIFT: u64 = 48;

/// Mask for all filter type flags (Member, Live, Group, Unit, Cost, Blade).
pub const FILTER_TYPE_MASK: u64 = FILTER_TYPE_MEMBER | FILTER_TYPE_LIVE | FILTER_GROUP_FLAG | FILTER_UNIT_FLAG | FILTER_COST_FLAG | FILTER_BLADE_FILTER_FLAG;

/// Special choice index for "Done" or "Cancel".
pub const CHOICE_DONE: i16 = 99;
/// Special choice index for "All" or "Everything".
pub const CHOICE_ALL: i16 = 999;

/// Flag for targeting the opponent (S word bit 24).
pub const FLAG_TARGET_OPPONENT: u64 = 0x01000000;
/// Flag for REVEAL_UNTIL live card check (S word bit 25).
pub const FLAG_REVEAL_UNTIL_IS_LIVE: u64 = 0x02000000;
