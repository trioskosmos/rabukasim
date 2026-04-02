//! Legacy Bytecode Codec
//!
//! This module contains all packed integer encoding/decoding logic for backwards compatibility.
//! All new code should use structured types (CardFilter, DecodedSlot, etc.) directly.
//!
//! This module is quarantined - it should only be used for:
//! - Importing legacy bytecode data
//! - Archive/forensic tools
//! - Regression tests that verify legacy round-trips

use crate::core::enums::Zone;
use crate::core::generated_constants::*;
use crate::core::generated_layout::*;
use crate::core::logic::filter::CardFilter;

/// Encode a CardFilter to packed 64-bit format (legacy)
pub fn encode_filter(filter: &CardFilter) -> u64 {
    filter.to_attr_computed()
}

/// Decode a CardFilter from packed 64-bit format (legacy)
pub fn decode_filter(attr: i64) -> CardFilter {
    CardFilter::from_attr_legacy(attr)
}

/// Encode DecodedSlot to packed i32 format (legacy)
pub fn encode_slot(
    target_slot: u8,
    comparison: u8,
    source_zone: Zone,
    dest_zone: Zone,
    remainder_zone: u8,
    area_idx: u8,
    is_opponent: bool,
    is_reveal_until_live: bool,
    is_baton_slot: bool,
    is_empty_slot: bool,
    is_wait: bool,
    is_dynamic: bool,
) -> i32 {
    let mut s = 0u32;
    s |= (target_slot as u32 & S_STANDARD_TARGET_SLOT_MASK as u32) << S_STANDARD_TARGET_SLOT_SHIFT;
    s |= (comparison as u32 & 0x0F) << 4;
    s |= (remainder_zone as u32 & S_STANDARD_REMAINDER_ZONE_MASK as u32)
        << S_STANDARD_REMAINDER_ZONE_SHIFT;
    s |= (source_zone as u8 as u32 & S_STANDARD_SOURCE_ZONE_MASK as u32) << S_STANDARD_SOURCE_ZONE_SHIFT;
    s |= (dest_zone as u8 as u32 & S_STANDARD_DEST_ZONE_MASK as u32) << S_STANDARD_DEST_ZONE_SHIFT;
    s |= (area_idx as u32 & S_STANDARD_AREA_IDX_MASK as u32) << S_STANDARD_AREA_IDX_SHIFT;
    if is_opponent {
        s |= 1 << S_STANDARD_IS_OPPONENT_SHIFT;
    }
    if is_reveal_until_live {
        s |= 1 << S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT;
    }
    if is_baton_slot {
        s |= 1 << S_STANDARD_IS_BATON_SLOT_SHIFT;
    }
    if is_empty_slot {
        s |= 1 << S_STANDARD_IS_EMPTY_SLOT_SHIFT;
    }
    if is_wait {
        s |= 1 << S_STANDARD_IS_WAIT_SHIFT;
    }
    if is_dynamic {
        s |= 1 << S_STANDARD_IS_DYNAMIC_SHIFT;
    }
    s as i32
}

/// Decode slot fields from packed i32 format (legacy)
pub fn decode_slot(raw_s: i32) -> DecodedSlotFields {
    let s = raw_s as u32;
    DecodedSlotFields {
        target_slot: ((s >> S_STANDARD_TARGET_SLOT_SHIFT) & S_STANDARD_TARGET_SLOT_MASK as u32) as u8,
        comparison: ((s >> 4) & 0x0F) as u8,
        remainder_zone: ((s >> S_STANDARD_REMAINDER_ZONE_SHIFT) & S_STANDARD_REMAINDER_ZONE_MASK as u32) as u8,
        source_zone_val: ((s >> S_STANDARD_SOURCE_ZONE_SHIFT) & S_STANDARD_SOURCE_ZONE_MASK as u32) as u8,
        dest_zone_val: ((s >> S_STANDARD_DEST_ZONE_SHIFT) & S_STANDARD_DEST_ZONE_MASK as u32) as u8,
        area_idx: ((s >> S_STANDARD_AREA_IDX_SHIFT) & S_STANDARD_AREA_IDX_MASK as u32) as u8,
        is_opponent: ((s >> S_STANDARD_IS_OPPONENT_SHIFT) & S_STANDARD_IS_OPPONENT_MASK as u32) != 0,
        is_reveal_until_live: ((s >> S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT)
            & S_STANDARD_IS_REVEAL_UNTIL_LIVE_MASK as u32)
            != 0,
        is_baton_slot: ((s >> S_STANDARD_IS_BATON_SLOT_SHIFT) & S_STANDARD_IS_BATON_SLOT_MASK as u32)
            != 0,
        is_empty_slot: ((s >> S_STANDARD_IS_EMPTY_SLOT_SHIFT) & S_STANDARD_IS_EMPTY_SLOT_MASK as u32)
            != 0,
        is_wait: ((s >> S_STANDARD_IS_WAIT_SHIFT) & S_STANDARD_IS_WAIT_MASK as u32) != 0,
        is_dynamic: ((s >> S_STANDARD_IS_DYNAMIC_SHIFT) & S_STANDARD_IS_DYNAMIC_MASK as u32) != 0,
    }
}

