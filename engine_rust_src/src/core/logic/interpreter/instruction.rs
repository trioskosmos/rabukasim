use crate::core::enums::Zone;
use crate::core::generated_constants::*;
use crate::core::generated_layout::*;
use crate::core::logic::filter::CardFilter;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::sync::Arc;

pub const WORDS_PER_INSTRUCTION: usize = 5;
const LAYOUT_TAG_MASK: u32 = 0xF000_0000;
const COMPACT_HEADER_FLAG: u32 = 0x8000_0000;
const TAGGED_HEADER_FLAG: u32 = 0x9000_0000;
const COMPACT_HAS_V_FLAG: u32 = 1 << 16;
const COMPACT_HAS_A_FLAG: u32 = 1 << 17;
const COMPACT_HAS_S_FLAG: u32 = 1 << 18;
const COMPACT_WIDE_A_FLAG: u32 = 1 << 19;
const TAGGED_OPERAND_COUNT_SHIFT: u32 = 16;
const TAGGED_OPERAND_COUNT_MASK: u32 = 0xFF;
const OPERAND_HEADER_TAG_MASK: u32 = 0xFF;
const OPERAND_HEADER_WIDE_FLAG: u32 = 1 << 8;

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize, Hash)]
#[serde(from = "DecodedSlotRaw")]
pub struct DecodedSlot {
    pub target_slot: u8,
    pub comparison: u8,
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

#[derive(Deserialize)]
#[serde(untagged)]
enum DecodedSlotRaw {
    Legacy(i32),
    Structured(DecodedSlotStructuredRaw),
}

#[derive(Deserialize, Default)]
struct DecodedSlotStructuredRaw {
    #[serde(default)]
    target_slot: Option<u8>,
    #[serde(default)]
    comparison: Option<u8>,
    #[serde(default)]
    source_zone: Option<Zone>,
    #[serde(default)]
    dest_zone: Option<Zone>,
    #[serde(default)]
    remainder_zone: Option<u8>,
    #[serde(default)]
    is_opponent: Option<Value>,
    #[serde(default)]
    is_reveal_until_live: Option<Value>,
    #[serde(default)]
    is_baton_slot: Option<Value>,
    #[serde(default)]
    is_empty_slot: Option<Value>,
    #[serde(default)]
    is_wait: Option<Value>,
    #[serde(default)]
    is_dynamic: Option<Value>,
    #[serde(default)]
    area_idx: Option<u8>,
}

fn as_bool_robust(v: &Value) -> bool {
    v.as_bool()
        .unwrap_or_else(|| v.as_i64().map(|i| i != 0).unwrap_or(false))
}

impl From<DecodedSlotRaw> for DecodedSlot {
    fn from(raw: DecodedSlotRaw) -> Self {
        match raw {
            DecodedSlotRaw::Legacy(v) => Self::decode(v),
            DecodedSlotRaw::Structured(raw) => Self {
                target_slot: raw.target_slot.unwrap_or_default(),
                comparison: raw.comparison.unwrap_or_default(),
                source_zone: raw.source_zone.unwrap_or_default(),
                dest_zone: raw.dest_zone.unwrap_or_default(),
                remainder_zone: raw.remainder_zone.unwrap_or_default(),
                is_opponent: raw
                    .is_opponent
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                is_reveal_until_live: raw
                    .is_reveal_until_live
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                is_baton_slot: raw
                    .is_baton_slot
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                is_empty_slot: raw
                    .is_empty_slot
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                is_wait: raw.is_wait.map(|v| as_bool_robust(&v)).unwrap_or_default(),
                is_dynamic: raw
                    .is_dynamic
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                area_idx: raw.area_idx.unwrap_or_default(),
            },
        }
    }
}

impl DecodedSlot {
    pub fn decode(raw_s: i32) -> Self {
        let s = raw_s as u32;
        let source_zone_val =
            ((s >> S_STANDARD_SOURCE_ZONE_SHIFT) & S_STANDARD_SOURCE_ZONE_MASK as u32) as u8;
        let dest_zone_val =
            ((s >> S_STANDARD_DEST_ZONE_SHIFT) & S_STANDARD_DEST_ZONE_MASK as u32) as u8;

        Self {
            target_slot: ((s >> S_STANDARD_TARGET_SLOT_SHIFT) & S_STANDARD_TARGET_SLOT_MASK as u32)
                as u8,
            comparison: ((s >> 4) & 0x0F) as u8,
            remainder_zone: ((s >> S_STANDARD_REMAINDER_ZONE_SHIFT)
                & S_STANDARD_REMAINDER_ZONE_MASK as u32) as u8,
            source_zone: Self::decode_zone(source_zone_val),
            dest_zone: Self::decode_zone(dest_zone_val),
            area_idx: ((s >> S_STANDARD_AREA_IDX_SHIFT) & S_STANDARD_AREA_IDX_MASK as u32) as u8,
            is_opponent: ((s >> S_STANDARD_IS_OPPONENT_SHIFT) & S_STANDARD_IS_OPPONENT_MASK as u32)
                != 0,
            is_reveal_until_live: ((s >> S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT)
                & S_STANDARD_IS_REVEAL_UNTIL_LIVE_MASK as u32)
                != 0,
            is_baton_slot: ((s >> S_STANDARD_IS_BATON_SLOT_SHIFT)
                & S_STANDARD_IS_BATON_SLOT_MASK as u32)
                != 0,
            is_empty_slot: ((s >> S_STANDARD_IS_EMPTY_SLOT_SHIFT)
                & S_STANDARD_IS_EMPTY_SLOT_MASK as u32)
                != 0,
            is_wait: ((s >> S_STANDARD_IS_WAIT_SHIFT) & S_STANDARD_IS_WAIT_MASK as u32) != 0,
            is_dynamic: ((s >> S_STANDARD_IS_DYNAMIC_SHIFT) & S_STANDARD_IS_DYNAMIC_MASK as u32)
                != 0,
        }
    }

    fn decode_zone(val: u8) -> Zone {
        let v = val as i32;
        if v == ZONE_DECK_TOP {
            Zone::DeckTop
        } else if v == ZONE_DECK_BOTTOM {
            Zone::DeckBottom
        } else if v == ZONE_ENERGY {
            Zone::Energy
        } else if v == ZONE_STAGE {
            Zone::Stage
        } else if v == ZONE_HAND {
            Zone::Hand
        } else if v == ZONE_DISCARD {
            Zone::Discard
        } else if v == ZONE_DECK {
            Zone::Deck
        } else if v == ZONE_LIVE_SET {
            Zone::LiveSet
        } else if v == ZONE_SUCCESS_PILE {
            Zone::SuccessPile
        } else if v == ZONE_YELL {
            Zone::Yell
        } else {
            Zone::Default
        }
    }

