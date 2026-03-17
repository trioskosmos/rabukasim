use crate::core::enums::Zone;
use crate::core::generated_layout::*;
use crate::core::generated_constants::*;

#[derive(Debug, Clone, Copy, Default)]
pub struct DecodedSlot {
    pub target_slot: u8,
    pub source_zone: Zone,
    pub dest_zone: Zone,
    pub remainder_zone: u8,
    pub is_opponent: bool,
    pub is_reveal_until_live: bool,
    pub is_baton_slot: bool,
    pub is_empty_slot: bool,
    pub is_wait: bool,
    pub is_dynamic: bool,
    pub area_idx: u8,
}

impl DecodedSlot {
    pub fn decode(raw_s: i32) -> Self {
        let s = raw_s as u32;
        let source_zone_val = ((s >> S_STANDARD_SOURCE_ZONE_SHIFT) & S_STANDARD_SOURCE_ZONE_MASK as u32) as u8;
        let dest_zone_val = ((s >> S_STANDARD_DEST_ZONE_SHIFT) & S_STANDARD_DEST_ZONE_MASK as u32) as u8;

        Self {
            target_slot: ((s >> S_STANDARD_TARGET_SLOT_SHIFT) & S_STANDARD_TARGET_SLOT_MASK as u32) as u8,
            remainder_zone: ((s >> S_STANDARD_REMAINDER_ZONE_SHIFT) & S_STANDARD_REMAINDER_ZONE_MASK as u32) as u8,
            source_zone: Self::decode_zone(source_zone_val),
            dest_zone: Self::decode_zone(dest_zone_val),
            area_idx: ((s >> S_STANDARD_AREA_IDX_SHIFT) & S_STANDARD_AREA_IDX_MASK as u32) as u8,
            is_opponent: ((s >> S_STANDARD_IS_OPPONENT_SHIFT) & S_STANDARD_IS_OPPONENT_MASK as u32) != 0,
            is_reveal_until_live: ((s >> S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT) & S_STANDARD_IS_REVEAL_UNTIL_LIVE_MASK as u32) != 0,
            is_baton_slot: ((s >> S_STANDARD_IS_BATON_SLOT_SHIFT) & S_STANDARD_IS_BATON_SLOT_MASK as u32) != 0,
            is_empty_slot: ((s >> S_STANDARD_IS_EMPTY_SLOT_SHIFT) & S_STANDARD_IS_EMPTY_SLOT_MASK as u32) != 0,
            is_wait: ((s >> S_STANDARD_IS_WAIT_SHIFT) & S_STANDARD_IS_WAIT_MASK as u32) != 0,
            is_dynamic: ((s >> S_STANDARD_IS_DYNAMIC_SHIFT) & S_STANDARD_IS_DYNAMIC_MASK as u32) != 0,
        }
    }

