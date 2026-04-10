use crate::core::enums::Zone;
use crate::core::generated_constants::*;
use crate::core::generated_layout::*;
use crate::core::logic::filter::{
    parse_card_type_value, parse_character_id_value, parse_color_mask_value,
    parse_special_id_value, parse_target_player_value, parse_zone_mask_value, CardFilter,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const WORDS_PER_INSTRUCTION: usize = 5;

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
    Structured(DecodedSlotStructuredRaw),
}

#[derive(Deserialize, Default)]
struct DecodedSlotStructuredRaw {
    #[serde(default, deserialize_with = "deserialize_optional_target_slot")]
    target_slot: Option<u8>,
    #[serde(default, deserialize_with = "deserialize_optional_comparison")]
    comparison: Option<u8>,
    #[serde(default, deserialize_with = "deserialize_optional_zone")]
    source_zone: Option<Zone>,
    #[serde(default, deserialize_with = "deserialize_optional_zone")]
    dest_zone: Option<Zone>,
    #[serde(default, deserialize_with = "deserialize_optional_remainder_zone")]
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

fn deserialize_optional_zone<'de, D>(deserializer: D) -> Result<Option<Zone>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let value = Option::<Value>::deserialize(deserializer)?;
    let Some(value) = value else {
        return Ok(None);
    };

    let parsed = match value {
        Value::String(text) => match text.trim().to_ascii_uppercase().as_str() {
            "HAND" | "CARD_HAND" => Some(Zone::Hand),
            "DISCARD" | "CARD_DISCARD" => Some(Zone::Discard),
            "STAGE" => Some(Zone::Stage),
            "DECK" => Some(Zone::Deck),
            "DECK_TOP" | "TOP_DECK" => Some(Zone::DeckTop),
            "DECK_BOTTOM" | "BOTTOM_DECK" => Some(Zone::DeckBottom),
            "ENERGY" => Some(Zone::Energy),
            "LIVE" | "SUCCESS_LIVE" | "SUCCESS_PILE" => Some(Zone::SuccessPile),
            "YELL" => Some(Zone::Yell),
            _ => None,
        },
        Value::Number(number) => number
            .as_u64()
            .and_then(|raw| serde_json::from_value::<Zone>(Value::Number(raw.into())).ok()),
        other => serde_json::from_value::<Zone>(other).ok(),
    };

    parsed
        .map(Some)
        .ok_or_else(|| serde::de::Error::custom("invalid zone value"))
}

fn deserialize_zone_text(text: &str) -> Option<Zone> {
    match text.trim().to_ascii_uppercase().as_str() {
        "HAND" | "CARD_HAND" => Some(Zone::Hand),
        "DISCARD" | "CARD_DISCARD" => Some(Zone::Discard),
        "STAGE" => Some(Zone::Stage),
        "DECK" => Some(Zone::Deck),
        "DECK_TOP" | "TOP_DECK" => Some(Zone::DeckTop),
        "DECK_BOTTOM" | "BOTTOM_DECK" => Some(Zone::DeckBottom),
        "ENERGY" => Some(Zone::Energy),
        "LIVE" | "SUCCESS_LIVE" | "SUCCESS_PILE" => Some(Zone::SuccessPile),
        "YELL" => Some(Zone::Yell),
        _ => None,
    }
}

pub(crate) fn parse_target_slot_value(value: &Value) -> Option<u8> {
    value.as_u64().map(|value| value as u8).or_else(|| {
        value.as_str().and_then(|text| {
            let normalized = text.trim().to_ascii_uppercase().replace('-', "_").replace(' ', "_");
            match normalized.as_str() {
                "STAGE_0" => Some(0),
                "STAGE_1" => Some(1),
                "STAGE_2" => Some(2),
                "CONTEXT" => Some(4),
                "HAND" => Some(6),
                "DISCARD" => Some(7),
                "CHOICE_TARGET" => Some(10),
                "LIVE_0" | "LIVE_SET" => Some(13),
                "LIVE_1" => Some(14),
                "LIVE_2" => Some(15),
                "PLAYER_SELECT" => Some(20),
                _ => normalized.parse::<u8>().ok(),
            }
        })
    })
}