    pub fn to_raw(&self) -> i32 {
        let mut s = 0u32;
        s |= (self.target_slot as u32 & S_STANDARD_TARGET_SLOT_MASK as u32)
            << S_STANDARD_TARGET_SLOT_SHIFT;
        s |= (self.comparison as u32 & 0x0F) << 4;
        s |= (self.remainder_zone as u32 & S_STANDARD_REMAINDER_ZONE_MASK as u32)
            << S_STANDARD_REMAINDER_ZONE_SHIFT;
        s |= (self.source_zone as u8 as u32 & S_STANDARD_SOURCE_ZONE_MASK as u32)
            << S_STANDARD_SOURCE_ZONE_SHIFT;
        s |= (self.dest_zone as u8 as u32 & S_STANDARD_DEST_ZONE_MASK as u32)
            << S_STANDARD_DEST_ZONE_SHIFT;
        s |= (self.area_idx as u32 & S_STANDARD_AREA_IDX_MASK as u32) << S_STANDARD_AREA_IDX_SHIFT;
        if self.is_opponent {
            s |= 1 << S_STANDARD_IS_OPPONENT_SHIFT;
        }
        if self.is_reveal_until_live {
            s |= 1 << S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT;
        }
        if self.is_baton_slot {
            s |= 1 << S_STANDARD_IS_BATON_SLOT_SHIFT;
        }
        if self.is_empty_slot {
            s |= 1 << S_STANDARD_IS_EMPTY_SLOT_SHIFT;
        }
        if self.is_wait {
            s |= 1 << S_STANDARD_IS_WAIT_SHIFT;
        }
        if self.is_dynamic {
            s |= 1 << S_STANDARD_IS_DYNAMIC_SHIFT;
        }
        s as i32
    }
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize, Hash)]
#[serde(from = "DecodedHeartCountsRaw")]
pub struct DecodedHeartCounts {
    pub pink: u8,
    pub red: u8,
    pub yellow: u8,
    pub green: u8,
    pub blue: u8,
    pub purple: u8,
    pub any: u8,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum DecodedHeartCountsRaw {
    Legacy(i32),
    Structured {
        pink: u8,
        red: u8,
        yellow: u8,
        green: u8,
        blue: u8,
        purple: u8,
        any: u8,
    },
}

impl From<DecodedHeartCountsRaw> for DecodedHeartCounts {
    fn from(raw: DecodedHeartCountsRaw) -> Self {
        match raw {
            DecodedHeartCountsRaw::Legacy(v) => Self::decode(v),
            DecodedHeartCountsRaw::Structured {
                pink,
                red,
                yellow,
                green,
                blue,
                purple,
                any,
            } => Self {
                pink,
                red,
                yellow,
                green,
                blue,
                purple,
                any,
            },
        }
    }
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

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize, Hash)]
#[serde(from = "DecodedLookAndChooseRaw")]
pub struct DecodedLookAndChoose {
    pub count: u8,
    #[serde(default)]
    pub choose_count: u8,
    pub char_id_1: u8,
    pub char_id_2: u8,
    pub char_id_3: u8,
    pub reveal: bool,
    pub dest_discard: bool,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum DecodedLookAndChooseRaw {
    Legacy(i32),
    Structured {
        count: u8,
        #[serde(default)]
        choose_count: u8,
        char_id_1: u8,
        char_id_2: u8,
        char_id_3: u8,
        reveal: bool,
        dest_discard: bool,
    },
}

impl From<DecodedLookAndChooseRaw> for DecodedLookAndChoose {
    fn from(raw: DecodedLookAndChooseRaw) -> Self {
        match raw {
            DecodedLookAndChooseRaw::Legacy(v) => Self::decode(v),
            DecodedLookAndChooseRaw::Structured {
                count,
                choose_count,
                char_id_1,
                char_id_2,
                char_id_3,
                reveal,
                dest_discard,
            } => Self {
                count,
                choose_count,
                char_id_1,
                char_id_2,
                char_id_3,
                reveal,
                dest_discard,
            },
        }
    }
}

impl DecodedLookAndChoose {
    pub fn decode(v: i32) -> Self {
        let uv = v as u32;
        Self {
            count: ((uv >> V_LOOK_CHOOSE_COUNT_SHIFT) & V_LOOK_CHOOSE_COUNT_MASK) as u8,
            choose_count: 0,
            char_id_1: ((uv >> V_LOOK_CHOOSE_CHAR_ID_1_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_1_MASK) as u8,
            char_id_2: ((uv >> V_LOOK_CHOOSE_CHAR_ID_2_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_2_MASK) as u8,
            char_id_3: ((uv >> V_LOOK_CHOOSE_CHAR_ID_3_SHIFT) & V_LOOK_CHOOSE_CHAR_ID_3_MASK) as u8,
            reveal: ((uv >> V_LOOK_CHOOSE_REVEAL_SHIFT) & V_LOOK_CHOOSE_REVEAL_MASK) != 0,
            dest_discard: ((uv >> V_LOOK_CHOOSE_DEST_DISCARD_SHIFT)
                & V_LOOK_CHOOSE_DEST_DISCARD_MASK)
                != 0,
        }
    }

    pub fn to_raw(&self) -> i32 {
        let mut v = 0u32;
        v |= (self.count as u32 & V_LOOK_CHOOSE_COUNT_MASK) << V_LOOK_CHOOSE_COUNT_SHIFT;
        v |=
            (self.char_id_1 as u32 & V_LOOK_CHOOSE_CHAR_ID_1_MASK) << V_LOOK_CHOOSE_CHAR_ID_1_SHIFT;
        v |=
            (self.char_id_2 as u32 & V_LOOK_CHOOSE_CHAR_ID_2_MASK) << V_LOOK_CHOOSE_CHAR_ID_2_SHIFT;
        v |=
            (self.char_id_3 as u32 & V_LOOK_CHOOSE_CHAR_ID_3_MASK) << V_LOOK_CHOOSE_CHAR_ID_3_SHIFT;
        if self.reveal {
            v |= 1 << V_LOOK_CHOOSE_REVEAL_SHIFT;
        }
        if self.dest_discard {
            v |= 1 << V_LOOK_CHOOSE_DEST_DISCARD_SHIFT;
        }
        v as i32
    }
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize, Hash)]
#[serde(from = "DecodedHeartRequirementsRaw")]
pub struct DecodedHeartRequirements {
    pub reqs: [u8; 8],
}

#[derive(Deserialize)]
#[serde(untagged)]
enum DecodedHeartRequirementsRaw {
    Legacy(i64),
    Structured { reqs: [u8; 8] },
}

impl From<DecodedHeartRequirementsRaw> for DecodedHeartRequirements {
    fn from(raw: DecodedHeartRequirementsRaw) -> Self {
        match raw {
            DecodedHeartRequirementsRaw::Legacy(v) => Self::decode(v),
            DecodedHeartRequirementsRaw::Structured { reqs } => Self { reqs },
        }
    }
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

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Hash)]
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

impl<'de> Deserialize<'de> for DecodedFilterAttr {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let value = serde_json::Value::deserialize(deserializer)?;