/// Struct to hold decoded slot fields (legacy)
pub struct DecodedSlotFields {
    pub target_slot: u8,
    pub comparison: u8,
    pub remainder_zone: u8,
    pub source_zone_val: u8,
    pub dest_zone_val: u8,
    pub area_idx: u8,
    pub is_opponent: bool,
    pub is_reveal_until_live: bool,
    pub is_baton_slot: bool,
    pub is_empty_slot: bool,
    pub is_wait: bool,
    pub is_dynamic: bool,
}

/// Encode LookAndChoose value to packed i32 (legacy)
pub fn encode_look_and_choose(
    count: u8,
    _choose_count: u8, // not represented in legacy format
    char_id_1: u8,
    char_id_2: u8,
    char_id_3: u8,
    reveal: bool,
    dest_discard: bool,
) -> i32 {
    let mut v = 0u32;
    v |= (count as u32 & V_LOOK_CHOOSE_COUNT_MASK) << V_LOOK_CHOOSE_COUNT_SHIFT;
    v |= (char_id_1 as u32 & V_LOOK_CHOOSE_CHAR_ID_1_MASK) << V_LOOK_CHOOSE_CHAR_ID_1_SHIFT;
    v |= (char_id_2 as u32 & V_LOOK_CHOOSE_CHAR_ID_2_MASK) << V_LOOK_CHOOSE_CHAR_ID_2_SHIFT;
    v |= (char_id_3 as u32 & V_LOOK_CHOOSE_CHAR_ID_3_MASK) << V_LOOK_CHOOSE_CHAR_ID_3_SHIFT;
    if reveal {
        v |= 1 << V_LOOK_CHOOSE_REVEAL_SHIFT;
    }
    if dest_discard {
        v |= 1 << V_LOOK_CHOOSE_DEST_DISCARD_SHIFT;
    }
    v as i32
}