pub(crate) fn parse_comparison_value(value: &Value) -> Option<u8> {
    value.as_u64().map(|value| value as u8).or_else(|| {
        value.as_str().and_then(|text| {
            match text.trim().to_ascii_uppercase().replace('-', "_").replace(' ', "_").as_str() {
                "EQ" => Some(0),
                "GT" => Some(1),
                "LT" => Some(2),
                "GE" => Some(3),
                "LE" => Some(4),
                other => other.parse::<u8>().ok(),
            }
        })
    })
}

pub(crate) fn parse_remainder_zone_value(value: &Value) -> Option<u8> {
    value.as_u64().map(|value| value as u8).or_else(|| {
        value.as_str().and_then(|text| {
            match text.trim().to_ascii_uppercase().replace('-', "_").replace(' ', "_").as_str() {
                "STAGE" => Some(203),
                "HAND" => Some(204),
                "SUCCESS_PILE" | "SUCCESS_LIVE" | "LIVE_AREA" => Some(218),
                _ => deserialize_zone_text(text)
                    .map(|zone| zone as u8)
                    .or_else(|| text.trim().parse::<u8>().ok()),
            }
        })
    })
}

fn deserialize_optional_target_slot<'de, D>(deserializer: D) -> Result<Option<u8>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let value = Option::<Value>::deserialize(deserializer)?;
    Ok(value.as_ref().and_then(parse_target_slot_value))
}

fn deserialize_optional_comparison<'de, D>(deserializer: D) -> Result<Option<u8>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let value = Option::<Value>::deserialize(deserializer)?;
    Ok(value.as_ref().and_then(parse_comparison_value))
}

fn deserialize_optional_remainder_zone<'de, D>(deserializer: D) -> Result<Option<u8>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let value = Option::<Value>::deserialize(deserializer)?;
    Ok(value.as_ref().and_then(parse_remainder_zone_value))
}