        let Some(map) = value.as_object() else {
            return Ok(Self::default());
        };

        fn get_u8(map: &serde_json::Map<String, serde_json::Value>, key: &str) -> u8 {
            map.get(key)
                .and_then(|value| value.as_u64())
                .unwrap_or_default() as u8
        }

        fn get_bool(map: &serde_json::Map<String, serde_json::Value>, key: &str) -> bool {
            map.get(key)
                .and_then(|value| value.as_bool())
                .unwrap_or_default()
        }

        Ok(Self {
            target_player: get_u8(map, "target_player"),
            card_type: get_u8(map, "card_type"),
            group_enabled: get_bool(map, "group_enabled"),
            group_id: get_u8(map, "group_id"),
            is_tapped: get_bool(map, "is_tapped"),
            has_blade_heart: get_bool(map, "has_blade_heart"),
            not_has_blade_heart: get_bool(map, "not_has_blade_heart"),
            unique_names: get_bool(map, "unique_names"),
            unit_enabled: get_bool(map, "unit_enabled"),
            unit_id: get_u8(map, "unit_id"),
            value_enabled: get_bool(map, "value_enabled"),
            value_threshold: get_u8(map, "value_threshold"),
            is_le: get_bool(map, "is_le"),
            is_cost_type: get_bool(map, "is_cost_type"),
            color_mask: get_u8(map, "color_mask"),
            char_id_1: get_u8(map, "char_id_1"),
            char_id_2: get_u8(map, "char_id_2"),
            char_id_3: get_u8(map, "char_id_3"),
            zone_mask: get_u8(map, "zone_mask"),
            special_id: get_u8(map, "special_id"),
            is_setsuna: get_bool(map, "is_setsuna"),
            compare_accumulated: get_bool(map, "compare_accumulated"),
            is_optional: get_bool(map, "is_optional"),
            keyword_energy: get_bool(map, "keyword_energy"),
            keyword_member: get_bool(map, "keyword_member"),
        })
    }
}

#[derive(Deserialize)]
#[serde(untagged)]
enum DecodedFilterAttrRaw {
    Legacy(i64),
    Structured(DecodedFilterAttrStructuredRaw),
}

#[derive(Deserialize)]
struct DecodedFilterAttrStructuredRaw {
    #[serde(default)]
    target_player: Option<u8>,
    #[serde(default)]
    card_type: Option<u8>,
    #[serde(default)]
    group_enabled: Option<Value>,
    #[serde(default)]
    group_id: Option<u8>,
    #[serde(default)]
    is_tapped: Option<Value>,
    #[serde(default)]
    has_blade_heart: Option<Value>,
    #[serde(default)]
    not_has_blade_heart: Option<Value>,
    #[serde(default)]
    unique_names: Option<Value>,
    #[serde(default)]
    unit_enabled: Option<Value>,
    #[serde(default)]
    unit_id: Option<u8>,
    #[serde(default)]
    value_enabled: Option<Value>,
    #[serde(default)]
    value_threshold: Option<u8>,
    #[serde(default)]
    is_le: Option<Value>,
    #[serde(default)]
    is_cost_type: Option<Value>,
    #[serde(default)]
    color_mask: Option<u8>,
    #[serde(default)]
    char_id_1: Option<u8>,
    #[serde(default)]
    char_id_2: Option<u8>,
    #[serde(default)]
    char_id_3: Option<u8>,
    #[serde(default)]
    zone_mask: Option<u8>,
    #[serde(default)]
    special_id: Option<Value>,
    #[serde(default)]
    is_setsuna: Option<Value>,
    #[serde(default)]
    compare_accumulated: Option<Value>,
    #[serde(default)]
    is_optional: Option<Value>,
    #[serde(default)]
    keyword_energy: Option<Value>,
    #[serde(default)]
    keyword_member: Option<Value>,
}

impl From<DecodedFilterAttrRaw> for DecodedFilterAttr {
    fn from(raw: DecodedFilterAttrRaw) -> Self {
        match raw {
            DecodedFilterAttrRaw::Legacy(v) => Self::decode(v),
            DecodedFilterAttrRaw::Structured(raw) => Self {
                target_player: raw.target_player.unwrap_or_default(),
                card_type: raw.card_type.unwrap_or_default(),
                group_enabled: raw
                    .group_enabled
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                group_id: raw.group_id.unwrap_or_default(),
                is_tapped: raw
                    .is_tapped
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                has_blade_heart: raw
                    .has_blade_heart
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                not_has_blade_heart: raw
                    .not_has_blade_heart
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                unique_names: raw
                    .unique_names
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                unit_enabled: raw
                    .unit_enabled
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                unit_id: raw.unit_id.unwrap_or_default(),
                value_enabled: raw
                    .value_enabled
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                value_threshold: raw.value_threshold.unwrap_or_default(),
                is_le: raw.is_le.map(|v| as_bool_robust(&v)).unwrap_or_default(),
                is_cost_type: raw
                    .is_cost_type
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                color_mask: raw.color_mask.unwrap_or_default(),
                char_id_1: raw.char_id_1.unwrap_or_default(),
                char_id_2: raw.char_id_2.unwrap_or_default(),
                char_id_3: raw.char_id_3.unwrap_or_default(),
                zone_mask: raw.zone_mask.unwrap_or_default(),
                special_id: raw
                    .special_id
                    .map(|v| {
                        if let Some(s) = v.as_str() {
                            match s.to_uppercase().replace('_', " ").as_str() {
                                "NOT MY" | "NOTMY" => 2,
                                "NOT SELF" | "NOTSELF" => 3,
                                _ => 0,
                            }
                        } else {
                            v.as_u64().unwrap_or_default() as u8
                        }
                    })
                    .unwrap_or_default(),
                is_setsuna: raw
                    .is_setsuna
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                compare_accumulated: raw
                    .compare_accumulated
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                is_optional: raw
                    .is_optional
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                keyword_energy: raw
                    .keyword_energy
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
                keyword_member: raw
                    .keyword_member
                    .map(|v| as_bool_robust(&v))
                    .unwrap_or_default(),
            },
        }
    }
}