/// Decode LookAndChoose fields from packed i32 (legacy)
/// Note: choose_count is NOT in the legacy format, always returns 0
pub fn decode_look_and_choose(v: i32) -> LookAndChooseFields {
    let uv = v as u32;
    LookAndChooseFields {
        count: ((uv >> V_LOOK_CHOOSE_COUNT_SHIFT) & V_LOOK_CHOOSE_COUNT_MASK) as u8,
        choose_count: 0, // not in legacy format
        char_id_1: ((uv >> V_LOOK_CHOOSE_CHAR_ID_1_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_1_MASK) as u8,
        char_id_2: ((uv >> V_LOOK_CHOOSE_CHAR_ID_2_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_2_MASK) as u8,
        char_id_3: ((uv >> V_LOOK_CHOOSE_CHAR_ID_3_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_3_MASK) as u8,
        reveal: ((uv >> V_LOOK_CHOOSE_REVEAL_SHIFT) & V_LOOK_CHOOSE_REVEAL_MASK) != 0,
        dest_discard: ((uv >> V_LOOK_CHOOSE_DEST_DISCARD_SHIFT) & V_LOOK_CHOOSE_DEST_DISCARD_MASK)
            != 0,
    }
}

/// Struct to hold decoded LookAndChoose fields (legacy)
pub struct LookAndChooseFields {
    pub count: u8,
    pub choose_count: u8,
    pub char_id_1: u8,
    pub char_id_2: u8,
    pub char_id_3: u8,
    pub reveal: bool,
    pub dest_discard: bool,
}

/// Encode HeartCounts to packed i32 (legacy)
pub fn encode_heart_counts(
    pink: u8,
    red: u8,
    yellow: u8,
    green: u8,
    blue: u8,
    purple: u8,
    any: u8,
) -> i32 {
    let mut v = 0u32;
    v |= (pink as u32 & V_HEART_COUNTS_PINK_MASK) << V_HEART_COUNTS_PINK_SHIFT;
    v |= (red as u32 & V_HEART_COUNTS_RED_MASK) << V_HEART_COUNTS_RED_SHIFT;
    v |= (yellow as u32 & V_HEART_COUNTS_YELLOW_MASK) << V_HEART_COUNTS_YELLOW_SHIFT;
    v |= (green as u32 & V_HEART_COUNTS_GREEN_MASK) << V_HEART_COUNTS_GREEN_SHIFT;
    v |= (blue as u32 & V_HEART_COUNTS_BLUE_MASK) << V_HEART_COUNTS_BLUE_SHIFT;
    v |= (purple as u32 & V_HEART_COUNTS_PURPLE_MASK) << V_HEART_COUNTS_PURPLE_SHIFT;
    v |= (any as u32 & V_HEART_COUNTS_ANY_MASK) << V_HEART_COUNTS_ANY_SHIFT;
    v as i32
}

/// Decode HeartCounts fields from packed i32 (legacy)
pub fn decode_heart_counts(v: i32) -> HeartCountsFields {
    let uv = v as u32;
    HeartCountsFields {
        pink: ((uv >> V_HEART_COUNTS_PINK_SHIFT) & V_HEART_COUNTS_PINK_MASK) as u8,
        red: ((uv >> V_HEART_COUNTS_RED_SHIFT) & V_HEART_COUNTS_RED_MASK) as u8,
        yellow: ((uv >> V_HEART_COUNTS_YELLOW_SHIFT) & V_HEART_COUNTS_YELLOW_MASK) as u8,
        green: ((uv >> V_HEART_COUNTS_GREEN_SHIFT) & V_HEART_COUNTS_GREEN_MASK) as u8,
        blue: ((uv >> V_HEART_COUNTS_BLUE_SHIFT) & V_HEART_COUNTS_BLUE_MASK) as u8,
        purple: ((uv >> V_HEART_COUNTS_PURPLE_SHIFT) & V_HEART_COUNTS_PURPLE_MASK) as u8,
        any: ((uv >> V_HEART_COUNTS_ANY_SHIFT) & V_HEART_COUNTS_ANY_MASK) as u8,
    }
}

/// Struct to hold decoded HeartCounts fields (legacy)
pub struct HeartCountsFields {
    pub pink: u8,
    pub red: u8,
    pub yellow: u8,
    pub green: u8,
    pub blue: u8,
    pub purple: u8,
    pub any: u8,
}

/// Encode HeartRequirements to packed i64 (legacy)
pub fn encode_heart_requirements(reqs: [u8; 8]) -> i64 {
    let mut a = 0u64;
    a |= (reqs[0] as u64 & A_HEART_COST_REQ_1_MASK) << A_HEART_COST_REQ_1_SHIFT;
    a |= (reqs[1] as u64 & A_HEART_COST_REQ_2_MASK) << A_HEART_COST_REQ_2_SHIFT;
    a |= (reqs[2] as u64 & A_HEART_COST_REQ_3_MASK) << A_HEART_COST_REQ_3_SHIFT;
    a |= (reqs[3] as u64 & A_HEART_COST_REQ_4_MASK) << A_HEART_COST_REQ_4_SHIFT;
    a |= (reqs[4] as u64 & A_HEART_COST_REQ_5_MASK) << A_HEART_COST_REQ_5_SHIFT;
    a |= (reqs[5] as u64 & A_HEART_COST_REQ_6_MASK) << A_HEART_COST_REQ_6_SHIFT;
    a |= (reqs[6] as u64 & A_HEART_COST_REQ_7_MASK) << A_HEART_COST_REQ_7_SHIFT;
    a |= (reqs[7] as u64 & A_HEART_COST_REQ_8_MASK) << A_HEART_COST_REQ_8_SHIFT;
    a as i64
}

/// Decode HeartRequirements fields from packed i64 (legacy)
pub fn decode_heart_requirements(a: i64) -> [u8; 8] {
    let ua = a as u64;
    [
        ((ua >> A_HEART_COST_REQ_1_SHIFT) & A_HEART_COST_REQ_1_MASK) as u8,
        ((ua >> A_HEART_COST_REQ_2_SHIFT) & A_HEART_COST_REQ_2_MASK) as u8,
        ((ua >> A_HEART_COST_REQ_3_SHIFT) & A_HEART_COST_REQ_3_MASK) as u8,
        ((ua >> A_HEART_COST_REQ_4_SHIFT) & A_HEART_COST_REQ_4_MASK) as u8,
        ((ua >> A_HEART_COST_REQ_5_SHIFT) & A_HEART_COST_REQ_5_MASK) as u8,
        ((ua >> A_HEART_COST_REQ_6_SHIFT) & A_HEART_COST_REQ_6_MASK) as u8,
        ((ua >> A_HEART_COST_REQ_7_SHIFT) & A_HEART_COST_REQ_7_MASK) as u8,
        ((ua >> A_HEART_COST_REQ_8_SHIFT) & A_HEART_COST_REQ_8_MASK) as u8,
    ]
}
