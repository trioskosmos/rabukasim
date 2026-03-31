use crate::core::enums::ChoiceType;
use crate::core::enums::*;
use crate::core::generated_layout::*;
use crate::core::logic::filter::{filter_attr_from_params, CardFilter};
#[allow(deprecated)]
use crate::core::logic::interpreter::instruction::{
    BytecodeInstruction, BytecodeProgram, DecodedLookAndChoose, DecodedSlot,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum AbilityFrame {
    Return,
    Draw {
        count: i32,
        slot: DecodedSlot,
        is_cost: bool,
    },
    Semantic {
        opcode: i32,
        value: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        is_negated: bool,
        is_cost: bool,
        params: Value,
    },
    RecoverLive {
        count: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        params: Value,
        is_cost: bool,
    },
    RecoverMember {
        count: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        params: Value,
        is_cost: bool,
    },
    LookAndChoose {
        count: i32,
        choose_count: i32,
        reveal: bool,
        dest_discard: bool,
        char_id_1: u8,
        char_id_2: u8,
        char_id_3: u8,
        filter: CardFilter,
        slot: DecodedSlot,
        is_cost: bool,
    },
    SelectMember {
        count: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        is_cost: bool,
    },
    MoveMember {
        filter: CardFilter,
        slot: DecodedSlot,
        from_slot: i32,
        is_cost: bool,
    },
    MetaRule {
        rule_type: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        is_cost: bool,
    },
    Raw {
        opcode: i32,
        value: i32,
        attr: u64,
        slot: i32,
        is_cost: bool,
    },
}

impl<'de> Deserialize<'de> for AbilityFrame {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let raw_value = Value::deserialize(deserializer)?;
        Ok(Self::from_json_value(&raw_value))
    }
}

impl Serialize for AbilityFrame {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use serde::ser::SerializeMap;
        
        match self {
            AbilityFrame::Return => {
                let mut map = serializer.serialize_map(Some(1))?;
                map.serialize_entry("kind", "RETURN")?;
                map.end()
            }
            AbilityFrame::Draw { count, slot, is_cost } => {
                let mut map = serializer.serialize_map(Some(4))?;
                map.serialize_entry("kind", "DRAW")?;
                map.serialize_entry("count", count)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                map.end()
            }
            AbilityFrame::Semantic { opcode, value, filter, slot, is_negated, is_cost, params } => {
                let mut map = serializer.serialize_map(Some(7))?;
                map.serialize_entry("kind", "SEMANTIC")?;
                map.serialize_entry("opcode", opcode)?;
                map.serialize_entry("value", value)?;
                map.serialize_entry("filter", filter)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_negated", is_negated)?;
                map.serialize_entry("is_cost", is_cost)?;
                if !params.is_null() {
                    map.serialize_entry("params", params)?;
                }
                map.end()
            }
            AbilityFrame::RecoverLive { count, filter, slot, params, is_cost } => {
                let mut map = serializer.serialize_map(Some(6))?;
                map.serialize_entry("kind", "RECOVER_LIVE")?;
                map.serialize_entry("count", count)?;
                map.serialize_entry("filter", filter)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                if !params.is_null() {
                    map.serialize_entry("params", params)?;
                }
                map.end()
            }
            AbilityFrame::RecoverMember { count, filter, slot, params, is_cost } => {
                let mut map = serializer.serialize_map(Some(6))?;
                map.serialize_entry("kind", "RECOVER_MEMBER")?;
                map.serialize_entry("count", count)?;
                map.serialize_entry("filter", filter)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                if !params.is_null() {
                    map.serialize_entry("params", params)?;
                }
                map.end()
            }
            AbilityFrame::LookAndChoose { count, choose_count, reveal, dest_discard, char_id_1, char_id_2, char_id_3, filter, slot, is_cost } => {
                let mut map = serializer.serialize_map(Some(11))?;
                map.serialize_entry("kind", "LOOK_AND_CHOOSE")?;
                map.serialize_entry("count", count)?;
                map.serialize_entry("choose_count", choose_count)?;
                map.serialize_entry("reveal", reveal)?;
                map.serialize_entry("dest_discard", dest_discard)?;
                map.serialize_entry("char_id_1", char_id_1)?;
                map.serialize_entry("char_id_2", char_id_2)?;
                map.serialize_entry("char_id_3", char_id_3)?;
                map.serialize_entry("filter", filter)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                map.end()
            }
            AbilityFrame::SelectMember { count, filter, slot, is_cost } => {
                let mut map = serializer.serialize_map(Some(5))?;
                map.serialize_entry("kind", "SELECT_MEMBER")?;
                map.serialize_entry("count", count)?;
                map.serialize_entry("filter", filter)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                map.end()
            }
            AbilityFrame::MoveMember { filter, slot, from_slot, is_cost } => {
                let mut map = serializer.serialize_map(Some(5))?;
                map.serialize_entry("kind", "MOVE_MEMBER")?;
                map.serialize_entry("filter", filter)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("from_slot", from_slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                map.end()
            }
            AbilityFrame::MetaRule { rule_type, filter, slot, is_cost } => {
                let mut map = serializer.serialize_map(Some(5))?;
                map.serialize_entry("kind", "META_RULE")?;
                map.serialize_entry("rule_type", rule_type)?;
                map.serialize_entry("filter", filter)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                map.end()
            }
            AbilityFrame::Raw { opcode, value, attr, slot, is_cost } => {
                let mut map = serializer.serialize_map(Some(5))?;
                map.serialize_entry("opcode", opcode)?;
                map.serialize_entry("value", value)?;
                map.serialize_entry("attr", attr)?;
                map.serialize_entry("slot", slot)?;
                map.serialize_entry("is_cost", is_cost)?;
                map.end()
            }
        }
    }
}