impl DecodedFilterAttr {
    pub fn decode(a: i64) -> Self {
        let ua = a as u64;
        Self {
            target_player: ((ua >> A_STANDARD_TARGET_PLAYER_SHIFT) & A_STANDARD_TARGET_PLAYER_MASK)
                as u8,
            card_type: ((ua >> A_STANDARD_CARD_TYPE_SHIFT) & A_STANDARD_CARD_TYPE_MASK) as u8,
            group_enabled: ((ua >> A_STANDARD_GROUP_ENABLED_SHIFT) & A_STANDARD_GROUP_ENABLED_MASK)
                != 0,
            group_id: ((ua >> A_STANDARD_GROUP_ID_SHIFT) & A_STANDARD_GROUP_ID_MASK) as u8,
            is_tapped: ((ua >> A_STANDARD_IS_TAPPED_SHIFT) & A_STANDARD_IS_TAPPED_MASK) != 0,
            has_blade_heart: ((ua >> A_STANDARD_HAS_BLADE_HEART_SHIFT)
                & A_STANDARD_HAS_BLADE_HEART_MASK)
                != 0,
            not_has_blade_heart: ((ua >> A_STANDARD_NOT_HAS_BLADE_HEART_SHIFT)
                & A_STANDARD_NOT_HAS_BLADE_HEART_MASK)
                != 0,
            unique_names: ((ua >> A_STANDARD_UNIQUE_NAMES_SHIFT) & A_STANDARD_UNIQUE_NAMES_MASK)
                != 0,
            unit_enabled: ((ua >> A_STANDARD_UNIT_ENABLED_SHIFT) & A_STANDARD_UNIT_ENABLED_MASK)
                != 0,
            unit_id: ((ua >> A_STANDARD_UNIT_ID_SHIFT) & A_STANDARD_UNIT_ID_MASK) as u8,
            value_enabled: ((ua >> A_STANDARD_VALUE_ENABLED_SHIFT) & A_STANDARD_VALUE_ENABLED_MASK)
                != 0,
            value_threshold: ((ua >> A_STANDARD_VALUE_THRESHOLD_SHIFT)
                & A_STANDARD_VALUE_THRESHOLD_MASK) as u8,
            is_le: ((ua >> A_STANDARD_IS_LE_SHIFT) & A_STANDARD_IS_LE_MASK) != 0,
            is_cost_type: ((ua >> A_STANDARD_IS_COST_TYPE_SHIFT) & A_STANDARD_IS_COST_TYPE_MASK)
                != 0,
            color_mask: ((ua >> A_STANDARD_COLOR_MASK_SHIFT) & A_STANDARD_COLOR_MASK_MASK) as u8,
            char_id_1: ((ua >> A_STANDARD_CHAR_ID_1_SHIFT) & A_STANDARD_CHAR_ID_1_MASK) as u8,
            char_id_2: ((ua >> A_STANDARD_CHAR_ID_2_SHIFT) & A_STANDARD_CHAR_ID_2_MASK) as u8,
            char_id_3: if ((ua >> A_STANDARD_UNIT_ENABLED_SHIFT) & A_STANDARD_UNIT_ENABLED_MASK)
                == 0
            {
                ((ua >> A_STANDARD_UNIT_ID_SHIFT) & A_STANDARD_UNIT_ID_MASK) as u8
            } else {
                0
            },
            zone_mask: ((ua >> A_STANDARD_ZONE_MASK_SHIFT) & A_STANDARD_ZONE_MASK_MASK) as u8,
            special_id: ((ua >> A_STANDARD_SPECIAL_ID_SHIFT) & A_STANDARD_SPECIAL_ID_MASK) as u8,
            is_setsuna: ((ua >> A_STANDARD_IS_SETSUNA_SHIFT) & A_STANDARD_IS_SETSUNA_MASK) != 0,
            compare_accumulated: ((ua >> A_STANDARD_COMPARE_ACCUMULATED_SHIFT)
                & A_STANDARD_COMPARE_ACCUMULATED_MASK)
                != 0,
            is_optional: ((ua >> A_STANDARD_IS_OPTIONAL_SHIFT) & A_STANDARD_IS_OPTIONAL_MASK) != 0,
            keyword_energy: ((ua >> A_STANDARD_KEYWORD_ENERGY_SHIFT)
                & A_STANDARD_KEYWORD_ENERGY_MASK)
                != 0,
            keyword_member: ((ua >> A_STANDARD_KEYWORD_MEMBER_SHIFT)
                & A_STANDARD_KEYWORD_MEMBER_MASK)
                != 0,
        }
    }

    pub fn to_attr(&self) -> u64 {
        let mut a: u64 = 0;
        a |= (self.target_player as u64 & A_STANDARD_TARGET_PLAYER_MASK)
            << A_STANDARD_TARGET_PLAYER_SHIFT;
        a |= (self.card_type as u64 & A_STANDARD_CARD_TYPE_MASK) << A_STANDARD_CARD_TYPE_SHIFT;
        if self.group_enabled {
            a |= 1 << A_STANDARD_GROUP_ENABLED_SHIFT;
            a |= (self.group_id as u64 & A_STANDARD_GROUP_ID_MASK) << A_STANDARD_GROUP_ID_SHIFT;
        }
        if self.is_tapped {
            a |= 1 << A_STANDARD_IS_TAPPED_SHIFT;
        }
        if self.has_blade_heart {
            a |= 1 << A_STANDARD_HAS_BLADE_HEART_SHIFT;
        }
        if self.not_has_blade_heart {
            a |= 1 << A_STANDARD_NOT_HAS_BLADE_HEART_SHIFT;
        }
        if self.unique_names {
            a |= 1 << A_STANDARD_UNIQUE_NAMES_SHIFT;
        }
        if self.unit_enabled {
            a |= 1 << A_STANDARD_UNIT_ENABLED_SHIFT;
            a |= (self.unit_id as u64 & A_STANDARD_UNIT_ID_MASK) << A_STANDARD_UNIT_ID_SHIFT;
        }
        if self.value_enabled {
            a |= 1 << A_STANDARD_VALUE_ENABLED_SHIFT;
            a |= (self.value_threshold as u64 & A_STANDARD_VALUE_THRESHOLD_MASK)
                << A_STANDARD_VALUE_THRESHOLD_SHIFT;
        }
        if self.is_le {
            a |= 1 << A_STANDARD_IS_LE_SHIFT;
        }
        if self.is_cost_type {
            a |= 1 << A_STANDARD_IS_COST_TYPE_SHIFT;
        }
        a |= (self.color_mask as u64 & A_STANDARD_COLOR_MASK_MASK) << A_STANDARD_COLOR_MASK_SHIFT;
        a |= (self.char_id_1 as u64 & A_STANDARD_CHAR_ID_1_MASK) << A_STANDARD_CHAR_ID_1_SHIFT;
        a |= (self.char_id_2 as u64 & A_STANDARD_CHAR_ID_2_MASK) << A_STANDARD_CHAR_ID_2_SHIFT;
        a |= (self.zone_mask as u64 & A_STANDARD_ZONE_MASK_MASK) << A_STANDARD_ZONE_MASK_SHIFT;
        a |= (self.special_id as u64 & A_STANDARD_SPECIAL_ID_MASK) << A_STANDARD_SPECIAL_ID_SHIFT;
        if self.is_setsuna {
            a |= 1 << A_STANDARD_IS_SETSUNA_SHIFT;
        }
        if self.compare_accumulated {
            a |= 1 << A_STANDARD_COMPARE_ACCUMULATED_SHIFT;
        }
        if self.is_optional {
            a |= 1 << A_STANDARD_IS_OPTIONAL_SHIFT;
        }
        if self.keyword_energy {
            a |= 1 << A_STANDARD_KEYWORD_ENERGY_SHIFT;
        }
        if self.keyword_member {
            a |= 1 << A_STANDARD_KEYWORD_MEMBER_SHIFT;
        }
        a
    }
}