impl From<DecodedSlotRaw> for DecodedSlot {
    fn from(raw: DecodedSlotRaw) -> Self {
        match raw {
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

        fn get_filter_u8(
            map: &serde_json::Map<String, serde_json::Value>,
            key: &str,
        ) -> u8 {
            let Some(value) = map.get(key) else {
                return 0;
            };

            match key {
                "target_player" => parse_target_player_value(value).unwrap_or_default(),
                "card_type" => parse_card_type_value(value).unwrap_or_default(),
                "zone_mask" => parse_zone_mask_value(value).unwrap_or_default(),
                "special_id" => parse_special_id_value(value).unwrap_or_default(),
                "color_mask" => parse_color_mask_value(value).unwrap_or_default(),
                "char_id_1" | "char_id_2" => {
                    parse_character_id_value(value).unwrap_or_default()
                }
                _ => value.as_u64().unwrap_or_default() as u8,
            }
        }

        fn get_bool(map: &serde_json::Map<String, serde_json::Value>, key: &str) -> bool {
            map.get(key)
                .and_then(|value| value.as_bool())
                .unwrap_or_default()
        }

        Ok(Self {
            target_player: get_filter_u8(map, "target_player"),
            card_type: get_filter_u8(map, "card_type"),
            group_enabled: get_bool(map, "group_enabled"),
            group_id: get_filter_u8(map, "group_id"),
            is_tapped: get_bool(map, "is_tapped"),
            has_blade_heart: get_bool(map, "has_blade_heart"),
            not_has_blade_heart: get_bool(map, "not_has_blade_heart"),
            unique_names: get_bool(map, "unique_names"),
            unit_enabled: get_bool(map, "unit_enabled"),
            unit_id: get_filter_u8(map, "unit_id"),
            value_enabled: get_bool(map, "value_enabled"),
            value_threshold: get_filter_u8(map, "value_threshold"),
            is_le: get_bool(map, "is_le"),
            is_cost_type: get_bool(map, "is_cost_type"),
            color_mask: get_filter_u8(map, "color_mask"),
            char_id_1: get_filter_u8(map, "char_id_1"),
            char_id_2: get_filter_u8(map, "char_id_2"),
            char_id_3: get_filter_u8(map, "char_id_3"),
            zone_mask: get_filter_u8(map, "zone_mask"),
            special_id: get_filter_u8(map, "special_id"),
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
            DecodedFilterAttrRaw::Structured(raw) => CardFilter {
                is_enabled: true,
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
            }
            .into(),
        }
    }
}

impl From<CardFilter> for DecodedFilterAttr {
    fn from(filter: CardFilter) -> Self {
        Self {
            target_player: filter.target_player,
            card_type: filter.card_type,
            group_enabled: filter.group_enabled,
            group_id: filter.group_id,
            is_tapped: filter.is_tapped,
            has_blade_heart: filter.has_blade_heart,
            not_has_blade_heart: filter.not_has_blade_heart,
            unique_names: filter.unique_names,
            unit_enabled: filter.unit_enabled,
            unit_id: filter.unit_id,
            value_enabled: filter.value_enabled,
            value_threshold: filter.value_threshold,
            is_le: filter.is_le,
            is_cost_type: filter.is_cost_type,
            color_mask: filter.color_mask,
            char_id_1: filter.char_id_1,
            char_id_2: filter.char_id_2,
            char_id_3: filter.char_id_3,
            zone_mask: filter.zone_mask,
            special_id: filter.special_id,
            is_setsuna: filter.is_setsuna,
            compare_accumulated: filter.compare_accumulated,
            is_optional: filter.is_optional,
            keyword_energy: filter.keyword_energy,
            keyword_member: filter.keyword_member,
        }
    }
}

impl From<DecodedFilterAttr> for CardFilter {
    fn from(filter: DecodedFilterAttr) -> Self {
        Self {
            is_enabled: true,
            target_player: filter.target_player,
            card_type: filter.card_type,
            group_enabled: filter.group_enabled,
            group_id: filter.group_id,
            is_tapped: filter.is_tapped,
            has_blade_heart: filter.has_blade_heart,
            not_has_blade_heart: filter.not_has_blade_heart,
            unique_names: filter.unique_names,
            unit_enabled: filter.unit_enabled,
            unit_id: filter.unit_id,
            value_enabled: filter.value_enabled,
            value_threshold: filter.value_threshold,
            is_le: filter.is_le,
            is_cost_type: filter.is_cost_type,
            color_mask: filter.color_mask,
            char_id_1: filter.char_id_1,
            char_id_2: filter.char_id_2,
            char_id_3: filter.char_id_3,
            zone_mask: filter.zone_mask,
            special_id: filter.special_id,
            is_setsuna: filter.is_setsuna,
            compare_accumulated: filter.compare_accumulated,
            is_optional: filter.is_optional,
            keyword_energy: filter.keyword_energy,
            keyword_member: filter.keyword_member,
        }
    }
}

impl DecodedFilterAttr {
    pub fn decode(a: i64) -> Self {
        CardFilter::from_attr(a as u64).into()
    }

    pub fn to_attr(&self) -> u64 {
        CardFilter::from(*self).to_attr()
    }
}

impl DecodedFilterAttr {
    pub fn to_card_filter(&self) -> CardFilter {
        (*self).into()
    }
}

#[cfg(test)]
mod tests {
    use super::{DecodedFilterAttr, DecodedSlot};
    use crate::core::enums::Zone;
    use crate::core::{TARGET_PLAYER_OPPONENT, ZONE_DISCARD};
    use serde_json::json;

    #[test]
    fn decoded_filter_attr_parses_string_special_and_zone_values() {
        let value = json!({
            "target_player": "OPPONENT",
            "card_type": "MEMBER",
            "special_id": "Base Cost",
            "zone_mask": "DISCARD"
        });

        let parsed: DecodedFilterAttr = serde_json::from_value(value).expect("filter should deserialize");

        assert_eq!(parsed.target_player, TARGET_PLAYER_OPPONENT as u8);
        assert_eq!(parsed.card_type, 1);
        assert_eq!(parsed.special_id, 5);
        assert_eq!(parsed.zone_mask, ZONE_DISCARD as u8);
    }

    #[test]
    fn decoded_slot_parses_named_target_slot_and_remainder_zone() {
        let parsed: DecodedSlot = serde_json::from_value(json!({
            "target_slot": "HAND",
            "comparison": "GE",
            "remainder_zone": "DISCARD",
            "source_zone": "DECK_TOP"
        }))
        .expect("slot should deserialize");

        assert_eq!(parsed.target_slot, 6);
        assert_eq!(parsed.comparison, 3);
        assert_eq!(parsed.remainder_zone, ZONE_DISCARD as u8);
        assert_eq!(parsed.source_zone, Zone::DeckTop);
    }
}