impl Default for AbilityFrame {
    fn default() -> Self {
        AbilityFrame::Raw {
            opcode: 0,
            value: 0,
            attr: 0,
            slot: 0,
            is_cost: false,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct AbilityFrameComponents<'a> {
    pub raw_opcode: i32,
    pub opcode: i32,
    pub value: i32,
    pub filter: CardFilter,
    pub slot: DecodedSlot,
    pub raw_attr: u64,
    pub raw_slot: i32,
    pub is_negated: bool,
    pub is_cost: bool,
    pub params: Option<&'a Value>,
}

impl<'a> AbilityFrameComponents<'a> {
    /// Check if this frame uses dynamic value calculation (accumulated compare)
    pub fn is_dynamic(&self) -> bool {
        use crate::core::generated_layout::{A_STANDARD_COMPARE_ACCUMULATED_MASK, A_STANDARD_COMPARE_ACCUMULATED_SHIFT};
        (self.raw_attr & (A_STANDARD_COMPARE_ACCUMULATED_MASK << A_STANDARD_COMPARE_ACCUMULATED_SHIFT)) != 0
    }

    /// Get heart counts from frame data - returns tuple for compatibility
    pub fn heart_counts(&self) -> (i32, i32) {
        // Use V_HEART_COUNTS constants to extract proper heart values
        use crate::core::generated_layout::{
            V_HEART_COUNTS_PINK_SHIFT, V_HEART_COUNTS_RED_SHIFT, V_HEART_COUNTS_YELLOW_SHIFT,
            V_HEART_COUNTS_GREEN_SHIFT, V_HEART_COUNTS_BLUE_SHIFT, V_HEART_COUNTS_PURPLE_SHIFT,
            V_HEART_COUNTS_ANY_SHIFT, V_HEART_COUNTS_PINK_MASK
        };
        
        // Extract individual color counts and sum them for total hearts
        let pink = ((self.value >> V_HEART_COUNTS_PINK_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let red = ((self.value >> V_HEART_COUNTS_RED_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let yellow = ((self.value >> V_HEART_COUNTS_YELLOW_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let green = ((self.value >> V_HEART_COUNTS_GREEN_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let blue = ((self.value >> V_HEART_COUNTS_BLUE_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let purple = ((self.value >> V_HEART_COUNTS_PURPLE_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let any = ((self.value >> V_HEART_COUNTS_ANY_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        
        let total_hearts = pink + red + yellow + green + blue + purple;
        (total_hearts, any)
    }

    /// Get heart counts as DecodedHeartCounts struct
    pub fn heart_counts_struct(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartCounts {
        crate::core::logic::interpreter::instruction::DecodedHeartCounts::decode(self.value)
    }

    /// Get heart requirements from frame data - returns tuple for compatibility
    pub fn heart_requirements(&self) -> (i32, i32) {
        // Match the exact bit shifts used in apply_aura_modifier around line 1236-1242
        let hearts_req = ((self.raw_attr >> 16) & 0xF) as i32;  // From O_SET_HEART_COST logic
        let hearts_cost = ((self.raw_attr >> 20) & 0xF) as i32; // From O_SET_HEART_COST logic  
        (hearts_req, hearts_cost)
    }

    /// Get heart requirements as DecodedHeartRequirements struct
    pub fn heart_requirements_struct(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartRequirements {
        crate::core::logic::interpreter::instruction::DecodedHeartRequirements::decode(self.raw_attr as i64)
    }

    /// Extract look and choose parameters from this frame
    pub fn look_choose(&self) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        crate::core::logic::interpreter::instruction::DecodedLookAndChoose::decode(self.raw_slot)
    }

    /// Get the divisor for dynamic value calculation
    pub fn scalar_dynamic_divisor(&self) -> i32 {
        use crate::core::generated_layout::{V_SCALAR_DYNAMIC_DIVISOR_MASK, V_SCALAR_DYNAMIC_DIVISOR_SHIFT};
        ((self.value as u32 >> V_SCALAR_DYNAMIC_DIVISOR_SHIFT) & V_SCALAR_DYNAMIC_DIVISOR_MASK) as i32
    }

    /// Get the base for dynamic value calculation
    pub fn scalar_dynamic_base(&self) -> i32 {
        use crate::core::generated_layout::{V_SCALAR_DYNAMIC_BASE_VALUE_MASK, V_SCALAR_DYNAMIC_BASE_VALUE_SHIFT};
        ((self.value as u32 >> V_SCALAR_DYNAMIC_BASE_VALUE_SHIFT) & V_SCALAR_DYNAMIC_BASE_VALUE_MASK) as i32
    }
}

impl AbilityFrame {
    fn opcode_from_effect_type(effect_type: EffectType) -> i32 {
        match effect_type {
            EffectType::Draw => O_DRAW,
            EffectType::PayEnergy => O_PAY_ENERGY,
            EffectType::AddBlades => O_ADD_BLADES,
            EffectType::AddHearts => O_ADD_HEARTS,
            EffectType::ReduceCost => O_REDUCE_COST,
            EffectType::LookDeck => O_LOOK_DECK,
            EffectType::RecoverLive => O_RECOVER_LIVE,
            EffectType::BoostScore => O_BOOST_SCORE,
            EffectType::RecoverMember => O_RECOVER_MEMBER,
            EffectType::BuffPower => O_BUFF_POWER,
            EffectType::Immunity => O_IMMUNITY,
            EffectType::MoveMember => O_MOVE_MEMBER,
            EffectType::SwapCards => O_SWAP_CARDS,
            EffectType::SearchDeck => O_SEARCH_DECK,
            EffectType::EnergyCharge => O_ENERGY_CHARGE,
            EffectType::SetBlades => O_SET_BLADES,
            EffectType::SetHearts => O_SET_HEARTS,
            EffectType::FormationChange => O_FORMATION_CHANGE,
            EffectType::NegateEffect => O_NEGATE_EFFECT,
            EffectType::OrderDeck => O_ORDER_DECK,
            EffectType::MetaRule => O_META_RULE,
            EffectType::SelectMode => O_SELECT_MODE,
            EffectType::MoveToDeck => O_MOVE_TO_DECK,
            EffectType::TapOpponent => O_TAP_OPPONENT,
            EffectType::PlaceUnder => O_PLACE_UNDER,
            EffectType::Restriction => O_RESTRICTION,
            EffectType::BatonTouchMod => O_BATON_TOUCH_MOD,
            EffectType::SetScore => O_SET_SCORE,
            EffectType::SwapZone => O_SWAP_ZONE,
            EffectType::TransformColor => O_TRANSFORM_COLOR,
            EffectType::RevealCards => O_REVEAL_CARDS,
            EffectType::LookAndChoose => O_LOOK_AND_CHOOSE,
            EffectType::CheerReveal => O_CHEER_REVEAL,
            EffectType::ActivateMember => O_ACTIVATE_MEMBER,
            EffectType::AddToHand => O_ADD_TO_HAND,
            EffectType::ColorSelect => O_COLOR_SELECT,
            EffectType::TriggerRemote => O_TRIGGER_REMOTE,
            EffectType::ReduceHeartReq => O_REDUCE_HEART_REQ,
            EffectType::ModifyScoreRule => O_MODIFY_SCORE_RULE,
            EffectType::AddStageEnergy => O_ADD_STAGE_ENERGY,
            EffectType::SetTapped => O_SET_TAPPED,
            EffectType::TapMember => O_TAP_MEMBER,
            EffectType::PlayMemberFromHand => O_PLAY_MEMBER_FROM_HAND,
            EffectType::MoveToDiscard => O_MOVE_TO_DISCARD,
            EffectType::GrantAbility => O_GRANT_ABILITY,
            EffectType::IncreaseHeartCost => O_INCREASE_HEART_COST,
            EffectType::ReduceYellCount => O_REDUCE_YELL_COUNT,
            EffectType::PlayMemberFromDiscard => O_PLAY_MEMBER_FROM_DISCARD,
            EffectType::SelectMember => O_SELECT_MEMBER,
            EffectType::DrawUntil => O_DRAW_UNTIL,
            EffectType::SelectPlayer => O_SELECT_PLAYER,
            EffectType::SelectLive => O_SELECT_LIVE,
            EffectType::RevealUntil => O_REVEAL_UNTIL,
            EffectType::IncreaseCost => O_INCREASE_COST,
            EffectType::PreventPlayToSlot => O_PREVENT_PLAY_TO_SLOT,
            EffectType::SwapArea => O_SWAP_AREA,
            EffectType::TransformHeart => O_TRANSFORM_HEART,
            EffectType::SelectCards => O_SELECT_CARDS,
            EffectType::OpponentChoose => O_OPPONENT_CHOOSE,
            EffectType::PlayLiveFromDiscard => O_PLAY_LIVE_FROM_DISCARD,
            EffectType::ReduceLiveSetLimit => O_REDUCE_LIVE_SET_LIMIT,
            EffectType::SetTargetSelf => O_SET_TARGET_SELF,
            EffectType::SetTargetOpponent => O_SET_TARGET_OPPONENT,
            EffectType::PreventSetToSuccessPile => O_PREVENT_SET_TO_SUCCESS_PILE,
            EffectType::ActivateEnergy => O_ACTIVATE_ENERGY,
            EffectType::PreventActivate => O_PREVENT_ACTIVATE,
            EffectType::SetHeartCost => O_SET_HEART_COST,
            EffectType::PreventBatonTouch => O_PREVENT_BATON_TOUCH,
            EffectType::LookDeckDynamic => O_LOOK_DECK_DYNAMIC,
            EffectType::ReduceScore => O_REDUCE_SCORE,
            EffectType::RepeatAbility => O_REPEAT_ABILITY,
            EffectType::LoseExcessHearts => O_LOSE_EXCESS_HEARTS,
            EffectType::SkipActivatePhase => O_SKIP_ACTIVATE_PHASE,
            EffectType::PayEnergyDynamic => O_PAY_ENERGY_DYNAMIC,
            EffectType::PlaceEnergyUnderMember => O_PLACE_ENERGY_UNDER_MEMBER,
            EffectType::CalcSumCost => O_CALC_SUM_COST,
            EffectType::LookReorderDiscard => O_LOOK_REORDER_DISCARD,
            EffectType::DivValue => O_DIV_VALUE,
            EffectType::TransformBlades => O_TRANSFORM_BLADES,
            _ => 0,
        }
    }

    fn normalize_frame_kind(kind: &str) -> String {
        if kind.is_empty() {
            return String::new();
        }

        if kind.chars().any(|ch| ch == '_') {
            return kind.to_ascii_uppercase();
        }

        let mut normalized = String::with_capacity(kind.len() + 4);
        let mut prev_is_lower_or_digit = false;
        for ch in kind.chars() {
            if ch.is_ascii_uppercase() && prev_is_lower_or_digit {
                normalized.push('_');
            }
            normalized.push(ch.to_ascii_uppercase());
            prev_is_lower_or_digit = ch.is_ascii_lowercase() || ch.is_ascii_digit();
        }
        normalized
    }

    fn opcode_id_from_frame_kind(kind: &str) -> i32 {
        match kind {
            "RETURN" => O_RETURN,
            "DRAW" => O_DRAW,
            "NOP" => O_NOP,
            "PAY_ENERGY" => O_PAY_ENERGY,
            "PAY_ENERGY_DYNAMIC" => O_PAY_ENERGY_DYNAMIC,
            "ENERGY_CHARGE" => O_ENERGY_CHARGE,
            "ACTIVATE_ENERGY" => O_ACTIVATE_ENERGY,
            "PLACE_ENERGY_UNDER_MEMBER" => O_PLACE_ENERGY_UNDER_MEMBER,
            "RECOVER_LIVE" => O_RECOVER_LIVE,
            "RECOVER_MEMBER" => O_RECOVER_MEMBER,
            "LOOK_AND_CHOOSE" => O_LOOK_AND_CHOOSE,
            "SELECT_MEMBER" => O_SELECT_MEMBER,
            "SELECT_LIVE" => O_SELECT_LIVE,
            "SELECT_PLAYER" => O_SELECT_PLAYER,
            "SELECT_CARDS" => O_SELECT_CARDS,
            "SELECT_MODE" => O_SELECT_MODE,
            "MOVE_MEMBER" => O_MOVE_MEMBER,
            "MOVE_TO_DECK" => O_MOVE_TO_DECK,
            "MOVE_TO_DISCARD" => O_MOVE_TO_DISCARD,
            "PLAY_MEMBER_FROM_HAND" => O_PLAY_MEMBER_FROM_HAND,
            "PLAY_MEMBER_FROM_DISCARD" => O_PLAY_MEMBER_FROM_DISCARD,
            "PLAY_LIVE_FROM_DISCARD" => O_PLAY_LIVE_FROM_DISCARD,
            "TAP_MEMBER" => O_TAP_MEMBER,
            "TAP_OPPONENT" => O_TAP_OPPONENT,
            "SET_TAPPED" => O_SET_TAPPED,
            "COLOR_SELECT" => O_COLOR_SELECT,
            "TRIGGER_REMOTE" => O_TRIGGER_REMOTE,
            "META_RULE" => O_META_RULE,
            "ADD_TO_HAND" => O_ADD_TO_HAND,
            "DRAW_UNTIL" => O_DRAW_UNTIL,
            "REVEAL_UNTIL" => O_REVEAL_UNTIL,
            "LOOK_DECK" => O_LOOK_DECK,
            "LOOK_DECK_DYNAMIC" => O_LOOK_DECK_DYNAMIC,
            "LOOK_REORDER_DISCARD" => O_LOOK_REORDER_DISCARD,
            "ORDER_DECK" => O_ORDER_DECK,
            "SEARCH_DECK" => O_SEARCH_DECK,
            "BOOST_SCORE" => O_BOOST_SCORE,
            "SET_SCORE" => O_SET_SCORE,
            "REDUCE_SCORE" => O_REDUCE_SCORE,
            "ADD_BLADES" => O_ADD_BLADES,
            "ADD_HEARTS" => O_ADD_HEARTS,
            "SET_BLADES" => O_SET_BLADES,
            "SET_HEARTS" => O_SET_HEARTS,
            "TRANSFORM_BLADES" => O_TRANSFORM_BLADES,
            "TRANSFORM_HEART" => O_TRANSFORM_HEART,
            "TRANSFORM_COLOR" => O_TRANSFORM_COLOR,
            "REPEAT_ABILITY" => O_REPEAT_ABILITY,
            "LOSE_EXCESS_HEARTS" => O_LOSE_EXCESS_HEARTS,
            "SKIP_ACTIVATE_PHASE" => O_SKIP_ACTIVATE_PHASE,
            "SET_HEART_COST" => O_SET_HEART_COST,
            "RESTRICTION" => O_RESTRICTION,
            "PREVENT_ACTIVATE" => O_PREVENT_ACTIVATE,
            "PREVENT_BATON_TOUCH" => O_PREVENT_BATON_TOUCH,
            "PREVENT_PLAY_TO_SLOT" => O_PREVENT_PLAY_TO_SLOT,
            "PREVENT_SET_TO_SUCCESS_PILE" => O_PREVENT_SET_TO_SUCCESS_PILE,
            "MODIFY_SCORE_RULE" => O_MODIFY_SCORE_RULE,
            "GRANT_ABILITY" => O_GRANT_ABILITY,
            "INCREASE_COST" => O_INCREASE_COST,
            "REDUCE_COST" => O_REDUCE_COST,
            "INCREASE_HEART_COST" => O_INCREASE_HEART_COST,
            "REDUCE_HEART_REQ" => O_REDUCE_HEART_REQ,
            "REDUCE_LIVE_SET_LIMIT" => O_REDUCE_LIVE_SET_LIMIT,
            "REDUCE_YELL_COUNT" => O_REDUCE_YELL_COUNT,
            "SWAP_CARDS" => O_SWAP_CARDS,
            "SWAP_AREA" => O_SWAP_AREA,
            "SET_TARGET_SELF" => O_SET_TARGET_SELF,
            "SET_TARGET_OPPONENT" => O_SET_TARGET_OPPONENT,
            "BATON_TOUCH_MOD" => O_BATON_TOUCH_MOD,
            "PLACE_UNDER" => O_PLACE_UNDER,
            "FORMALTION_CHANGE" => O_FORMATION_CHANGE,
            "FORMATION_CHANGE" => O_FORMATION_CHANGE,
            "CHEER_REVEAL" => O_CHEER_REVEAL,
            "REVEAL_CARDS" => O_REVEAL_CARDS,
            "CALC_SUM_COST" => O_CALC_SUM_COST,
            "DIV_VALUE" => O_DIV_VALUE,
            "APPLY_RULES" => O_META_RULE,
            "GROUP_FILTER" => C_GROUP_FILTER,
            "SCORE_COMPARE" => C_SCORE_COMPARE,
            "HAS_KEYWORD" => C_HAS_KEYWORD,
            "ALL_CARDS_MATCH" => 309,
            _ => 0,
        }
    }

    fn decoded_hint_name(decoded_hint: &str) -> Option<String> {
        let token = decoded_hint
            .split(|ch: char| ch.is_whitespace() || ch == '|')
            .find(|part| !part.is_empty())?;
        let token = token.trim_end_matches('?');
        let token = token.strip_prefix("CHECK_").unwrap_or(token);
        if token.is_empty() {
            None
        } else {
            Some(token.to_ascii_uppercase())
        }
    }

    fn first_field<'a>(value: &'a Value, keys: &[&str]) -> Option<&'a Value> {
        keys.iter().find_map(|key| value.get(*key))
    }

    fn first_str<'a>(value: &'a Value, keys: &[&str]) -> Option<&'a str> {
        Self::first_field(value, keys).and_then(Value::as_str)
    }

    fn first_i64(value: &Value, keys: &[&str]) -> Option<i64> {
        Self::first_field(value, keys).and_then(Value::as_i64)
    }

    fn first_cloned_value(value: &Value, keys: &[&str]) -> Value {
        Self::first_field(value, keys).cloned().unwrap_or(Value::Null)
    }

    fn zone_from_text(value: &str) -> Option<Zone> {
        match value.trim().to_ascii_uppercase().as_str() {
            "HAND" | "CARD_HAND" => Some(Zone::Hand),
            "DISCARD" | "CARD_DISCARD" => Some(Zone::Discard),
            "STAGE" => Some(Zone::Stage),
            "DECK" => Some(Zone::Deck),
            "DECK_TOP" | "TOP_DECK" => Some(Zone::DeckTop),
            "DECK_BOTTOM" | "BOTTOM_DECK" => Some(Zone::DeckBottom),
            "ENERGY" => Some(Zone::Energy),
            "LIVE" | "SUCCESS_LIVE" | "SUCCESS_PILE" => Some(Zone::SuccessPile),
            _ => None,
        }
    }

    pub(crate) fn from_json_value(frame: &Value) -> Self {
        if matches!(frame.as_str(), Some("Return" | "RETURN")) {
            return AbilityFrame::Return;
        }

        let semantic = frame.get("semantic").filter(|value| value.is_object());
        let mut payload = semantic.unwrap_or(frame);
        let mut kind = frame
            .get("kind")
            .and_then(|v| v.as_str())
            .or_else(|| frame.get("op").and_then(|v| v.as_str()))
            .unwrap_or("");
        if kind.is_empty() {
            if let Some(obj) = frame.as_object() {
                if obj.len() == 1 {
                    if let Some((key, value)) = obj.iter().next() {
                        if value.is_object()
                            || value.is_array()
                            || value.is_string()
                            || value.is_number()
                        {
                            kind = key.as_str();
                            payload = value;
                        }
                    }
                }
            }
        } else if semantic.is_none() {
            if let Some(value) = frame.get(kind) {
                if value.is_object() || value.is_array() || value.is_string() || value.is_number() {
                    payload = value;
                }
            }
        }

        let opcode_name = Self::first_str(payload, &["opcode_name", "op"])
            .or_else(|| Self::first_str(frame, &["opcode_name", "op"]))
            .unwrap_or("");
        let opcode_id = Self::first_i64(payload, &["opcode_id", "opcode", "op"])
            .or_else(|| Self::first_i64(frame, &["opcode_id", "opcode"]))
            .unwrap_or(0) as i32;
        let value_json = Self::first_cloned_value(payload, &["value", "count", "rule_type", "params", "v"]);
        let value = Self::first_i64(&value_json, &["value"])
            .or_else(|| Self::first_i64(payload, &["count", "rule_type", "v"]))
            .or_else(|| Self::first_i64(frame, &["value", "rule_type", "v"]))
            .unwrap_or(0) as i32;
        let filter = filter_attr_from_params(Some(payload))
            .map(|attr| CardFilter::from_attr(attr as i64))
            .unwrap_or_else(|| {
                payload
                    .get("filter")
                    .or_else(|| payload.get("attr"))
                    .cloned()
                    .and_then(|value| serde_json::from_value::<CardFilter>(value).ok())
                    .unwrap_or_default()
            });
        let slot = payload
            .get("slot")
            .or_else(|| frame.get("slot"))
            .cloned()
            .and_then(|value| serde_json::from_value::<DecodedSlot>(value).ok())
            .unwrap_or_default();
        let is_negated = payload
            .get("is_negated")
            .or_else(|| payload.get("negated"))
            .or_else(|| frame.get("negated"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let options = Self::first_cloned_value(frame, &["options"]);
        let options = if options.is_null() {
            Self::first_cloned_value(payload, &["options"])
        } else {
            options
        };
        let params = Self::first_cloned_value(payload, &["params"]);
        let params = if params.is_null() {
            Self::first_cloned_value(frame, &["params"])
        } else {
            params
        };
        let is_cost = payload
            .get("is_cost")
            .or_else(|| frame.get("is_cost"))
            .or_else(|| params.get("is_cost"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let params = if params.is_null() {
            options
                .get("params")
                .cloned()
                .unwrap_or(Value::Null)
        } else {
            params
        };
        let params_for_filter = if params.is_null() {
            options.clone()
        } else {
            params.clone()
        };
        let recover_params = params_for_filter.clone();
        let filter = if let Some(filter_attr) = filter_attr_from_params(Some(&params_for_filter)) {
            CardFilter::from_attr((filter.to_attr() as u64 | filter_attr) as i64)
        } else {
            filter
        };
        let filter = if let Some(structured_filter) = payload
            .get("filter")
            .or_else(|| options.get("filter"))
            .cloned()
            .and_then(|value| serde_json::from_value::<CardFilter>(value).ok())
        {
            let mut structured_filter = structured_filter;
            structured_filter.is_enabled = true;
            structured_filter
        } else {
            filter
        };
        let filter = if options
            .get("is_cost")
            .or_else(|| options.get("is_cost_type"))
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            let mut filter = filter;
            filter.is_cost_type = true;
            filter
        } else {
            filter
        };
        let filter = if options
            .get("optional")
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            let mut filter = filter;
            filter.is_optional = true;
            filter
        } else {
            filter
        };
        let mut slot = slot;
        if let Some(options_slot) = options.get("slot") {
            if let Ok(decoded_slot) = serde_json::from_value::<DecodedSlot>(options_slot.clone()) {
                slot = decoded_slot;
            }
        }
        if let Some(params_obj) = params.as_object() {
            let from_zone = params_obj
                .get("FROM")
                .or_else(|| params_obj.get("from"))
                .and_then(|value| value.as_str())
                .map(|value| value.to_ascii_uppercase());
            if slot.source_zone == Zone::default() {
                match from_zone.as_deref() {
                    Some("DISCARD") => slot.source_zone = Zone::Discard,
                    Some("HAND") => slot.source_zone = Zone::Hand,
                    Some("DECK") => slot.source_zone = Zone::Deck,
                    Some("STAGE") => slot.source_zone = Zone::Stage,
                    _ => {}
                }
            }
        }
        let opcode_key = if !kind.is_empty() { kind } else { opcode_name };
        let opcode_key = Self::normalize_frame_kind(opcode_key);
        let decoded_hint = Self::first_str(payload, &["decoded"])
            .or_else(|| Self::first_str(frame, &["decoded"]))
            .unwrap_or("");
        let decoded_hint_name = Self::decoded_hint_name(decoded_hint);

        let resolved_opcode_id = if opcode_id != 0 {
            opcode_id
        } else if opcode_key == "NOP" {
            decoded_hint_name
                .as_deref()
                .map(Self::opcode_id_from_frame_kind)
                .unwrap_or(0)
        } else {
            Self::opcode_id_from_frame_kind(opcode_key.as_str())
        };

        if resolved_opcode_id == 0 {
            if params
                .as_object()
                .and_then(|params| params.get("FILTER").or_else(|| params.get("filter")))
                .and_then(|value| value.as_str())
                .is_some()
                && params
                    .as_object()
                    .and_then(|params| params.get("FROM").or_else(|| params.get("from")))
                    .and_then(|value| value.as_str())
                    .map(|value| value.eq_ignore_ascii_case("DISCARD"))
                    .unwrap_or(false)
            {
                return AbilityFrame::Semantic {
                    opcode: O_SELECT_CARDS,
                    value: value.max(1),
                    filter,
                    slot,
                    is_negated,
                    is_cost: false,
                    params,
                };
            }
        }

        if opcode_key == "NOP" {
            if let Some(decoded_name) = decoded_hint_name.as_deref() {
                if resolved_opcode_id == 0 {
                    let mut params_obj = params.as_object().cloned().unwrap_or_default();
                    params_obj.insert("raw_cond".to_string(), Value::String(decoded_name.to_string()));
                    if decoded_name == "UNIQUE_NAMES_COUNT" {
                        params_obj.insert("MIN".to_string(), Value::from(value.max(0)));
                    }
                    return AbilityFrame::Semantic {
                        opcode: 0,
                        value,
                        filter,
                        slot,
                        is_negated,
                        is_cost: false,
                        params: Value::Object(params_obj),
                    };
                }
            }
        }

        match opcode_key.as_str() {
            "RETURN" => AbilityFrame::Return,
            "DRAW" => AbilityFrame::Draw { count: value, slot, is_cost },
            "RECOVER_LIVE" => AbilityFrame::RecoverLive {
                count: value,
                filter,
                slot,
                params: recover_params.clone(),
                is_cost,
            },
            "RECOVER_MEMBER" => AbilityFrame::RecoverMember {
                count: value,
                filter,
                slot,
                params: recover_params.clone(),
                is_cost,
            },
            "LOOK_AND_CHOOSE" => {
                let decoded = crate::core::logic::interpreter::instruction::DecodedLookAndChoose::decode(value);
                AbilityFrame::LookAndChoose {
                    count: decoded.count as i32,
                    choose_count: decoded.choose_count as i32,
                    reveal: decoded.reveal,
                    dest_discard: decoded.dest_discard,
                    char_id_1: decoded.char_id_1,
                    char_id_2: decoded.char_id_2,
                    char_id_3: decoded.char_id_3,
                    filter,
                    slot,
                    is_cost,
                }
            }
            "SELECT_MEMBER" => AbilityFrame::SelectMember {
                count: value,
                filter,
                slot,
                is_cost,
            },
            "MOVE_MEMBER" => AbilityFrame::MoveMember {
                filter,
                slot,
                from_slot: 0,
                is_cost,
            },
            "META_RULE" => AbilityFrame::MetaRule {
                rule_type: value,
                filter: filter,
                slot,
                is_cost,
            },
            _ => AbilityFrame::Semantic {
                opcode: resolved_opcode_id,
                value,
                filter,
                slot,
                is_negated,
                is_cost,
                params,
            },
        }
    }

    #[allow(deprecated)]
    pub fn from_instruction(instr: &BytecodeInstruction) -> Self {
        let is_negated = instr.op >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        let opcode = if is_negated {
            instr.op - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
        } else {
            instr.op
        };

        let filter = CardFilter::from_attr(instr.a);
        let slot = DecodedSlot::decode(instr.raw_s);
        let semantic = |opcode, value, is_negated, params| {
            AbilityFrame::Semantic {
                opcode,
                value,
                filter,
                slot,
                is_negated,
                is_cost: false,
                params,
            }
        };

        if is_negated {
            return semantic(opcode, instr.v, true, Value::Null);
        }

        match opcode {
            O_RETURN => AbilityFrame::Return,
            O_DRAW => AbilityFrame::Draw {
                count: instr.v,
                slot,
                is_cost: false,
            },
            O_RECOVER_LIVE => AbilityFrame::RecoverLive {
                count: instr.v,
                filter,
                slot,
                params: Value::Null,
                is_cost: false,
            },
            O_RECOVER_MEMBER => AbilityFrame::RecoverMember {
                count: instr.v,
                filter,
                slot,
                params: Value::Null,
                is_cost: false,
            },
            O_LOOK_AND_CHOOSE => {
                let decoded = DecodedLookAndChoose::decode(instr.v);
                AbilityFrame::LookAndChoose {
                    count: decoded.count as i32,
                    choose_count: decoded.choose_count as i32,
                    reveal: decoded.reveal,
                    dest_discard: decoded.dest_discard,
                    char_id_1: decoded.char_id_1,
                    char_id_2: decoded.char_id_2,
                    char_id_3: decoded.char_id_3,
                    filter,
                    slot,
                    is_cost: false,
                }
            }
            O_SELECT_MEMBER => AbilityFrame::SelectMember {
                count: instr.v,
                filter,
                slot,
                is_cost: false,
            },
            O_MOVE_MEMBER => AbilityFrame::MoveMember {
                filter,
                slot,
                from_slot: 0,
                is_cost: false,
            },
            O_META_RULE => AbilityFrame::MetaRule {
                rule_type: instr.v,
                filter,
                slot,
                is_cost: false,
            },
            _ => semantic(opcode, instr.v, false, Value::Null),
        }
    }

    pub fn new(opcode: i32, value: i32, attr: i64, raw_s: i32, is_cost: bool) -> Self {
        AbilityFrame::Raw {
            opcode,
            value,
            attr: attr as u64,
            slot: raw_s,
            is_cost,
        }
    }

    pub fn from_effect(effect: &Effect) -> Self {
        let runtime_opcode = if effect.runtime_opcode != 0 {
            effect.runtime_opcode
        } else {
            Self::opcode_from_effect_type(effect.effect_type)
        };
        let runtime_value = effect.value.clone();
        let runtime_attr = effect.runtime_attr;
        let mut runtime_slot = effect.runtime_slot;
        let mut slot = DecodedSlot::decode(runtime_slot);

        if let Some(destination) = effect
            .params
            .as_object()
            .and_then(|params| params.get("destination"))
            .and_then(|value| value.as_str())
        {
            match destination.to_ascii_lowercase().as_str() {
                "card_hand" => slot.target_slot = 6,
                "card_discard" => slot.target_slot = 7,
                _ => {}
            }
        }

        if let Some(source) = effect
            .params
            .as_object()
            .and_then(|params| params.get("source").or_else(|| params.get("SOURCE")))
            .and_then(|value| value.as_str())
            .and_then(Self::zone_from_text)
        {
            slot.source_zone = source;
        }

        if let Some(dest_zone) = effect
            .params
            .as_object()
            .and_then(|params| {
                params
                    .get("destination")
                    .or_else(|| params.get("DESTINATION"))
            })
            .and_then(|value| value.as_str())
            .and_then(Self::zone_from_text)
        {
            slot.dest_zone = dest_zone;
        }

        if effect
            .params
            .as_object()
            .and_then(|params| params.get("card_type"))
            .and_then(|value| value.as_str())
            .map(|value| value.eq_ignore_ascii_case("live"))
            .unwrap_or(false)
        {
            slot.is_reveal_until_live = true;
        }

        if effect
            .params
            .as_object()
            .and_then(|params| params.get("wait").or_else(|| params.get("WAIT")))
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            slot.is_wait = true;
        }

        runtime_slot = slot.to_raw();

        let value_i32 = match runtime_value {
            Value::Number(n) => n.as_i64().unwrap_or(0) as i32,
            Value::Object(obj) => {
                obj.get("count")
                    .and_then(|v| v.as_i64())
                    .or_else(|| obj.get("value").and_then(|v| v.as_i64()))
                    .unwrap_or(0) as i32
            }
            _ => 0,
        };

        // Special handling for SWAP_AREA effect (Mei's formation change)
        if runtime_opcode == O_SWAP_AREA {
            // When Mei (590) is played, rotate formation: [0,1,2] -> [1,2,0]
            return AbilityFrame::Raw {
                opcode: O_SWAP_AREA,
                value: 0,
                attr: 0,
                slot: 4,  // s=4 triggers rotation
                is_cost: false,
            };
        }

        // Special handling for FORMATION_CHANGE effect
        if runtime_opcode == O_FORMATION_CHANGE {
            // When Mei (590) is played on Left (0), rotate: [0,1,2] -> [1,2,0]
            // Center moves to Left, Left moves to Right, Right moves to Center
            return AbilityFrame::Raw {
                opcode: O_FORMATION_CHANGE,
                value: 0,  // Will trigger choice prompt for rotation
                attr: 0,
                slot: 4,  // Target slot 4 = RearrangeFormation
                is_cost: false,
            };
        }

        if !effect.params.is_null() {
            // Extract group info from params if available
            let mut filter = CardFilter::from_attr(runtime_attr as i64);
            if let Some(params_obj) = effect.params.as_object() {
                if let Some(group_enabled) = params_obj.get("group_enabled")
                    .and_then(|v| v.as_bool()) 
                {
                    filter.group_enabled = group_enabled;
                }
                if let Some(group_id) = params_obj.get("group_id")
                    .and_then(|v| v.as_i64()) 
                {
                    filter.group_id = group_id as u8;
                }
            }
            return AbilityFrame::Semantic {
                opcode: runtime_opcode,
                value: value_i32,
                filter,
                slot,
                is_negated: false,
                is_cost: false,
                params: effect.params.clone(),
            };
        }
        Self::new(
            runtime_opcode,
            value_i32,
            runtime_attr as i64,
            runtime_slot,
            false,
        )
    }

    pub fn opcode(&self) -> i32 {
        match self {
            AbilityFrame::Return => O_RETURN,
            AbilityFrame::Draw { .. } => O_DRAW,
            AbilityFrame::Semantic { opcode, .. } => *opcode,
            AbilityFrame::RecoverLive { .. } => O_RECOVER_LIVE,
            AbilityFrame::RecoverMember { .. } => O_RECOVER_MEMBER,
            AbilityFrame::LookAndChoose { .. } => O_LOOK_AND_CHOOSE,
            AbilityFrame::SelectMember { .. } => O_SELECT_MEMBER,
            AbilityFrame::MoveMember { .. } => O_MOVE_MEMBER,
            AbilityFrame::MetaRule { .. } => O_META_RULE,
            AbilityFrame::Raw { opcode, .. } => *opcode,
        }
    }

    pub fn is_cost(&self) -> bool {
        self.components().is_cost
    }

    pub fn components(&self) -> AbilityFrameComponents<'_> {
        let raw_opcode = self.opcode();
        let is_negated = self.is_negated();
        let opcode =
            if is_negated && raw_opcode >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET {
                raw_opcode - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
            } else {
                raw_opcode
            };

        match self {
            AbilityFrame::Return => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: 0,
                filter: CardFilter::default(),
                slot: DecodedSlot::default(),
                raw_attr: 0,
                raw_slot: 0,
                is_negated,
                is_cost: false,
                params: None,
            },
            AbilityFrame::Draw { count, slot, is_cost } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *count,
                filter: CardFilter::default(),
                slot: *slot,
                raw_attr: 0,
                raw_slot: slot.to_raw(),
                is_negated,
                is_cost: *is_cost,
                params: None,
            },
            AbilityFrame::Semantic {
                value,
                filter,
                slot,
                params,
                is_cost,
                ..
            } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *value,
                filter: *filter,
                slot: *slot,
                raw_attr: filter.to_attr() as u64,
                raw_slot: slot.to_raw(),
                is_negated,
                is_cost: *is_cost,
                params: Some(params),
            },
            AbilityFrame::RecoverLive {
                count,
                filter,
                slot,
                params,
                is_cost,
            }
            | AbilityFrame::RecoverMember {
                count,
                filter,
                slot,
                params,
                is_cost,
            } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *count,
                filter: *filter,
                slot: *slot,
                raw_attr: filter.to_attr() as u64,
                raw_slot: slot.to_raw(),
                is_negated,
                is_cost: *is_cost,
                params: Some(params),
            },
            AbilityFrame::SelectMember {
                count,
                filter,
                slot,
                is_cost,
            } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *count,
                filter: *filter,
                slot: *slot,
                raw_attr: filter.to_attr() as u64,
                raw_slot: slot.to_raw(),
                is_negated,
                is_cost: *is_cost,
                params: None,
            },
            AbilityFrame::LookAndChoose { filter, slot, is_cost, .. }
            | AbilityFrame::MoveMember { filter, slot, is_cost, .. }
            | AbilityFrame::MetaRule { filter, slot, is_cost, .. } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: self.value(),
                filter: *filter,
                slot: *slot,
                raw_attr: filter.to_attr() as u64,
                raw_slot: slot.to_raw(),
                is_negated,
                is_cost: *is_cost,
                params: None,
            },
            AbilityFrame::Raw {
                value, attr, slot, is_cost, ..
            } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *value,
                filter: CardFilter::from_attr(*attr as i64),
                slot: DecodedSlot::decode(*slot),
                raw_attr: *attr,
                raw_slot: *slot,
                is_negated,
                is_cost: *is_cost,
                params: None,
            },
        }
    }

    pub fn value(&self) -> i32 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { count, .. } => *count,
            AbilityFrame::Semantic { value, .. } => *value,
            AbilityFrame::RecoverLive { count, .. }
            | AbilityFrame::RecoverMember { count, .. }
            | AbilityFrame::SelectMember { count, .. } => *count,
            AbilityFrame::LookAndChoose {
                count,
                choose_count,
                reveal,
                dest_discard,
                char_id_1,
                char_id_2,
                char_id_3,
                ..
            } => crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
                count: *count as u8,
                choose_count: *choose_count as u8,
                reveal: *reveal,
                dest_discard: *dest_discard,
                char_id_1: *char_id_1,
                char_id_2: *char_id_2,
                char_id_3: *char_id_3,
            }
            .to_raw(),
            AbilityFrame::MoveMember { .. } => 0,
            AbilityFrame::MetaRule { rule_type, .. } => *rule_type,
            AbilityFrame::Raw { value, .. } => *value,
        }
    }

    pub fn attr(&self) -> u64 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { .. } => 0,
            AbilityFrame::Semantic { filter, .. }
            | AbilityFrame::RecoverLive { filter, .. }
            | AbilityFrame::RecoverMember { filter, .. }
            | AbilityFrame::LookAndChoose { filter, .. }
            | AbilityFrame::SelectMember { filter, .. }
            | AbilityFrame::MoveMember { filter, .. }
            | AbilityFrame::MetaRule { filter, .. } => filter.to_attr() as u64,
            AbilityFrame::Raw { attr, .. } => *attr,
        }
    }

    pub fn is_negated(&self) -> bool {
        match self {
            AbilityFrame::Semantic { is_negated, .. } => *is_negated,
            _ => {
                let op = self.opcode();
                op >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET
            }
        }
    }

    pub fn slot(&self) -> i32 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { .. } => 0,
            AbilityFrame::Semantic { slot, .. }
            | AbilityFrame::RecoverLive { slot, .. }
            | AbilityFrame::RecoverMember { slot, .. }
            | AbilityFrame::LookAndChoose { slot, .. }
            | AbilityFrame::SelectMember { slot, .. }
            | AbilityFrame::MoveMember { slot, .. }
            | AbilityFrame::MetaRule { slot, .. } => slot.to_raw(),
            AbilityFrame::Raw { slot, .. } => *slot,
        }
    }

    pub fn look_choose(
        &self,
    ) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        match self {
            AbilityFrame::LookAndChoose {
                count,
                choose_count,
                reveal,
                dest_discard,
                char_id_1,
                char_id_2,
                char_id_3,
                ..
            } => crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
                count: *count as u8,
                choose_count: *choose_count as u8,
                reveal: *reveal,
                dest_discard: *dest_discard,
                char_id_1: *char_id_1,
                char_id_2: *char_id_2,
                char_id_3: *char_id_3,
            },
            _ => crate::core::logic::interpreter::instruction::DecodedLookAndChoose::decode(
                self.value(),
            ),
        }
    }
    pub fn is_dynamic(&self) -> bool {
        (self.attr()
            & (A_STANDARD_COMPARE_ACCUMULATED_MASK << A_STANDARD_COMPARE_ACCUMULATED_SHIFT) as u64)
            != 0
    }
    pub fn scalar_dynamic_base(&self) -> i32 {
        ((self.value() as u32 >> V_SCALAR_DYNAMIC_BASE_VALUE_SHIFT)
            & V_SCALAR_DYNAMIC_BASE_VALUE_MASK) as i32
    }
    pub fn scalar_dynamic_divisor(&self) -> i32 {
        ((self.value() as u32 >> V_SCALAR_DYNAMIC_DIVISOR_SHIFT) & V_SCALAR_DYNAMIC_DIVISOR_MASK)
            as i32
    }
    pub fn heart_requirements(
        &self,
    ) -> crate::core::logic::interpreter::instruction::DecodedHeartRequirements {
        crate::core::logic::interpreter::instruction::DecodedHeartRequirements::decode(
            self.attr() as i64
        )
    }
    pub fn heart_counts(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartCounts {
        crate::core::logic::interpreter::instruction::DecodedHeartCounts::decode(self.value())
    }

    pub fn filter(&self) -> CardFilter {
        match self {
            AbilityFrame::Semantic { filter, .. }
            | AbilityFrame::RecoverLive { filter, .. }
            | AbilityFrame::RecoverMember { filter, .. }
            | AbilityFrame::LookAndChoose { filter, .. }
            | AbilityFrame::SelectMember { filter, .. }
            | AbilityFrame::MoveMember { filter, .. } => *filter,
            AbilityFrame::MetaRule { filter, .. } => CardFilter::from_attr(filter.to_attr() as i64),
            AbilityFrame::Raw { attr, .. } => CardFilter::from_attr((*attr) as i64),
            _ => CardFilter::default(),
        }
    }

    pub fn dslot(&self) -> DecodedSlot {
        match self {
            AbilityFrame::Semantic { slot, .. }
            | AbilityFrame::RecoverLive { slot, .. }
            | AbilityFrame::RecoverMember { slot, .. }
            | AbilityFrame::LookAndChoose { slot, .. }
            | AbilityFrame::SelectMember { slot, .. }
            | AbilityFrame::MoveMember { slot, .. }
            | AbilityFrame::MetaRule { slot, .. } => *slot,
            AbilityFrame::Raw { slot, .. } => DecodedSlot::decode(*slot),
            _ => DecodedSlot::default(),
        }
    }

    #[allow(deprecated)]
    pub fn to_instruction(
        &self,
    ) -> crate::core::logic::interpreter::instruction::BytecodeInstruction {
        let op = self.opcode();
        let v = self.value();
        let a = self.attr();
        let s = self.slot();

        let mut final_op = op;
        if self.is_negated() && op < crate::core::logic::constants::OPCODE_NEGATION_OFFSET {
            final_op += crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        }

        crate::core::logic::interpreter::instruction::BytecodeInstruction {
            op: final_op,
            v,
            a: a as i64,
            raw_s: s,
        }
    }
}