impl DecodedFilterAttr {
    pub fn to_card_filter(&self) -> CardFilter {
        CardFilter {
            is_enabled: true,
            target_player: self.target_player,
            card_type: self.card_type,
            group_enabled: self.group_enabled,
            group_id: self.group_id,
            is_tapped: self.is_tapped,
            has_blade_heart: self.has_blade_heart,
            not_has_blade_heart: self.not_has_blade_heart,
            unique_names: self.unique_names,
            unit_enabled: self.unit_enabled,
            unit_id: self.unit_id,
            value_enabled: self.value_enabled,
            value_threshold: self.value_threshold,
            is_le: self.is_le,
            is_cost_type: self.is_cost_type,
            color_mask: self.color_mask,
            char_id_1: self.char_id_1,
            char_id_2: self.char_id_2,
            char_id_3: self.char_id_3,
            zone_mask: self.zone_mask,
            special_id: self.special_id,
            is_setsuna: self.is_setsuna,
            compare_accumulated: self.compare_accumulated,
            is_optional: self.is_optional,
            keyword_energy: self.keyword_energy,
            keyword_member: self.keyword_member,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BytecodeInstruction {
    pub op: i32,
    pub v: i32,
    pub a: i64,
    pub raw_s: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BytecodeLayout {
    Fixed5x32V1,
    CompactV2,
    TaggedV3,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BytecodeOperandTag {
    Value = 1,
    Attr = 2,
    Slot = 3,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BytecodeOperandLayout {
    pub has_v: bool,
    pub has_a: bool,
    pub has_s: bool,
}

#[derive(Debug, Clone)]
pub struct BytecodeProgram {
    words: Arc<Vec<i32>>,
}

impl BytecodeProgram {
    pub fn from_frames(frames: &[crate::core::logic::models::AbilityFrame]) -> Self {
        let mut words = Vec::with_capacity(frames.len() * WORDS_PER_INSTRUCTION);
        for frame in frames {
            let instr = frame.to_instruction();
            words.push(instr.op);
            words.push(instr.v);
            words.push(instr.a as u32 as i32);
            words.push((instr.a >> 32) as u32 as i32);
            words.push(instr.raw_s);
        }
        Self::from_slice(&words)
    }

    pub fn new(words: Arc<Vec<i32>>) -> Self {
        Self { words }
    }

    pub fn from_slice(words: &[i32]) -> Self {
        Self {
            words: Arc::new(words.to_vec()),
        }
    }

    pub fn words(&self) -> &[i32] {
        self.words.as_slice()
    }

    pub fn arc(&self) -> Arc<Vec<i32>> {
        Arc::clone(&self.words)
    }

    pub fn len_words(&self) -> usize {
        self.words.len()
    }

    pub fn layout(&self) -> BytecodeLayout {
        match (self.words.first().copied().unwrap_or(0) as u32) & LAYOUT_TAG_MASK {
            TAGGED_HEADER_FLAG => BytecodeLayout::TaggedV3,
            COMPACT_HEADER_FLAG => BytecodeLayout::CompactV2,
            _ => BytecodeLayout::Fixed5x32V1,
        }
    }

    pub fn len_instructions(&self) -> usize {
        match self.layout() {
            BytecodeLayout::Fixed5x32V1 => self.words.len() / WORDS_PER_INSTRUCTION,
            BytecodeLayout::CompactV2 => {
                let mut count = 0;
                let mut ip = 0;
                while let Some((_, next_ip)) = self.decode_at(ip) {
                    count += 1;
                    ip = next_ip;
                }
                count
            }
            BytecodeLayout::TaggedV3 => {
                let mut count = 0;
                let mut ip = 0;
                while let Some((_, next_ip)) = self.decode_at(ip) {
                    count += 1;
                    ip = next_ip;
                }
                count
            }
        }
    }

    pub fn is_word_ip_valid(&self, ip: usize) -> bool {
        self.decode_at(ip).is_some()
    }

    pub fn effect_ip(effect_idx: usize) -> usize {
        effect_idx * WORDS_PER_INSTRUCTION
    }

    pub fn effect_idx(ip: usize) -> usize {
        ip / WORDS_PER_INSTRUCTION
    }

    pub fn next_ip(&self, ip: usize) -> usize {
        self.decode_at(ip)
            .map(|(_, next_ip)| next_ip)
            .unwrap_or(self.words.len())
    }

    pub fn jump_target(&self, ip: usize, offset_in_instructions: i32) -> Option<usize> {
        let current_idx = self.instruction_index_at_ip(ip)? as i64;
        let target_idx = current_idx + 1 + offset_in_instructions as i64;
        if target_idx < 0 {
            return None;
        }
        self.ip_for_instruction_index(target_idx as usize)
    }

    pub fn instruction_at(&self, ip: usize) -> Option<BytecodeInstruction> {
        self.decode_at(ip).map(|(instr, _)| instr)
    }

    pub fn has_opcode(&self, target_op: i32) -> bool {
        let mut ip = 0;
        while let Some(instr) = self.instruction_at(ip) {
            if instr.op == target_op {
                return true;
            }
            ip = self.next_ip(ip);
        }
        false
    }

    pub fn from_compact_instructions(instructions: &[BytecodeInstruction]) -> Self {
        let mut words = Vec::new();
        for instruction in instructions {
            words.extend(Self::encode_compact_instruction(*instruction));
        }
        Self {
            words: Arc::new(words),
        }
    }

    fn instruction_index_at_ip(&self, ip: usize) -> Option<usize> {
        match self.layout() {
            BytecodeLayout::Fixed5x32V1 => {
                if ip < self.words.len() && ip % WORDS_PER_INSTRUCTION == 0 {
                    Some(ip / WORDS_PER_INSTRUCTION)
                } else {
                    None
                }
            }
            BytecodeLayout::CompactV2 => {
                let mut idx = 0;
                let mut cursor = 0;
                while let Some((_, next_ip)) = self.decode_at(cursor) {
                    if cursor == ip {
                        return Some(idx);
                    }
                    cursor = next_ip;
                    idx += 1;
                }
                None
            }
            BytecodeLayout::TaggedV3 => {
                let mut idx = 0;
                let mut cursor = 0;
                while let Some((_, next_ip)) = self.decode_at(cursor) {
                    if cursor == ip {
                        return Some(idx);
                    }
                    cursor = next_ip;
                    idx += 1;
                }
                None
            }
        }
    }

    fn ip_for_instruction_index(&self, target_idx: usize) -> Option<usize> {
        match self.layout() {
            BytecodeLayout::Fixed5x32V1 => {
                let ip = target_idx * WORDS_PER_INSTRUCTION;
                if ip < self.words.len() {
                    Some(ip)
                } else {
                    None
                }
            }
            BytecodeLayout::CompactV2 => {
                let mut idx = 0;
                let mut cursor = 0;
                while let Some((_, next_ip)) = self.decode_at(cursor) {
                    if idx == target_idx {
                        return Some(cursor);
                    }
                    cursor = next_ip;
                    idx += 1;
                }
                None
            }
            BytecodeLayout::TaggedV3 => {
                let mut idx = 0;
                let mut cursor = 0;
                while let Some((_, next_ip)) = self.decode_at(cursor) {
                    if idx == target_idx {
                        return Some(cursor);
                    }
                    cursor = next_ip;
                    idx += 1;
                }
                None
            }
        }
    }

    fn decode_at(&self, ip: usize) -> Option<(BytecodeInstruction, usize)> {
        if ip >= self.words.len() {
            return None;
        }
        match self.layout() {
            BytecodeLayout::Fixed5x32V1 => {
                let instr = BytecodeInstruction::decode(self.words(), ip);
                Some((instr, ip + WORDS_PER_INSTRUCTION))
            }
            BytecodeLayout::CompactV2 => {
                let header = self.words[ip] as u32;
                let op = (header & 0xFFFF) as i32;
                let has_v = (header & COMPACT_HAS_V_FLAG) != 0;
                let has_a = (header & COMPACT_HAS_A_FLAG) != 0;
                let has_s = (header & COMPACT_HAS_S_FLAG) != 0;
                let wide_a = (header & COMPACT_WIDE_A_FLAG) != 0;

                let mut cursor = ip + 1;
                let v = if has_v {
                    let value = *self.words.get(cursor)?;
                    cursor += 1;
                    value
                } else {
                    0
                };
                let a = if has_a {
                    let a_low = *self.words.get(cursor)? as u32;
                    cursor += 1;
                    let a_high = if wide_a {
                        let value = *self.words.get(cursor)? as u32;
                        cursor += 1;
                        value
                    } else {
                        0
                    };
                    ((a_high as i64) << 32) | (a_low as i64)
                } else {
                    0
                };
                let raw_s = if has_s {
                    let value = *self.words.get(cursor)?;
                    cursor += 1;
                    value
                } else {
                    0
                };

                Some((BytecodeInstruction { op, v, a, raw_s }, cursor))
            }
            BytecodeLayout::TaggedV3 => {
                let header = self.words[ip] as u32;
                let op = (header & 0xFFFF) as i32;
                let operand_count =
                    ((header >> TAGGED_OPERAND_COUNT_SHIFT) & TAGGED_OPERAND_COUNT_MASK) as usize;

                let mut cursor = ip + 1;
                let mut v = 0;
                let mut a = 0i64;
                let mut raw_s = 0;

                for _ in 0..operand_count {
                    let operand_header = *self.words.get(cursor)? as u32;
                    cursor += 1;

                    let operand_tag = operand_header & OPERAND_HEADER_TAG_MASK;
                    let wide = (operand_header & OPERAND_HEADER_WIDE_FLAG) != 0;

                    match operand_tag {
                        x if x == BytecodeOperandTag::Value as u32 => {
                            v = *self.words.get(cursor)?;
                            cursor += 1;
                        }
                        x if x == BytecodeOperandTag::Attr as u32 => {
                            let low = *self.words.get(cursor)? as u32;
                            cursor += 1;
                            let high = if wide {
                                let value = *self.words.get(cursor)? as u32;
                                cursor += 1;
                                value
                            } else {
                                0
                            };
                            a = ((high as i64) << 32) | (low as i64);
                        }
                        x if x == BytecodeOperandTag::Slot as u32 => {
                            raw_s = *self.words.get(cursor)?;
                            cursor += 1;
                        }
                        _ => return None,
                    }
                }

                Some((BytecodeInstruction { op, v, a, raw_s }, cursor))
            }
        }
    }

    fn encode_compact_instruction(instruction: BytecodeInstruction) -> Vec<i32> {
        let mut header = COMPACT_HEADER_FLAG | ((instruction.op as u32) & 0xFFFF);
        let mut words = Vec::new();
        let a_low = instruction.a as u32;
        let a_high = ((instruction.a as u64 >> 32) & 0xFFFF_FFFF) as u32;
        let has_v = instruction.v != 0;
        let has_a = instruction.a != 0;
        let has_s = instruction.raw_s != 0;
        let wide_a = a_high != 0;

        if has_v {
            header |= COMPACT_HAS_V_FLAG;
        }
        if has_a {
            header |= COMPACT_HAS_A_FLAG;
        }
        if has_s {
            header |= COMPACT_HAS_S_FLAG;
        }
        if wide_a {
            header |= COMPACT_WIDE_A_FLAG;
        }

        words.push(header as i32);
        if has_v {
            words.push(instruction.v);
        }
        if has_a {
            words.push(a_low as i32);
            if wide_a {
                words.push(a_high as i32);
            }
        }
        if has_s {
            words.push(instruction.raw_s);
        }
        words
    }

    fn encode_tagged_instruction(instruction: BytecodeInstruction) -> Vec<i32> {
        let mut operand_entries = Vec::new();
        let operand_layout = instruction.operand_layout();

        if operand_layout.has_v {
            operand_entries.push(Self::encode_tagged_operand(
                BytecodeOperandTag::Value,
                instruction.v as i64,
            ));
        }
        if operand_layout.has_a {
            operand_entries.push(Self::encode_tagged_operand(
                BytecodeOperandTag::Attr,
                instruction.a,
            ));
        }
        if operand_layout.has_s {
            operand_entries.push(Self::encode_tagged_operand(
                BytecodeOperandTag::Slot,
                instruction.raw_s as i64,
            ));
        }

        let mut words = Vec::new();
        let header = TAGGED_HEADER_FLAG
            | (((operand_entries.len() as u32) & TAGGED_OPERAND_COUNT_MASK)
                << TAGGED_OPERAND_COUNT_SHIFT)
            | ((instruction.op as u32) & 0xFFFF);
        words.push(header as i32);
        for entry in operand_entries {
            words.extend(entry);
        }
        words
    }

    fn encode_tagged_operand(tag: BytecodeOperandTag, value: i64) -> Vec<i32> {
        let mut words = Vec::new();
        match tag {
            BytecodeOperandTag::Value | BytecodeOperandTag::Slot => {
                words.push(tag as i32);
                words.push(value as i32);
            }
            BytecodeOperandTag::Attr => {
                let low = value as u32;
                let high = ((value as u64 >> 32) & 0xFFFF_FFFF) as u32;
                let wide = high != 0;
                let mut header = tag as u32;
                if wide {
                    header |= OPERAND_HEADER_WIDE_FLAG;
                }
                words.push(header as i32);
                words.push(low as i32);
                if wide {
                    words.push(high as i32);
                }
            }
        }
        words
    }
}

impl BytecodeProgram {
    pub fn compact_words_for_instruction(instruction: BytecodeInstruction) -> Vec<i32> {
        Self::encode_compact_instruction(instruction)
    }
}

impl BytecodeProgram {
    pub fn is_compact_header(word: i32) -> bool {
        (word as u32 & COMPACT_HEADER_FLAG) != 0
    }
}

impl BytecodeProgram {
    pub fn fixed_layout_word_len() -> usize {
        WORDS_PER_INSTRUCTION
    }
}

impl BytecodeProgram {
    pub fn is_compact(&self) -> bool {
        self.layout() == BytecodeLayout::CompactV2
    }

    pub fn is_tagged(&self) -> bool {
        self.layout() == BytecodeLayout::TaggedV3
    }
}

impl BytecodeProgram {
    pub fn decode_all(&self) -> Vec<BytecodeInstruction> {
        let mut decoded = Vec::new();
        let mut ip = 0;
        while let Some(instr) = self.instruction_at(ip) {
            decoded.push(instr);
            ip = self.next_ip(ip);
        }
        decoded
    }
}

impl BytecodeInstruction {
    pub fn new(op: i32, v: i32, a: i64, raw_s: i32) -> Self {
        Self { op, v, a, raw_s }
    }

    pub fn decode(words: &[i32], ip: usize) -> Self {
        let op = words[ip];
        let v = if ip + 1 < words.len() {
            words[ip + 1]
        } else {
            0
        };
        let a_low = if ip + 2 < words.len() {
            words[ip + 2]
        } else {
            0
        } as u32;
        let a_high = if ip + 3 < words.len() {
            words[ip + 3]
        } else {
            0
        } as u32;
        let raw_s = if ip + 4 < words.len() {
            words[ip + 4]
        } else {
            0
        };

        let a = ((a_high as i64) << 32) | (a_low as i64);

        Self { op, v, a, raw_s }
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

    pub fn operand_layout(&self) -> BytecodeOperandLayout {
        BytecodeOperandLayout {
            has_v: self.v != 0,
            has_a: self.a != 0,
            has_s: self.raw_s != 0,
        }
    }

    pub fn is_dynamic(&self) -> bool {
        (self.a
            & (A_STANDARD_COMPARE_ACCUMULATED_MASK << A_STANDARD_COMPARE_ACCUMULATED_SHIFT) as i64)
            != 0
    }

    pub fn scalar_dynamic_base(&self) -> i32 {
        ((self.v as u32 >> V_SCALAR_DYNAMIC_BASE_VALUE_SHIFT) & V_SCALAR_DYNAMIC_BASE_VALUE_MASK)
            as i32
    }

    pub fn scalar_dynamic_divisor(&self) -> i32 {
        ((self.v as u32 >> V_SCALAR_DYNAMIC_DIVISOR_SHIFT) & V_SCALAR_DYNAMIC_DIVISOR_MASK) as i32
    }
}

impl BytecodeProgram {
    pub fn from_tagged_instructions(instructions: &[BytecodeInstruction]) -> Self {
        let mut words = Vec::new();
        for instruction in instructions {
            words.extend(Self::encode_tagged_instruction(*instruction));
        }
        Self {
            words: Arc::new(words),
        }
    }

    pub fn tagged_words_for_instruction(instruction: BytecodeInstruction) -> Vec<i32> {
        Self::encode_tagged_instruction(instruction)
    }
}

#[cfg(test)]
mod tests {
    use super::{
        BytecodeInstruction, BytecodeLayout, BytecodeProgram, DecodedFilterAttr, DecodedSlot,
    };
    use crate::core::enums::Zone;
    use crate::test_helpers::BytecodeBuilder;
    use serde_json::json;

    #[test]
    fn decoded_slot_accepts_sparse_object() {
        let slot: DecodedSlot = serde_json::from_value(json!({})).unwrap();
        assert_eq!(slot, DecodedSlot::default());
    }

    #[test]
    fn decoded_slot_accepts_partial_object() {
        let slot: DecodedSlot = serde_json::from_value(json!({
            "target_slot": 6,
            "is_wait": true
        }))
        .unwrap();

        assert_eq!(slot.target_slot, 6);
        assert!(slot.is_wait);
        assert_eq!(slot.source_zone, Default::default());
    }

    #[test]
    fn compact_program_round_trips_instructions() {
        let instructions = vec![
            BytecodeInstruction::new(204, 3, 0, 0),
            BytecodeInstruction::new(3, 1, 0, 0),
            BytecodeInstruction::new(10, 1, 0, 4),
            BytecodeInstruction::new(58, 1, 0x2000_0000, 6),
            BytecodeInstruction::new(1, 0, 0, 0),
        ];

        let program = BytecodeProgram::from_compact_instructions(&instructions);
        assert_eq!(program.layout(), BytecodeLayout::CompactV2);
        assert_eq!(program.len_instructions(), instructions.len());
        assert_eq!(program.decode_all(), instructions);
    }

    #[test]
    fn compact_program_resolves_relative_jumps_by_instruction_index() {
        let instructions = vec![
            BytecodeInstruction::new(204, 3, 0, 0),
            BytecodeInstruction::new(3, 1, 0, 0),
            BytecodeInstruction::new(10, 1, 0, 4),
            BytecodeInstruction::new(1, 0, 0, 0),
        ];

        let program = BytecodeProgram::from_compact_instructions(&instructions);
        let jump_ip = program.next_ip(0);
        let target_ip = program.jump_target(jump_ip, 1).expect("jump target");
        let target = program
            .instruction_at(target_ip)
            .expect("target instruction");

        assert_eq!(target.op, 1);
    }

    #[test]
    fn tagged_program_round_trips_instructions() {
        let instructions = vec![
            BytecodeInstruction::new(204, 3, 0, 0),
            BytecodeInstruction::new(3, 1, 0, 0),
            BytecodeInstruction::new(10, 1, 0, 4),
            BytecodeInstruction::new(58, 1, 0x2000_0000, 6),
            BytecodeInstruction::new(1, 0, 0, 0),
        ];

        let program = BytecodeProgram::from_tagged_instructions(&instructions);
        assert_eq!(program.layout(), BytecodeLayout::TaggedV3);
        assert_eq!(program.len_instructions(), instructions.len());
        assert_eq!(program.decode_all(), instructions);
    }

    #[test]
    fn tagged_program_resolves_relative_jumps_by_instruction_index() {
        let instructions = vec![
            BytecodeInstruction::new(204, 3, 0, 0),
            BytecodeInstruction::new(3, 1, 0, 0),
            BytecodeInstruction::new(10, 1, 0, 4),
            BytecodeInstruction::new(1, 0, 0, 0),
        ];

        let program = BytecodeProgram::from_tagged_instructions(&instructions);
        let jump_ip = program.next_ip(0);
        let target_ip = program.jump_target(jump_ip, 1).expect("jump target");
        let target = program
            .instruction_at(target_ip)
            .expect("target instruction");

        assert_eq!(target.op, 1);
    }

    #[test]
    fn tagged_program_is_more_explicit_than_fixed_width_for_sparse_instructions() {
        let instr = BytecodeInstruction::new(204, 3, 0, 0);
        assert_eq!(
            BytecodeProgram::tagged_words_for_instruction(instr).len(),
            3
        );
        assert_eq!(
            BytecodeProgram::compact_words_for_instruction(instr).len(),
            2
        );
        assert_eq!(BytecodeProgram::fixed_layout_word_len(), 5);
    }

    #[test]
    fn slot_accessor_decodes_all_slot_flags() {
        let words = BytecodeBuilder::new(0)
            .slot(0)
            .source(Zone::Stage)
            .dest(Zone::Discard)
            .target(5)
            .reveal_until_live(true)
            .is_opponent(true)
            .area_idx(3)
            .build();

        let instruction = BytecodeInstruction::decode(&words, 0);
        let slot = instruction.slot();
        assert_eq!(slot.target_slot, 5);
        assert_eq!(slot.source_zone, Zone::Stage);
        assert_eq!(slot.dest_zone, Zone::Discard);
        assert_eq!(slot.remainder_zone, 0);
        assert!(slot.is_opponent);
        assert!(slot.is_reveal_until_live);
        assert!(slot.is_baton_slot);
        assert!(!slot.is_empty_slot);
        assert!(!slot.is_wait);
        assert!(!slot.is_dynamic);
        assert_eq!(slot.area_idx, 3);
    }

    #[test]
    fn filter_attr_accessor_round_trips_standard_fields() {
        let original = DecodedFilterAttr {
            target_player: 1,
            card_type: 2,
            group_enabled: true,
            group_id: 5,
            is_tapped: true,
            has_blade_heart: true,
            not_has_blade_heart: false,
            unique_names: true,
            unit_enabled: true,
            unit_id: 7,
            value_enabled: true,
            value_threshold: 9,
            is_le: true,
            is_cost_type: true,
            color_mask: 0b101010,
            char_id_1: 3,
            char_id_2: 4,
            char_id_3: 0,
            zone_mask: 0b011,
            special_id: 0,
            is_setsuna: true,
            compare_accumulated: true,
            is_optional: true,
            keyword_energy: true,
            keyword_member: false,
        };

        let instruction = BytecodeInstruction::new(0, 0, original.to_attr() as i64, 0);
        let decoded = instruction.filter_attr();
        assert_eq!(decoded.target_player, original.target_player);
        assert_eq!(decoded.card_type, original.card_type);
        assert_eq!(decoded.group_enabled, original.group_enabled);
        assert_eq!(decoded.group_id, original.group_id);
        assert_eq!(decoded.is_tapped, original.is_tapped);
        assert_eq!(decoded.has_blade_heart, original.has_blade_heart);
        assert_eq!(decoded.not_has_blade_heart, original.not_has_blade_heart);
        assert_eq!(decoded.unique_names, original.unique_names);
        assert_eq!(decoded.unit_enabled, original.unit_enabled);
        assert_eq!(decoded.unit_id, original.unit_id);
        assert_eq!(decoded.value_enabled, original.value_enabled);
        assert_eq!(decoded.value_threshold, original.value_threshold);
        assert_eq!(decoded.is_le, original.is_le);
        assert_eq!(decoded.is_cost_type, original.is_cost_type);
        assert_eq!(decoded.color_mask, original.color_mask);
        assert_eq!(decoded.char_id_1, original.char_id_1);
        assert_eq!(decoded.char_id_2, original.char_id_2);
        assert_eq!(decoded.char_id_3, original.char_id_3);
        assert_eq!(decoded.zone_mask, original.zone_mask);
        assert_eq!(decoded.special_id, original.special_id);
        assert_eq!(decoded.is_setsuna, original.is_setsuna);
        assert_eq!(decoded.compare_accumulated, original.compare_accumulated);
        assert_eq!(decoded.is_optional, original.is_optional);
        assert_eq!(decoded.keyword_energy, original.keyword_energy);
        assert_eq!(decoded.keyword_member, original.keyword_member);
    }
}