    fn decode_zone(val: u8) -> Zone {
        let v = val as i32;
        if v == ZONE_DECK_TOP { Zone::DeckTop }
        else if v == ZONE_DECK_BOTTOM { Zone::DeckBottom }
        else if v == ZONE_ENERGY { Zone::Energy }
        else if v == ZONE_STAGE { Zone::Stage }
        else if v == ZONE_HAND { Zone::Hand }
        else if v == ZONE_DISCARD { Zone::Discard }
        else if v == ZONE_DECK { Zone::Deck }
        else if v == ZONE_LIVE_SET { Zone::LiveSet }
        else if v == ZONE_SUCCESS_PILE { Zone::SuccessPile }
        else if v == ZONE_YELL { Zone::Yell }
        else { Zone::Default }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DecodedHeartCounts {
    pub pink: u8,
    pub red: u8,
    pub yellow: u8,
    pub green: u8,
    pub blue: u8,
    pub purple: u8,
    pub any: u8,
}

impl DecodedHeartCounts {
    pub fn decode(v: i32) -> Self {
        let uv = v as u32;
        Self {
            pink: ((uv >> V_HEART_COUNTS_PINK_SHIFT) & V_HEART_COUNTS_PINK_MASK) as u8,
            red: ((uv >> V_HEART_COUNTS_RED_SHIFT) & V_HEART_COUNTS_RED_MASK) as u8,
            yellow: ((uv >> V_HEART_COUNTS_YELLOW_SHIFT) & V_HEART_COUNTS_YELLOW_MASK) as u8,
            green: ((uv >> V_HEART_COUNTS_GREEN_SHIFT) & V_HEART_COUNTS_GREEN_MASK) as u8,
            blue: ((uv >> V_HEART_COUNTS_BLUE_SHIFT) & V_HEART_COUNTS_BLUE_MASK) as u8,
            purple: ((uv >> V_HEART_COUNTS_PURPLE_SHIFT) & V_HEART_COUNTS_PURPLE_MASK) as u8,
            any: ((uv >> V_HEART_COUNTS_ANY_SHIFT) & V_HEART_COUNTS_ANY_MASK) as u8,
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DecodedLookAndChoose {
    pub count: u8,
    pub char_id_1: u8,
    pub char_id_2: u8,
    pub char_id_3: u8,
    pub reveal: bool,
    pub dest_discard: bool,
}

impl DecodedLookAndChoose {
    pub fn decode(v: i32) -> Self {
        let uv = v as u32;
        Self {
            count: ((uv >> V_LOOK_CHOOSE_COUNT_SHIFT) & V_LOOK_CHOOSE_COUNT_MASK) as u8,
            char_id_1: ((uv >> V_LOOK_CHOOSE_CHAR_ID_1_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_1_MASK) as u8,
            char_id_2: ((uv >> V_LOOK_CHOOSE_CHAR_ID_2_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_2_MASK) as u8,
            char_id_3: ((uv >> V_LOOK_CHOOSE_CHAR_ID_3_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_3_MASK) as u8,
            reveal: ((uv >> V_LOOK_CHOOSE_REVEAL_SHIFT) & V_LOOK_CHOOSE_REVEAL_MASK) != 0,
            dest_discard: ((uv >> V_LOOK_CHOOSE_DEST_DISCARD_SHIFT) & V_LOOK_CHOOSE_DEST_DISCARD_MASK) != 0,
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DecodedHeartRequirements {
    pub reqs: [u8; 8],
}

impl DecodedHeartRequirements {
    pub fn decode(a: i64) -> Self {
        let ua = a as u64;
        Self {
            reqs: [
                ((ua >> A_HEART_COST_REQ_1_SHIFT) & A_HEART_COST_REQ_1_MASK) as u8,
                ((ua >> A_HEART_COST_REQ_2_SHIFT) & A_HEART_COST_REQ_2_MASK) as u8,
                ((ua >> A_HEART_COST_REQ_3_SHIFT) & A_HEART_COST_REQ_3_MASK) as u8,
                ((ua >> A_HEART_COST_REQ_4_SHIFT) & A_HEART_COST_REQ_4_MASK) as u8,
                ((ua >> A_HEART_COST_REQ_5_SHIFT) & A_HEART_COST_REQ_5_MASK) as u8,
                ((ua >> A_HEART_COST_REQ_6_SHIFT) & A_HEART_COST_REQ_6_MASK) as u8,
                ((ua >> A_HEART_COST_REQ_7_SHIFT) & A_HEART_COST_REQ_7_MASK) as u8,
                ((ua >> A_HEART_COST_REQ_8_SHIFT) & A_HEART_COST_REQ_8_MASK) as u8,
            ],
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DecodedFilterAttr {
    pub target_player: u8,
    pub card_type: u8,
    pub group_enabled: bool,
    pub group_id: u8,
    pub is_tapped: bool,
    pub has_blade_heart: bool,
    pub not_has_blade_heart: bool,
    pub unique_names: bool,
    pub unit_enabled: bool,
    pub unit_id: u8,
    pub value_enabled: bool,
    pub value_threshold: u8,
    pub is_le: bool,
    pub is_cost_type: bool,
    pub color_mask: u8,
    pub char_id_1: u8,
    pub char_id_2: u8,
    pub char_id_3: u8,
    pub zone_mask: u8,
    pub special_id: u8,
    pub is_setsuna: bool,
    pub compare_accumulated: bool,
    pub is_optional: bool,
    pub keyword_energy: bool,
    pub keyword_member: bool,
}

impl DecodedFilterAttr {
    pub fn decode(a: i64) -> Self {
        let ua = a as u64;
        Self {
            target_player: ((ua >> A_STANDARD_TARGET_PLAYER_SHIFT) & A_STANDARD_TARGET_PLAYER_MASK) as u8,
            card_type: ((ua >> A_STANDARD_CARD_TYPE_SHIFT) & A_STANDARD_CARD_TYPE_MASK) as u8,
            group_enabled: ((ua >> A_STANDARD_GROUP_ENABLED_SHIFT) & A_STANDARD_GROUP_ENABLED_MASK) != 0,
            group_id: ((ua >> A_STANDARD_GROUP_ID_SHIFT) & A_STANDARD_GROUP_ID_MASK) as u8,
            is_tapped: ((ua >> A_STANDARD_IS_TAPPED_SHIFT) & A_STANDARD_IS_TAPPED_MASK) != 0,
            has_blade_heart: ((ua >> A_STANDARD_HAS_BLADE_HEART_SHIFT) & A_STANDARD_HAS_BLADE_HEART_MASK) != 0,
            not_has_blade_heart: ((ua >> A_STANDARD_NOT_HAS_BLADE_HEART_SHIFT) & A_STANDARD_NOT_HAS_BLADE_HEART_MASK) != 0,
            unique_names: ((ua >> A_STANDARD_UNIQUE_NAMES_SHIFT) & A_STANDARD_UNIQUE_NAMES_MASK) != 0,
            unit_enabled: ((ua >> A_STANDARD_UNIT_ENABLED_SHIFT) & A_STANDARD_UNIT_ENABLED_MASK) != 0,
            unit_id: ((ua >> A_STANDARD_UNIT_ID_SHIFT) & A_STANDARD_UNIT_ID_MASK) as u8,
            value_enabled: ((ua >> A_STANDARD_VALUE_ENABLED_SHIFT) & A_STANDARD_VALUE_ENABLED_MASK) != 0,
            value_threshold: ((ua >> A_STANDARD_VALUE_THRESHOLD_SHIFT) & A_STANDARD_VALUE_THRESHOLD_MASK) as u8,
            is_le: ((ua >> A_STANDARD_IS_LE_SHIFT) & A_STANDARD_IS_LE_MASK) != 0,
            is_cost_type: ((ua >> A_STANDARD_IS_COST_TYPE_SHIFT) & A_STANDARD_IS_COST_TYPE_MASK) != 0,
            color_mask: ((ua >> A_STANDARD_COLOR_MASK_SHIFT) & A_STANDARD_COLOR_MASK_MASK) as u8,
            char_id_1: ((ua >> A_STANDARD_CHAR_ID_1_SHIFT) & A_STANDARD_CHAR_ID_1_MASK) as u8,
            char_id_2: ((ua >> A_STANDARD_CHAR_ID_2_SHIFT) & A_STANDARD_CHAR_ID_2_MASK) as u8,
            char_id_3: if ((ua >> A_STANDARD_UNIT_ENABLED_SHIFT) & A_STANDARD_UNIT_ENABLED_MASK) == 0 {
                ((ua >> A_STANDARD_UNIT_ID_SHIFT) & A_STANDARD_UNIT_ID_MASK) as u8
            } else {
                0
            },
            zone_mask: ((ua >> A_STANDARD_ZONE_MASK_SHIFT) & A_STANDARD_ZONE_MASK_MASK) as u8,
            special_id: ((ua >> A_STANDARD_SPECIAL_ID_SHIFT) & A_STANDARD_SPECIAL_ID_MASK) as u8,
            is_setsuna: ((ua >> A_STANDARD_IS_SETSUNA_SHIFT) & A_STANDARD_IS_SETSUNA_MASK) != 0,
            compare_accumulated: ((ua >> A_STANDARD_COMPARE_ACCUMULATED_SHIFT) & A_STANDARD_COMPARE_ACCUMULATED_MASK) != 0,
            is_optional: ((ua >> A_STANDARD_IS_OPTIONAL_SHIFT) & A_STANDARD_IS_OPTIONAL_MASK) != 0,
            keyword_energy: ((ua >> A_STANDARD_KEYWORD_ENERGY_SHIFT) & A_STANDARD_KEYWORD_ENERGY_MASK) != 0,
            keyword_member: ((ua >> A_STANDARD_KEYWORD_MEMBER_SHIFT) & A_STANDARD_KEYWORD_MEMBER_MASK) != 0,
        }
    }

    pub fn to_attr(&self) -> u64 {
        let mut a: u64 = 0;
        a |= (self.target_player as u64 & A_STANDARD_TARGET_PLAYER_MASK) << A_STANDARD_TARGET_PLAYER_SHIFT;
        a |= (self.card_type as u64 & A_STANDARD_CARD_TYPE_MASK) << A_STANDARD_CARD_TYPE_SHIFT;
        if self.group_enabled {
            a |= 1 << A_STANDARD_GROUP_ENABLED_SHIFT;
            a |= (self.group_id as u64 & A_STANDARD_GROUP_ID_MASK) << A_STANDARD_GROUP_ID_SHIFT;
        }
        if self.is_tapped { a |= 1 << A_STANDARD_IS_TAPPED_SHIFT; }
        if self.has_blade_heart { a |= 1 << A_STANDARD_HAS_BLADE_HEART_SHIFT; }
        if self.not_has_blade_heart { a |= 1 << A_STANDARD_NOT_HAS_BLADE_HEART_SHIFT; }
        if self.unique_names { a |= 1 << A_STANDARD_UNIQUE_NAMES_SHIFT; }
        if self.unit_enabled {
            a |= 1 << A_STANDARD_UNIT_ENABLED_SHIFT;
            a |= (self.unit_id as u64 & A_STANDARD_UNIT_ID_MASK) << A_STANDARD_UNIT_ID_SHIFT;
        }
        if self.value_enabled {
            a |= 1 << A_STANDARD_VALUE_ENABLED_SHIFT;
            a |= (self.value_threshold as u64 & A_STANDARD_VALUE_THRESHOLD_MASK) << A_STANDARD_VALUE_THRESHOLD_SHIFT;
        }
        if self.is_le { a |= 1 << A_STANDARD_IS_LE_SHIFT; }
        if self.is_cost_type { a |= 1 << A_STANDARD_IS_COST_TYPE_SHIFT; }
        a |= (self.color_mask as u64 & A_STANDARD_COLOR_MASK_MASK) << A_STANDARD_COLOR_MASK_SHIFT;
        a |= (self.char_id_1 as u64 & A_STANDARD_CHAR_ID_1_MASK) << A_STANDARD_CHAR_ID_1_SHIFT;
        a |= (self.char_id_2 as u64 & A_STANDARD_CHAR_ID_2_MASK) << A_STANDARD_CHAR_ID_2_SHIFT;
        a |= (self.zone_mask as u64 & A_STANDARD_ZONE_MASK_MASK) << A_STANDARD_ZONE_MASK_SHIFT;
        if self.is_setsuna { a |= 1 << A_STANDARD_IS_SETSUNA_SHIFT; }
        if self.compare_accumulated { a |= 1 << A_STANDARD_COMPARE_ACCUMULATED_SHIFT; }
        if self.is_optional { a |= 1 << A_STANDARD_IS_OPTIONAL_SHIFT; }
        if self.keyword_energy { a |= 1 << A_STANDARD_KEYWORD_ENERGY_SHIFT; }
        if self.keyword_member { a |= 1 << A_STANDARD_KEYWORD_MEMBER_SHIFT; }
        a
    }
}

#[derive(Debug, Clone, Copy)]
pub struct BytecodeInstruction {
    pub op: i32,
    pub v: i32,
    pub a: i64,
    pub raw_s: i32,
}

impl BytecodeInstruction {
    pub fn new(op: i32, v: i32, a: i64, raw_s: i32) -> Self {
        Self {
            op,
            v,
            a,
            raw_s,
        }
    }

    pub fn decode(bytecode: &[i32], ip: usize) -> Self {
        let op = bytecode[ip];
        let v = if ip + 1 < bytecode.len() { bytecode[ip + 1] } else { 0 };
        let a_low = if ip + 2 < bytecode.len() { bytecode[ip + 2] } else { 0 } as u32;
        let a_high = if ip + 3 < bytecode.len() { bytecode[ip + 3] } else { 0 } as u32;
        let raw_s = if ip + 4 < bytecode.len() { bytecode[ip + 4] } else { 0 };

        let a = ((a_high as i64) << 32) | (a_low as i64);

        Self {
            op,
            v,
            a,
            raw_s,
        }
    }

    pub fn slot(&self) -> DecodedSlot {
        DecodedSlot::decode(self.raw_s)
    }

    pub fn heart_counts(&self) -> DecodedHeartCounts {
        DecodedHeartCounts::decode(self.v)
    }

    pub fn look_choose(&self) -> DecodedLookAndChoose {
        DecodedLookAndChoose::decode(self.v)
    }

    pub fn heart_requirements(&self) -> DecodedHeartRequirements {
        DecodedHeartRequirements::decode(self.a)
    }

    pub fn filter_attr(&self) -> DecodedFilterAttr {
        DecodedFilterAttr::decode(self.a)
    }
}