impl From<&AbilityFrame> for AbilityFrame {
    fn from(frame: &AbilityFrame) -> Self {
        frame.clone()
    }
}

#[allow(deprecated)]
impl From<&crate::core::logic::interpreter::instruction::BytecodeInstruction> for AbilityFrame {
    fn from(instr: &crate::core::logic::interpreter::instruction::BytecodeInstruction) -> Self {
        AbilityFrame::from_instruction(instr)
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct FrameProgram {
    pub frames: Vec<AbilityFrame>,
    pub raw_program: Option<Value>,
}

impl Serialize for FrameProgram {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        if let Some(raw) = &self.raw_program {
            let has_structured_frames = raw
                .get("instructions")
                .and_then(|v| v.as_array())
                .map(|frames| !frames.is_empty())
                .unwrap_or(false);

            if has_structured_frames {
                return raw.serialize(serializer);
            }

            let mut merged = raw.as_object().cloned().unwrap_or_default();
            merged.insert(
                "instructions".to_string(),
                Value::Array(
                    self.frames
                        .iter()
                        .map(|frame| serde_json::to_value(frame).unwrap_or(Value::Null))
                        .collect(),
                ),
            );
            return Value::Object(merged).serialize(serializer);
        }

        let mut map = serde_json::Map::new();
        map.insert(
            "instructions".to_string(),
            Value::Array(
                self.frames
                    .iter()
                    .map(|frame| serde_json::to_value(frame).unwrap_or(Value::Null))
                    .collect(),
            ),
        );
        Value::Object(map).serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for FrameProgram {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let raw_program = Value::deserialize(deserializer)?;
        let frames = raw_program
            .get("instructions")
            .or_else(|| raw_program.get("frames"))
            .and_then(|v| v.as_array())
            .map(|frames| {
                frames
                    .iter()
                    .map(AbilityFrame::from_json_value)
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();

        Ok(Self {
            frames,
            raw_program: Some(raw_program),
        })
    }
}

impl Hash for FrameProgram {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.frames.hash(state);
        if let Some(raw_program) = &self.raw_program {
            if let Ok(raw_json) = serde_json::to_string(raw_program) {
                raw_json.hash(state);
            }
        }
    }
}

impl FrameProgram {
    #[allow(deprecated)]
    pub fn from_words(words: &[i32]) -> Self {
        let decoded = BytecodeProgram::from_slice(words).decode_all();
        let frames = decoded.iter().map(AbilityFrame::from_instruction).collect();

        Self {
            frames,
            raw_program: Some(serde_json::json!({
                "instructions": [],
                "bytecode": words,
            })),
        }
    }

    pub fn from_bytecode(bytecode: &[i32]) -> Self {
        Self::from_words(bytecode)
    }

    #[allow(deprecated)]
    pub fn to_words(&self) -> Vec<i32> {
        if let Some(raw_program) = &self.raw_program {
            if let Some(words) = raw_program.get("bytecode").and_then(|v| v.as_array()) {
                let mut bytecode = Vec::with_capacity(words.len());
                for word in words {
                    if let Some(value) = word.as_i64() {
                        bytecode.push(value as i32);
                    }
                }
                if !bytecode.is_empty() {
                    return bytecode;
                }
            }
        }

        let mut words = Vec::with_capacity(
            self.frames.len() * crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION,
        );
        for frame in &self.frames {
            let instr = frame.to_instruction();
            words.push(instr.op);
            words.push(instr.v);
            words.push(instr.a as i32);
            words.push((instr.a >> 32) as i32);
            words.push(instr.raw_s);
        }
        words
    }

    pub fn to_bytecode(&self) -> Vec<i32> {
        self.to_words()
    }
}

// Re-export constants so they're available to all modules using `use super::models::*;`
pub use crate::core::logic::constants::*;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Condition {
    #[serde(rename = "type")]
    pub condition_type: ConditionType,
    #[serde(default)]
    pub value: i32,
    #[serde(default)]
    pub attr: u64,
    #[serde(default)]
    pub target_slot: u8,
    #[serde(default)]
    pub is_negated: bool,
    #[serde(default)]
    pub params: serde_json::Value,
}

impl std::hash::Hash for Condition {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.condition_type.hash(state);
        self.value.hash(state);
        self.attr.hash(state);
        self.target_slot.hash(state);
        self.is_negated.hash(state);
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Effect {
    pub effect_type: EffectType,
    #[serde(default)]
    pub value: serde_json::Value,
    #[serde(default)]
    pub value_cond: ConditionType,
    #[serde(default)]
    pub target: TargetType,
    #[serde(default)]
    pub is_optional: bool,
    #[serde(default)]
    pub params: serde_json::Value,
    #[serde(default)]
    pub runtime_opcode: i32,
    #[serde(default)]
    pub runtime_value: i32,
    #[serde(default)]
    pub runtime_attr: u64,
    #[serde(default)]
    pub runtime_slot: i32,
    #[serde(default)]
    pub modal_options: serde_json::Value,
}

impl Effect {
    /// Get the value as i32 (handles both integer and object values)
    pub fn value_as_i32(&self) -> i32 {
        match &self.value {
            serde_json::Value::Number(n) => n.as_i64().unwrap_or(0) as i32,
            serde_json::Value::Object(obj) => {
                // Try to extract from common object patterns like {"count": N}
                obj.get("count")
                    .and_then(|v| v.as_i64())
                    .or_else(|| obj.get("value").and_then(|v| v.as_i64()))
                    .unwrap_or(0) as i32
            }
            _ => 0,
        }
    }
}

impl std::hash::Hash for Effect {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.effect_type.hash(state);
        // Hash the JSON Value directly (serde_json::Value implements Hash)
        std::hash::Hash::hash(&self.value, state);
        self.value_cond.hash(state);
        self.target.hash(state);
        self.is_optional.hash(state);
        self.runtime_opcode.hash(state);
        self.runtime_value.hash(state);
        self.runtime_attr.hash(state);
        self.runtime_slot.hash(state);
        std::hash::Hash::hash(&self.modal_options, state);
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Cost {
    #[serde(rename = "type")]
    pub cost_type: AbilityCostType,
    #[serde(default)]
    pub value: i32,
    #[serde(default)]
    pub is_optional: bool,
    #[serde(default)]
    pub params: serde_json::Value,
}

impl std::hash::Hash for Cost {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.cost_type.hash(state);
        self.value.hash(state);
        self.is_optional.hash(state);
        // params is skipped
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct AbilityContext {
    pub player_id: u8,
    pub activator_id: u8, // The player who originally triggered/activated the ability
    pub area_idx: i16,
    pub source_card_id: i32,
    pub target_card_id: i32,
    pub target_slot: i16,
    pub selected_hand_idx: i16,
    pub choice_index: i16,
    /// Accumulated value (e.g. remaining cost limit for multi-card plays)
    pub v_accumulated: i16,
    pub selected_color: i16,
    pub program_counter: u16,
    pub ability_index: i16,
    pub v_remaining: i16,
    #[serde(default)]
    pub trigger_type: TriggerType,
    #[serde(default)]
    pub original_phase: Option<Phase>,
    #[serde(default)]
    pub original_current_player: Option<u8>,
    #[serde(default)]
    pub repeat_count: i16, // For O_REPEAT_ABILITY: tracks how many times ability has repeated
    #[serde(default)]
    pub selected_cards: smallvec::SmallVec<[i32; 8]>, // IDs of cards picked in the current/last selection action
    #[serde(default)]
    pub selected_target_keys: smallvec::SmallVec<[i32; 8]>,
    #[serde(default)]
    pub auto_pick: bool, // If true, mandatory single-choice steps (like O_SELECT_MODE) will resolve automatically
    #[serde(default)]
    pub is_static_eval: bool, // If true, skip phase restoration in finish_execution
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct StaticAbilityContext {
    pub player_id: u8,
    pub activator_id: u8,
    pub area_idx: i16,
    pub source_card_id: i32,
    pub target_card_id: i32,
    pub target_slot: i16,
    pub ability_index: i16,
    pub trigger_type: TriggerType,
    pub original_phase: Option<Phase>,
    pub original_current_player: Option<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Default)]
pub struct AbilityExecutionState {
    pub choice_index: i16,
    pub v_accumulated: i16,
    pub program_counter: u16,
    pub v_remaining: i16,
    pub repeat_count: i16,
    pub selected_cards: smallvec::SmallVec<[i32; 8]>,
    pub selected_target_keys: smallvec::SmallVec<[i32; 8]>,
    pub selected_color: i16,
    pub auto_pick: bool,
}

impl Default for AbilityContext {
    fn default() -> Self {
        Self {
            player_id: 0,
            activator_id: 0,
            area_idx: -1,
            source_card_id: -1,
            target_card_id: -1,
            target_slot: -1,
            selected_hand_idx: -1,
            choice_index: -1,
            selected_color: 0,
            program_counter: 0,
            ability_index: -1,
            v_accumulated: 0,
            v_remaining: -1,
            trigger_type: TriggerType::None,
            original_phase: None,
            original_current_player: None,
            repeat_count: 0,
            selected_cards: smallvec::SmallVec::new(),
            selected_target_keys: smallvec::SmallVec::new(),
            auto_pick: false,
            is_static_eval: false,
        }
    }
}

impl AbilityContext {
    pub fn static_context(&self) -> StaticAbilityContext {
        StaticAbilityContext {
            player_id: self.player_id,
            activator_id: self.activator_id,
            area_idx: self.area_idx,
            source_card_id: self.source_card_id,
            target_card_id: self.target_card_id,
            target_slot: self.target_slot,
            ability_index: self.ability_index,
            trigger_type: self.trigger_type,
            original_phase: self.original_phase,
            original_current_player: self.original_current_player,
        }
    }

    pub fn capture_state_raw(&mut self, phase: crate::core::enums::Phase, current_player: u8) {
        self.original_phase = Some(phase);
        self.original_current_player = Some(current_player);
    }

    pub fn execution_state(&self) -> AbilityExecutionState {
        AbilityExecutionState {
            choice_index: self.choice_index,
            v_accumulated: self.v_accumulated,
            program_counter: self.program_counter,
            v_remaining: self.v_remaining,
            repeat_count: self.repeat_count,
            selected_cards: self.selected_cards.clone(),
            selected_target_keys: self.selected_target_keys.clone(),
            selected_color: self.selected_color,
            auto_pick: self.auto_pick,
        }
    }

    pub fn apply_execution_state(&mut self, execution_state: &AbilityExecutionState) {
        self.choice_index = execution_state.choice_index;
        self.v_accumulated = execution_state.v_accumulated;
        self.program_counter = execution_state.program_counter;
        self.v_remaining = execution_state.v_remaining;
        self.repeat_count = execution_state.repeat_count;
        self.selected_cards = execution_state.selected_cards.clone();
        self.selected_target_keys = execution_state.selected_target_keys.clone();
        self.selected_color = execution_state.selected_color;
        self.auto_pick = execution_state.auto_pick;
    }

    pub fn clear_step_state(&mut self) {
        self.choice_index = -1;
        self.v_remaining = -1;
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct PendingInteraction {
    pub ctx: AbilityContext,
    pub card_id: i32,
    pub ability_index: i16,
    pub effect_opcode: i32,
    pub target_slot: i32,
    #[serde(default)]
    pub choice_type: ChoiceType,
    pub filter_attr: u64,
    pub choice_text: String,
    pub v_remaining: i16,
    #[serde(default)]
    pub original_phase: Phase,
    #[serde(default)]
    pub original_current_player: u8,
    #[serde(default)]
    pub actions: Vec<i32>,
    #[serde(default)]
    pub options: Vec<Value>,
    #[serde(default)]
    pub execution_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default, Hash)]
pub struct PreparsedModifier {
    pub op: i32,
    pub val: i32,
    pub attr: u64,
    pub slot: i32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Ability {
    #[serde(default)]
    pub raw_text: String,
    pub trigger: TriggerType,
    #[serde(default)]
    pub bytecode: Vec<i32>,
    #[serde(default)]
    pub effects: Vec<Effect>,
    #[serde(default)]
    pub conditions: Vec<Condition>,
    #[serde(default)]
    pub costs: Vec<Cost>,
    #[serde(default)]
    pub is_once_per_turn: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub frame_program: Option<FrameProgram>,
    #[serde(default)]
    pub requires_selection: bool,
    #[serde(default)]
    pub choice_flags: u8,
    #[serde(default)]
    pub choice_count: u8,
    #[serde(default, skip_serializing)]
    pub opcodes_mask: u128,
    #[serde(default)]
    pub option_names: Vec<String>,
    #[serde(default)]
    pub modal_options: serde_json::Value,
    #[serde(default)]
    pub pseudocode: String,
    #[serde(default)]
    pub preparsed_modifiers: Vec<PreparsedModifier>,
    #[serde(default)]
    pub filters: Vec<crate::core::logic::filter::CardFilter>,
}

impl std::hash::Hash for Ability {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.raw_text.hash(state);
        self.trigger.hash(state);
        self.effects.hash(state);
        self.conditions.hash(state);
        self.costs.hash(state);
        self.is_once_per_turn.hash(state);
        self.requires_selection.hash(state);
        self.choice_flags.hash(state);
        self.choice_count.hash(state);
        self.opcodes_mask.hash(state);
        self.option_names.hash(state);
        self.pseudocode.hash(state);
        self.preparsed_modifiers.hash(state);
        self.filters.hash(state);
        // modal_options skipped
    }
}

impl Ability {
    /// Check if ability has any effects
    pub fn has_effects(&self) -> bool {
        !self.effects.is_empty()
    }

    /// Get the number of modal options from effects
    pub fn modal_option_count(&self) -> usize {
        // Check first effect's modal_options
        self.effects.first()
            .and_then(|e| e.modal_options.as_array())
            .map(|opts| opts.len())
            .unwrap_or(0)
    }

    /// Get effects for a specific modal option
    pub fn get_modal_effects(&self, choice_idx: usize) -> Option<Vec<Effect>> {
        self.effects.first()
            .and_then(|e| e.modal_options.as_array())
            .and_then(|opts| opts.get(choice_idx))
            .and_then(|opt| opt.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| serde_json::from_value(v.clone()).ok())
                    .collect()
            })
    }

    /// Get modal option frames (backward compatibility)
    pub fn get_modal_option_frames(&self, choice_idx: usize) -> Option<Vec<AbilityFrame>> {
        // Convert effects to frames for compatibility
        self.get_modal_effects(choice_idx)
            .map(|effects| {
                effects.iter()
                    .map(|e| AbilityFrame::from_effect(e))
                    .collect()
            })
    }

    #[allow(deprecated)]
    pub fn words(&self) -> Vec<i32> {
        // First try frame_program if available
        if let Some(ref frame_program) = self.frame_program {
            return frame_program.to_words();
        }
        
        // Fallback: generate words from effects-generated frames
        if !self.effects.is_empty() {
            let frames: Vec<AbilityFrame> = self.effects.iter()
                .map(|e| AbilityFrame::from_effect(e))
                .collect();
            
            let mut words = Vec::with_capacity(
                frames.len() * crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION,
            );
            for frame in &frames {
                let instr = frame.to_instruction();
                words.push(instr.op);
                words.push(instr.v);
                words.push(instr.a as i32);
                words.push((instr.a >> 32) as i32);
                words.push(instr.raw_s);
            }
            return words;
        }
        
        Vec::new()
    }

    pub fn bytecode(&self) -> Vec<i32> {
        self.words()
    }

    pub fn get_frame(&self, frame_idx: usize) -> Option<AbilityFrame> {
        self.frames().get(frame_idx).cloned()
    }

    pub fn frames(&self) -> Vec<AbilityFrame> {
        // First try frame_program if available
        if let Some(ref frame_program) = self.frame_program {
            return frame_program.frames.clone();
        }
        
        // Fallback: generate frames from effects
        if !self.effects.is_empty() {
            return self.effects.iter()
                .map(|e| AbilityFrame::from_effect(e))
                .collect();
        }
        
        Vec::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ability_has_effects_works() {
        let ability = Ability {
            trigger: TriggerType::OnPlay,
            effects: vec![Effect::default()],
            ..Default::default()
        };
        assert!(ability.has_effects());
    }

    #[test]
    fn ability_modal_count_from_effects() {
        let ability = Ability::default();
        assert_eq!(ability.modal_option_count(), 0);
    }
}
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EnergyCard {
    pub card_id: i32,
    #[serde(default)]
    pub card_no: String,
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub img_path: String,
    #[serde(default)]
    pub ability_text: String,
    #[serde(default)]
    pub original_text: String,
    #[serde(default)]
    pub original_text_en: String,
    #[serde(default)]
    pub rare: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct TurnEvent {
    pub turn: u32,
    pub phase: Phase,
    pub player_id: u8,
    pub event_type: String, // e.g. "PLAY", "ACTIVATE", "TRIGGER", "RULE", "PERFORMANCE"
    pub source_cid: i32,
    pub ability_idx: i16,
    pub description: String,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default)]
pub struct DeckStats {
    pub avg_hearts: [f32; 7],
    pub avg_notes: f32,
    pub avg_draw: f32,
    pub count: f32,
}

impl PartialEq for DeckStats {
    fn eq(&self, other: &Self) -> bool {
        self.avg_hearts
            .iter()
            .zip(other.avg_hearts.iter())
            .all(|(a, b)| a.to_bits() == b.to_bits())
            && self.avg_notes.to_bits() == other.avg_notes.to_bits()
            && self.avg_draw.to_bits() == other.avg_draw.to_bits()
            && self.count.to_bits() == other.count.to_bits()
    }
}

impl Eq for DeckStats {}

impl std::hash::Hash for DeckStats {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        for &h in &self.avg_hearts {
            h.to_bits().hash(state);
        }
        self.avg_notes.to_bits().hash(state);
        self.avg_draw.to_bits().hash(state);
        self.count.to_bits().hash(state);
    }
}
