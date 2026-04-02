use crate::core::enums::ChoiceType;
use crate::core::enums::*;
use crate::core::generated_layout::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::instruction::DecodedSlot;
#[allow(deprecated)]
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::borrow::Cow;
use std::hash::{Hash, Hasher};

/// Flat, uniform runtime ability frame.
///
/// Replaces the old 10-variant enum with a single struct. All ability frame types
/// are now represented by the same five packed fields plus optional `params`.
///
/// * `opcode` – raw opcode value; may include `OPCODE_NEGATION_OFFSET` for negated frames.
///   Use [`is_negated()`] and [`effective_opcode()`] accordingly.
/// * `value`  – packed value/count (depends on opcode).
/// * `attr`   – packed 64-bit filter attribute (see [`CardFilter`]).
/// * `slot`   – packed slot word (see [`DecodedSlot`]).
/// * `is_cost` – true when this frame represents a cost step.
/// * `params` – optional extra JSON params for handlers that need them (usually `null`).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct AbilityFrame {
    pub opcode: i32,
    pub value: i32,
    pub attr: u64,
    pub slot: i32,
    pub is_cost: bool,
    pub params: Value,
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
        let size = if self.params.is_null() { 5 } else { 6 };
        let mut map = serializer.serialize_map(Some(size))?;
        map.serialize_entry("opcode", &self.opcode)?;
        map.serialize_entry("value", &self.value)?;
        map.serialize_entry("attr", &self.attr)?;
        map.serialize_entry("slot", &self.slot)?;
        map.serialize_entry("is_cost", &self.is_cost)?;
        if !self.params.is_null() {
            map.serialize_entry("params", &self.params)?;
        }
        map.end()
    }
}

impl Default for AbilityFrame {
    fn default() -> Self {
        AbilityFrame {
            opcode: 0,
            value: 0,
            attr: 0,
            slot: 0,
            is_cost: false,
            params: Value::Null,
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

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AbilityTraceStep {
    pub opcode: String,
    pub summary: String,
    #[serde(default)]
    pub is_cost: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub value: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_zone: Option<Zone>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dest_zone: Option<Zone>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_slot: Option<u8>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub choose_count: Option<u8>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reveal: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub remainder_to_discard: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub filter: Option<CardFilter>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub slot: Option<DecodedSlot>,
    #[serde(default, skip_serializing_if = "Value::is_null")]
    pub params: Value,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AbilityTraceView {
    pub trigger: TriggerType,
    pub frame_source: String,
    #[serde(default)]
    pub raw_text: String,
    #[serde(default)]
    pub choice_count: u8,
    #[serde(default)]
    pub steps: Vec<AbilityTraceStep>,
}

fn trace_opcode_name(opcode: i32) -> String {
    match opcode {
        O_DRAW => "DRAW".to_string(),
        O_MOVE_TO_DISCARD => "MOVE_TO_DISCARD".to_string(),
        O_LOOK_AND_CHOOSE => "LOOK_AND_CHOOSE".to_string(),
        O_RECOVER_LIVE => "RECOVER_LIVE".to_string(),
        O_RECOVER_MEMBER => "RECOVER_MEMBER".to_string(),
        O_RETURN => "RETURN".to_string(),
        O_JUMP => "JUMP".to_string(),
        O_JUMP_IF_FALSE => "JUMP_IF_FALSE".to_string(),
        O_PAY_ENERGY => "PAY_ENERGY".to_string(),
        O_SELECT_MEMBER => "SELECT_MEMBER".to_string(),
        O_ADD_BLADES => "ADD_BLADES".to_string(),
        O_ADD_HEARTS => "ADD_HEARTS".to_string(),
        O_BOOST_SCORE => "BOOST_SCORE".to_string(),
        O_TAP_MEMBER => "TAP_MEMBER".to_string(),
        O_SET_TAPPED => "SET_TAPPED".to_string(),
        O_NOP => "NOP".to_string(),
        _ => format!("OP_{}", opcode),
    }
}

fn trace_zone(zone: Zone) -> Option<Zone> {
    if zone == Zone::Default {
        None
    } else {
        Some(zone)
    }
}

impl<'a> AbilityFrameComponents<'a> {
    /// Resolve which player this frame targets based on the structured slot data.
    pub fn target_player_index(&self, controller_idx: usize) -> usize {
        if self.slot.is_opponent || self.filter.target_player == TARGET_PLAYER_OPPONENT as u8 {
            1 - controller_idx
        } else {
            controller_idx
        }
    }

    /// `ADD_TO_HAND` is effectively two effects: draw from deck, or consume the
    /// shared `looked_cards` buffer produced by search/reveal effects.
    pub fn add_to_hand_uses_looked_cards(&self) -> bool {
        self.raw_slot == crate::core::generated_constants::ZONE_LOOKED_CARDS
            || self.slot.target_slot as i32 == crate::core::generated_constants::SLOT_HAND
    }

    /// Check if this frame uses dynamic value calculation (accumulated compare)
    pub fn is_dynamic(&self) -> bool {
        use crate::core::generated_layout::{A_STANDARD_COMPARE_ACCUMULATED_MASK, A_STANDARD_COMPARE_ACCUMULATED_SHIFT};
        (self.raw_attr & (A_STANDARD_COMPARE_ACCUMULATED_MASK << A_STANDARD_COMPARE_ACCUMULATED_SHIFT)) != 0
    }

    /// Get heart counts from frame data - returns tuple for compatibility
    pub fn heart_counts(&self) -> (i32, i32) {
        use crate::core::generated_layout::{
            V_HEART_COUNTS_PINK_SHIFT, V_HEART_COUNTS_RED_SHIFT, V_HEART_COUNTS_YELLOW_SHIFT,
            V_HEART_COUNTS_GREEN_SHIFT, V_HEART_COUNTS_BLUE_SHIFT, V_HEART_COUNTS_PURPLE_SHIFT,
            V_HEART_COUNTS_ANY_SHIFT,
            V_HEART_COUNTS_PINK_MASK, V_HEART_COUNTS_RED_MASK, V_HEART_COUNTS_YELLOW_MASK,
            V_HEART_COUNTS_GREEN_MASK, V_HEART_COUNTS_BLUE_MASK, V_HEART_COUNTS_PURPLE_MASK,
            V_HEART_COUNTS_ANY_MASK
        };
        
        let value_u32 = self.value as u32;
        let pink = ((value_u32 >> V_HEART_COUNTS_PINK_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let red = ((value_u32 >> V_HEART_COUNTS_RED_SHIFT) & V_HEART_COUNTS_RED_MASK) as i32;
        let yellow = ((value_u32 >> V_HEART_COUNTS_YELLOW_SHIFT) & V_HEART_COUNTS_YELLOW_MASK) as i32;
        let green = ((value_u32 >> V_HEART_COUNTS_GREEN_SHIFT) & V_HEART_COUNTS_GREEN_MASK) as i32;
        let blue = ((value_u32 >> V_HEART_COUNTS_BLUE_SHIFT) & V_HEART_COUNTS_BLUE_MASK) as i32;
        let purple = ((value_u32 >> V_HEART_COUNTS_PURPLE_SHIFT) & V_HEART_COUNTS_PURPLE_MASK) as i32;
        let any = ((value_u32 >> V_HEART_COUNTS_ANY_SHIFT) & V_HEART_COUNTS_ANY_MASK) as i32;
        
        let total_hearts = pink + red + yellow + green + blue + purple;
        (total_hearts, any)
    }

    /// Get heart counts as DecodedHeartCounts struct
    pub fn heart_counts_struct(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartCounts {
        crate::core::logic::interpreter::instruction::DecodedHeartCounts::decode(self.value)
    }

    /// Get heart requirements from frame data - returns tuple for compatibility
    pub fn heart_requirements(&self) -> (i32, i32) {
        let decoded = self.heart_requirements_struct();
        let total_reqs: i32 = decoded.reqs.iter().map(|&r| r as i32).sum();
        (total_reqs, 0)
    }

    /// Get heart requirements as DecodedHeartRequirements struct
    pub fn heart_requirements_struct(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartRequirements {
        crate::core::logic::interpreter::instruction::DecodedHeartRequirements::decode(self.raw_attr as i64)
    }

    /// Extract look and choose parameters from this frame
    pub fn look_choose(&self) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        AbilityFrame::decode_look_choose(self.value, self.params)
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

    pub fn to_trace_step(&self) -> AbilityTraceStep {
        let opcode = trace_opcode_name(self.opcode);
        let mut step = AbilityTraceStep {
            summary: opcode.clone(),
            opcode,
            is_cost: self.is_cost,
            value: Some(self.value),
            source_zone: trace_zone(self.slot.source_zone),
            dest_zone: trace_zone(self.slot.dest_zone),
            target_slot: (self.slot.target_slot != 0).then_some(self.slot.target_slot),
            choose_count: None,
            reveal: None,
            remainder_to_discard: None,
            filter: (self.filter != CardFilter::default()).then_some(self.filter),
            slot: (self.slot != DecodedSlot::default()).then_some(self.slot),
            params: self.params.cloned().unwrap_or(Value::Null),
        };

        step.summary = match self.opcode {
            O_RETURN => {
                step.value = None;
                step.filter = None;
                step.slot = None;
                "return".to_string()
            }
            O_DRAW => format!("draw {} card(s)", self.value.max(0)),
            O_MOVE_TO_DISCARD => {
                let from_zone = step
                    .source_zone
                    .map(|zone| format!("{:?}", zone))
                    .unwrap_or_else(|| "Default".to_string());
                format!("move {} card(s) from {} to discard", self.value.max(0), from_zone)
            }
            O_RECOVER_LIVE => format!("recover {} live card(s) from discard", self.value.max(0)),
            O_RECOVER_MEMBER => format!("recover {} member card(s) from discard", self.value.max(0)),
            O_LOOK_AND_CHOOSE => {
                let look = self.look_choose();
                step.choose_count = Some(look.choose_count.max(1));
                step.reveal = Some(look.reveal);
                step.remainder_to_discard = Some(look.dest_discard);
                let from_zone = step
                    .source_zone
                    .map(|zone| format!("{:?}", zone))
                    .unwrap_or_else(|| "Deck".to_string());
                format!(
                    "look {} choose {} from {}{}",
                    look.count.max(1),
                    look.choose_count.max(1),
                    from_zone,
                    if look.dest_discard { ", remainder to discard" } else { "" }
                )
            }
            O_JUMP => format!("jump by {} frame(s)", self.value),
            O_JUMP_IF_FALSE => format!("if false jump by {} frame(s)", self.value),
            O_PAY_ENERGY => format!("pay {} energy", self.value.max(0)),
            O_SELECT_MEMBER => format!("select {} member(s)", self.value.max(1)),
            O_ADD_BLADES => format!("add {} blade(s)", self.value),
            O_ADD_HEARTS => format!("add {} heart(s)", self.value),
            O_BOOST_SCORE => format!("boost score by {}", self.value),
            O_TAP_MEMBER => format!("tap {} member(s)", self.value.max(1)),
            O_SET_TAPPED => {
                if self.value != 0 {
                    "set tapped".to_string()
                } else {
                    "clear tapped".to_string()
                }
            }
            O_NOP => "no-op".to_string(),
            _ => format!("{} value={}", step.opcode, self.value),
        };

        step
    }
}

impl AbilityFrame {
    fn decode_look_choose(
        value: i32,
        params: Option<&Value>,
    ) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        let mut decoded =
            crate::core::logic::interpreter::instruction::DecodedLookAndChoose::decode(value);

        let Some(params) = params else {
            return decoded;
        };

        if let Some(count) = params
            .get("count")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.count = count;
        }
        if let Some(choose_count) = params
            .get("choose_count")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.choose_count = choose_count;
        }
        if let Some(char_id_1) = params
            .get("char_id_1")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.char_id_1 = char_id_1;
        }
        if let Some(char_id_2) = params
            .get("char_id_2")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.char_id_2 = char_id_2;
        }
        if let Some(char_id_3) = params
            .get("char_id_3")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.char_id_3 = char_id_3;
        }
        if let Some(reveal) = params.get("reveal").and_then(|value| value.as_bool()) {
            decoded.reveal = reveal;
        }
        if let Some(dest_discard) = params.get("dest_discard").and_then(|value| value.as_bool()) {
            decoded.dest_discard = dest_discard;
        }

        decoded
    }

    fn with_components(
        opcode: i32,
        value: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        is_cost: bool,
        params: Value,
    ) -> Self {
        AbilityFrame {
            opcode,
            value,
            attr: filter.to_attr(),
            slot: slot.to_raw(),
            is_cost,
            params,
        }
    }

    fn with_raw_parts(
        opcode: i32,
        value: i32,
        attr: u64,
        slot: i32,
        is_cost: bool,
        params: Value,
    ) -> Self {
        AbilityFrame {
            opcode,
            value,
            attr,
            slot,
            is_cost,
            params,
        }
    }

    pub(crate) fn opcode_from_effect_type(effect_type: EffectType) -> i32 {
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

    fn extract_u8_from_text(text: &str, keys: &[&str]) -> Option<u8> {
        let lower = text.to_ascii_lowercase();
        for key in keys {
            if let Some(pos) = lower.find(key) {
                let mut digits = String::new();
                for ch in lower[pos + key.len()..].chars() {
                    if ch.is_ascii_digit() {
                        digits.push(ch);
                    } else if digits.is_empty() && (ch == ' ' || ch == '=' || ch == ':') {
                        continue;
                    } else {
                        break;
                    }
                }
                if let Ok(value) = digits.parse::<u8>() {
                    return Some(value);
                }
            }
        }
        None
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
            return AbilityFrame { opcode: O_RETURN, ..Default::default() };
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

        let opcode_name = Self::first_str(payload, &["opcode_name", "opcode", "op"])
            .or_else(|| Self::first_str(frame, &["opcode_name", "opcode", "op"]))
            .unwrap_or("");
        let opcode_id = Self::first_i64(payload, &["opcode_id", "opcode", "op"])
            .or_else(|| Self::first_i64(frame, &["opcode_id", "opcode"]))
            .unwrap_or(0) as i32;
        let value_json = Self::first_cloned_value(payload, &["value", "count", "rule_type", "params", "v"]);
        let value = Self::first_i64(&value_json, &["value"])
            .or_else(|| Self::first_i64(payload, &["count", "rule_type", "v"]))
            .or_else(|| Self::first_i64(frame, &["value", "rule_type", "v"]))
            .unwrap_or(0) as i32;
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
        let mut filter = CardFilter::from_frame_json(payload, &options, &params);
        let filter_passthrough = [payload, &options, &params]
            .into_iter()
            .filter_map(|value| {
                crate::core::logic::filter::filter_parts_from_params(Some(value))
                    .map(|(_, extras)| extras)
            })
            .fold(0u64, |acc, extras| acc | extras);
        let slot_value = payload
            .get("slot")
            .or_else(|| frame.get("slot"))
            .cloned();
        let slot = slot_value
            .clone()
            .and_then(|value| serde_json::from_value::<DecodedSlot>(value).ok())
            .unwrap_or_default();
        let is_negated = payload
            .get("is_negated")
            .or_else(|| payload.get("negated"))
            .or_else(|| frame.get("negated"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let recover_params = params.clone();
        let mut slot = slot;
        if let Some(slot_obj) = slot_value.as_ref().and_then(Value::as_object) {
            if let Some(target_slot) = slot_obj.get("target_slot").and_then(Value::as_u64) {
                slot.target_slot = target_slot as u8;
            }
            if let Some(comparison) = slot_obj.get("comparison").and_then(Value::as_u64) {
                slot.comparison = comparison as u8;
            }
            if let Some(source_zone) = slot_obj
                .get("source_zone")
                .and_then(Value::as_str)
                .and_then(Self::zone_from_text)
            {
                slot.source_zone = source_zone;
            }
            if let Some(dest_zone) = slot_obj
                .get("dest_zone")
                .and_then(Value::as_str)
                .and_then(Self::zone_from_text)
            {
                slot.dest_zone = dest_zone;
            }
            if let Some(remainder_zone) = slot_obj.get("remainder_zone").and_then(Value::as_u64) {
                slot.remainder_zone = remainder_zone as u8;
            }
            if let Some(area_idx) = slot_obj.get("area_idx").and_then(Value::as_u64) {
                slot.area_idx = area_idx as u8;
            }
            if let Some(is_opponent) = slot_obj.get("is_opponent") {
                slot.is_opponent = is_opponent.as_bool().unwrap_or_else(|| {
                    is_opponent.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_reveal_until_live) = slot_obj.get("is_reveal_until_live") {
                slot.is_reveal_until_live = is_reveal_until_live.as_bool().unwrap_or_else(|| {
                    is_reveal_until_live
                        .as_i64()
                        .map(|value| value != 0)
                        .unwrap_or(false)
                });
            }
            if let Some(is_baton_slot) = slot_obj.get("is_baton_slot") {
                slot.is_baton_slot = is_baton_slot.as_bool().unwrap_or_else(|| {
                    is_baton_slot.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_empty_slot) = slot_obj.get("is_empty_slot") {
                slot.is_empty_slot = is_empty_slot.as_bool().unwrap_or_else(|| {
                    is_empty_slot.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_wait) = slot_obj.get("is_wait") {
                slot.is_wait = is_wait.as_bool().unwrap_or_else(|| {
                    is_wait.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_dynamic) = slot_obj.get("is_dynamic") {
                slot.is_dynamic = is_dynamic.as_bool().unwrap_or_else(|| {
                    is_dynamic.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
        }
        if let Some(options_slot) = options.get("slot") {
            if let Ok(decoded_slot) = serde_json::from_value::<DecodedSlot>(options_slot.clone()) {
                slot = decoded_slot;
            }
        }
        if filter.target_player == 0 {
            filter.target_player = if slot.is_opponent {
                TARGET_PLAYER_OPPONENT as u8
            } else {
                TARGET_PLAYER_SELF as u8
            };
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
                return Self::with_raw_parts(
                    O_SELECT_CARDS,
                    value.max(1),
                    filter.to_attr() | filter_passthrough,
                    slot.to_raw(),
                    false,
                    params,
                );
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
                    return Self::with_raw_parts(
                        0,
                        value,
                        filter.to_attr() | filter_passthrough,
                        slot.to_raw(),
                        false,
                        Value::Object(params_obj),
                    );
                }
            }
        }

        match opcode_key.as_str() {
            "RETURN" => AbilityFrame { opcode: O_RETURN, ..Default::default() },
            "DRAW" => Self::with_components(O_DRAW, value, CardFilter::default(), slot, is_cost, Value::Null),
            "RECOVER_LIVE" => Self::with_raw_parts(
                O_RECOVER_LIVE,
                value,
                filter.to_attr() | filter_passthrough,
                slot.to_raw(),
                is_cost,
                recover_params.clone(),
            ),
            "RECOVER_MEMBER" => Self::with_raw_parts(
                O_RECOVER_MEMBER,
                value,
                filter.to_attr() | filter_passthrough,
                slot.to_raw(),
                is_cost,
                recover_params.clone(),
            ),
            "LOOK_AND_CHOOSE" => {
                // Read individual LAC fields if present; fall back to packed `value`.
                let decoded_text = Self::first_str(payload, &["decoded"])
                    .or_else(|| Self::first_str(frame, &["decoded"]))
                    .unwrap_or("");
                let summary_text = Self::first_str(payload, &["summary"])
                    .or_else(|| Self::first_str(frame, &["summary"]))
                    .unwrap_or("");
                let value_payload = payload.get("value");
                let structured_i64 = |key: &str| {
                    payload.get(key).and_then(|v| v.as_i64())
                        .or_else(|| params.get(key).and_then(|v| v.as_i64()))
                        .or_else(|| value_payload.and_then(|v| v.get(key)).and_then(|v| v.as_i64()))
                };
                let structured_bool = |key: &str| {
                    payload.get(key).and_then(|v| v.as_bool())
                        .or_else(|| params.get(key).and_then(|v| v.as_bool()))
                        .or_else(|| value_payload.and_then(|v| v.get(key)).and_then(|v| v.as_bool()))
                };
                let lac_count = structured_i64("count")
                    .or_else(|| Self::extract_u8_from_text(decoded_text, &["look=", "look_count=", "count="]).map(|v| v as i64))
                    .or_else(|| Self::extract_u8_from_text(summary_text, &["look at ", "look ", "count="]).map(|v| v as i64))
                    .unwrap_or(value as i64) as u8;
                let lac_choose = structured_i64("choose_count")
                    .or_else(|| Self::extract_u8_from_text(decoded_text, &["choose=", "choose "]).map(|v| v as i64))
                    .or_else(|| Self::extract_u8_from_text(summary_text, &["choose "]).map(|v| v as i64))
                    .unwrap_or(0) as u8;
                let lac_reveal = structured_bool("reveal").unwrap_or(false);
                let lac_dest = structured_bool("dest_discard").unwrap_or(false);
                let lac_c1 = structured_i64("char_id_1").unwrap_or(0) as u8;
                let lac_c2 = structured_i64("char_id_2").unwrap_or(0) as u8;
                let lac_c3 = structured_i64("char_id_3").unwrap_or(0) as u8;
                let packed = crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
                    count: lac_count, choose_count: lac_choose, reveal: lac_reveal,
                    dest_discard: lac_dest, char_id_1: lac_c1, char_id_2: lac_c2, char_id_3: lac_c3,
                }.to_raw();
                let mut lac_params = params.as_object().cloned().unwrap_or_default();
                lac_params.insert("count".to_string(), Value::from(lac_count));
                lac_params.insert("choose_count".to_string(), Value::from(lac_choose));
                lac_params.insert("char_id_1".to_string(), Value::from(lac_c1));
                lac_params.insert("char_id_2".to_string(), Value::from(lac_c2));
                lac_params.insert("char_id_3".to_string(), Value::from(lac_c3));
                lac_params.insert("reveal".to_string(), Value::from(lac_reveal));
                lac_params.insert("dest_discard".to_string(), Value::from(lac_dest));
                Self::with_raw_parts(
                    O_LOOK_AND_CHOOSE,
                    packed,
                    filter.to_attr() | filter_passthrough,
                    slot.to_raw(),
                    is_cost,
                    Value::Object(lac_params),
                )
            }
            "SELECT_MEMBER" => Self::with_raw_parts(O_SELECT_MEMBER, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params),
            "MOVE_MEMBER" => Self::with_raw_parts(O_MOVE_MEMBER, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params),
            "META_RULE" => Self::with_raw_parts(O_META_RULE, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params),
            _ => {
                let raw_op = if is_negated && resolved_opcode_id < crate::core::logic::constants::OPCODE_NEGATION_OFFSET {
                    resolved_opcode_id + crate::core::logic::constants::OPCODE_NEGATION_OFFSET
                } else {
                    resolved_opcode_id
                };
                Self::with_raw_parts(raw_op, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params)
            },
        }
    }

    #[allow(deprecated)]
    pub fn from_instruction(instr: &BytecodeInstruction) -> Self {
        Self::with_raw_parts(instr.op, instr.v, instr.a as u64, instr.raw_s, false, Value::Null)
    }

    pub fn new(opcode: i32, value: i32, attr: i64, raw_s: i32, is_cost: bool) -> Self {
        Self::with_raw_parts(opcode, value, attr as u64, raw_s, is_cost, Value::Null)
    }

    /// Create a RETURN frame.
    pub fn new_return() -> Self {
        AbilityFrame { opcode: O_RETURN, ..Default::default() }
    }

    /// Returns the opcode with the negation offset removed (if negated).
    pub fn effective_opcode(&self) -> i32 {
        if self.opcode >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET {
            self.opcode - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
        } else {
            self.opcode
        }
    }

    pub fn from_effect(effect: &Effect) -> Self {
        let runtime_opcode = if effect.runtime_opcode != 0 {
            effect.runtime_opcode
        } else {
            Self::opcode_from_effect_type(effect.effect_type)
        };
        let runtime_value_json = effect.value.clone();
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
            .and_then(|params| {
                params
                    .get("source")
                    .or_else(|| params.get("SOURCE"))
                    .or_else(|| params.get("from"))
                    .or_else(|| params.get("FROM"))
            })
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
                    .or_else(|| params.get("dest"))
                    .or_else(|| params.get("DEST"))
                    .or_else(|| params.get("to"))
                    .or_else(|| params.get("TO"))
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

        // Use runtime_value if set, otherwise extract from JSON value
        let value_i32 = if effect.runtime_value != 0 {
            effect.runtime_value
        } else {
            match runtime_value_json {
                Value::Number(n) => n.as_i64().unwrap_or(0) as i32,
                Value::Object(obj) => {
                    obj.get("count")
                        .and_then(|v| v.as_i64())
                        .or_else(|| obj.get("value").and_then(|v| v.as_i64()))
                        .unwrap_or(0) as i32
                }
                _ => 0,
            }
        };

        // Special handling for SWAP_AREA effect (Mei's formation change)
        if runtime_opcode == O_SWAP_AREA {
            // When Mei (590) is played, rotate formation: [0,1,2] -> [1,2,0]
            return Self::with_raw_parts(O_SWAP_AREA, 0, 0, 4, false, Value::Null);
        }

        // Special handling for FORMATION_CHANGE effect
        if runtime_opcode == O_FORMATION_CHANGE {
            // When Mei (590) is played on Left (0), rotate: [0,1,2] -> [1,2,0]
            // Center moves to Left, Left moves to Right, Right moves to Center
            return Self::with_raw_parts(O_FORMATION_CHANGE, 0, 0, 4, false, Value::Null);
        }

        if !effect.params.is_null() || effect.is_optional {
            let mut filter = CardFilter::from_attr_legacy(runtime_attr as i64);
            let runtime_passthrough = runtime_attr & !filter.to_attr();
            let mut params_passthrough = 0u64;

            if let Some((params_filter, passthrough)) = crate::core::logic::filter::filter_parts_from_params(Some(&effect.params)) {
                params_passthrough = passthrough;
                filter = filter.with_overlay(&params_filter);
            }
            if effect.is_optional {
                filter.is_enabled = true;
                filter.is_optional = true;
            }
            if filter.target_player == 0 {
                filter.target_player = if slot.is_opponent {
                    TARGET_PLAYER_OPPONENT as u8
                } else {
                    TARGET_PLAYER_SELF as u8
                };
            }
            return AbilityFrame {
                opcode: runtime_opcode,
                value: value_i32,
                attr: filter.to_attr() | runtime_passthrough | params_passthrough,
                slot: slot.to_raw(),
                is_cost: false,
                params: effect.params.clone(),
            };
        }
        Self::new(runtime_opcode, value_i32, runtime_attr as i64, runtime_slot, false)
    }

    pub fn opcode(&self) -> i32 {
        self.opcode
    }

    pub fn is_cost(&self) -> bool {
        self.is_cost
    }

    pub fn components(&self) -> AbilityFrameComponents<'_> {
        let raw_opcode = self.opcode;
        let is_negated = raw_opcode >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        let opcode = if is_negated {
            raw_opcode - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
        } else {
            raw_opcode
        };
        AbilityFrameComponents {
            raw_opcode,
            opcode,
            value: self.value,
            filter: CardFilter::from_attr_legacy(self.attr as i64),
            slot: DecodedSlot::decode(self.slot),
            raw_attr: self.attr,
            raw_slot: self.slot,
            is_negated,
            is_cost: self.is_cost,
            params: if self.params.is_null() { None } else { Some(&self.params) },
        }
    }

    pub fn value(&self) -> i32 {
        self.value
    }

    pub fn attr(&self) -> u64 {
        self.attr
    }

    pub fn slot(&self) -> i32 {
        self.slot
    }

    pub fn look_choose(
        &self,
    ) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        Self::decode_look_choose(
            self.value,
            if self.params.is_null() {
                None
            } else {
                Some(&self.params)
            },
        )
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
        CardFilter::from_attr_legacy(self.attr as i64)
    }

    pub fn dslot(&self) -> DecodedSlot {
        DecodedSlot::decode(self.slot)
    }

    #[allow(deprecated)]
    pub fn to_instruction(
        &self,
    ) -> crate::core::logic::interpreter::instruction::BytecodeInstruction {
        crate::core::logic::interpreter::instruction::BytecodeInstruction {
            op: self.opcode,
            v: self.value,
            a: self.attr as i64,
            raw_s: self.slot,
        }
    }
}

impl From<&AbilityFrame> for AbilityFrame {
    fn from(frame: &AbilityFrame) -> Self {
        frame.clone()
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
        let mut frames = Vec::with_capacity(
            words.len() / crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION,
        );
        let mut ip = 0;
        while ip < words.len() {
            let instr = BytecodeInstruction::decode(words, ip);
            frames.push(AbilityFrame::from_instruction(&instr));
            ip += crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION;
        }

        Self {
            frames,
            raw_program: Some(serde_json::json!({
                "instructions": [],
                "bytecode": words,
            })),
        }
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
    #[deprecated(since = "0.1.0", note = "Bytecode is deprecated. Use frame_program for execution.")]
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
    fn effect_opcode(effect: &Effect) -> i32 {
        if effect.runtime_opcode != 0 {
            effect.runtime_opcode
        } else {
            AbilityFrame::opcode_from_effect_type(effect.effect_type)
        }
    }

    fn is_runtime_effect_frame(frame: &AbilityFrame) -> bool {
        let opcode = frame.opcode();
        opcode != O_RETURN
            && opcode != O_JUMP
            && opcode != O_JUMP_IF_FALSE
            && crate::core::logic::interpreter::conditions::common::parse_condition_type(opcode)
                == ConditionType::None
    }

    fn frame_program_matches_effects(&self) -> bool {
        let Some(frame_program) = self.frame_program.as_ref() else {
            return false;
        };

        if self.effects.is_empty() {
            return !frame_program.frames.is_empty();
        }

        let expected_opcodes: Vec<i32> = self
            .effects
            .iter()
            .map(Self::effect_opcode)
            .filter(|opcode| *opcode != O_NOP && *opcode != O_RETURN)
            .collect();
        if expected_opcodes.is_empty() {
            return !frame_program.frames.is_empty();
        }

        let actual_opcodes: Vec<i32> = frame_program
            .frames
            .iter()
            .filter(|frame| Self::is_runtime_effect_frame(frame))
            .map(AbilityFrame::opcode)
            .collect();
        if actual_opcodes.is_empty() {
            return false;
        }

        expected_opcodes
            .iter()
            .any(|opcode| actual_opcodes.contains(opcode))
    }

    pub fn resolved_frame_source(&self) -> &'static str {
        if self.frame_program.is_some() && self.frame_program_matches_effects() {
            "frame_program"
        } else if !self.effects.is_empty() {
            "effects"
        } else if self.frame_program.is_some() {
            "frame_program_unmatched"
        } else {
            "none"
        }
    }

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

    pub fn resolved_frames(&self) -> Cow<'_, [AbilityFrame]> {
        if let Some(ref frame_program) = self.frame_program {
            if self.frame_program_matches_effects() {
                return Cow::Borrowed(&frame_program.frames);
            }
        }

        if !self.effects.is_empty() {
            return Cow::Owned(
                self.effects
                    .iter()
                    .map(AbilityFrame::from_effect)
                    .collect(),
            );
        }

        if let Some(ref frame_program) = self.frame_program {
            return Cow::Borrowed(&frame_program.frames);
        }

        Cow::Borrowed(&[])
    }

    pub fn has_resolved_frames(&self) -> bool {
        !self.resolved_frames().is_empty()
    }

    #[allow(deprecated)]
    pub fn words(&self) -> Vec<i32> {
        if let Some(ref frame_program) = self.frame_program {
            return frame_program.to_words();
        }

        let frames = self.resolved_frames();
        if !frames.is_empty() {
            let mut words = Vec::with_capacity(
                frames.len() * crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION,
            );
            for frame in frames.iter() {
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

    pub fn get_frame(&self, frame_idx: usize) -> Option<AbilityFrame> {
        self.resolved_frames().get(frame_idx).cloned()
    }

    pub fn frames(&self) -> Vec<AbilityFrame> {
        self.resolved_frames().into_owned()
    }

    pub fn trace_view(&self) -> AbilityTraceView {
        let steps = self
            .resolved_frames()
            .iter()
            .map(|frame| frame.components().to_trace_step())
            .collect();

        AbilityTraceView {
            trigger: self.trigger,
            frame_source: self.resolved_frame_source().to_string(),
            raw_text: self.raw_text.clone(),
            choice_count: self.choice_count,
            steps,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::logic::constants::FILTER_REVEALED_CONTEXT;
    use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice_with_options;
    use crate::core::models::CardDatabase;
    use crate::test_helpers::create_test_state;
    use serde_json::json;

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

    #[test]
    fn ability_resolved_frames_fall_back_to_effects() {
        let ability = Ability {
            trigger: TriggerType::OnPlay,
            effects: vec![Effect {
                effect_type: EffectType::Draw,
                value: Value::from(1),
                ..Default::default()
            }],
            ..Default::default()
        };

        let frames = ability.resolved_frames();
        assert_eq!(frames.len(), 1);
        assert_eq!(frames[0].opcode(), O_DRAW);
        assert!(ability.has_resolved_frames());
    }

    #[test]
    fn resolved_frames_prefer_effects_when_frame_program_has_no_effect_overlap() {
        let ability = Ability {
            trigger: TriggerType::Constant,
            effects: vec![Effect {
                effect_type: EffectType::AddBlades,
                value: Value::from(1),
                ..Default::default()
            }],
            frame_program: Some(FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_RECOVER_LIVE, 1, 0, 0, false),
                    AbilityFrame::new_return(),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let frames = ability.resolved_frames();
        assert_eq!(ability.resolved_frame_source(), "effects");
        assert_eq!(frames.len(), 1);
        assert_eq!(frames[0].opcode(), O_ADD_BLADES);
    }

    #[test]
    fn structured_draw_frame_preserves_minimal_hand_semantics() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "DRAW",
            "value": 1,
            "slot": {
                "is_opponent": 1,
                "dest_zone": "DISCARD"
            }
        }));

        let frame_data = frame.components();
        assert_eq!(frame_data.opcode, O_DRAW);
        assert_eq!(frame_data.value, 1);
        assert_eq!(frame_data.target_player_index(0), 1);
        assert_eq!(frame_data.slot.dest_zone, Zone::Discard);
    }

    #[test]
    fn trace_view_uses_human_readable_steps() {
        let ability = Ability {
            trigger: TriggerType::OnPlay,
            raw_text: "draw 1".to_string(),
            frame_program: Some(FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_DRAW, 1, 0, 0, false),
                    AbilityFrame::new_return(),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let trace = ability.trace_view();
        assert_eq!(trace.frame_source, "frame_program");
        assert_eq!(trace.steps[0].summary, "draw 1 card(s)");
        assert_eq!(trace.steps[1].summary, "return");
    }

    #[test]
    fn look_and_choose_trace_step_preserves_choose_count_from_params() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "LOOK_AND_CHOOSE",
            "value": 7,
            "slot": {
                "source_zone": "DECK",
                "dest_zone": "DISCARD",
                "target_slot": 6
            },
            "params": {
                "count": 7,
                "choose_count": 3,
                "reveal": true,
                "dest_discard": true
            }
        }));

        let trace = frame.components().to_trace_step();
        assert_eq!(trace.opcode, "LOOK_AND_CHOOSE");
        assert_eq!(trace.choose_count, Some(3));
        assert_eq!(trace.reveal, Some(true));
        assert_eq!(trace.remainder_to_discard, Some(true));
        assert!(trace.summary.contains("look 7 choose 3"));
    }

    #[test]
    fn add_to_hand_helper_accepts_legacy_looked_cards_encodings() {
        let zone_encoded = AbilityFrame::new(
            O_ADD_TO_HAND,
            1,
            0,
            crate::core::generated_constants::ZONE_LOOKED_CARDS,
            false,
        );
        let slot_encoded = AbilityFrame::new(
            O_ADD_TO_HAND,
            1,
            0,
            crate::core::generated_constants::SLOT_HAND,
            false,
        );

        assert!(zone_encoded.components().add_to_hand_uses_looked_cards());
        assert!(slot_encoded.components().add_to_hand_uses_looked_cards());
    }

    #[test]
    fn structured_reduce_cost_frame_preserves_card10_style_filter_bits() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "REDUCE_COST",
            "value": 1,
            "attr": {
                "target_player": 1,
                "special_id": "Not Self",
                "compare_accumulated": 1
            },
            "slot": {
                "is_dynamic": 1,
                "remainder_zone": 204
            }
        }));

        let frame_data = frame.components();
        assert_eq!(frame_data.filter.target_player, 1);
        assert_eq!(frame_data.filter.special_id, 3);
        assert!(frame_data.filter.compare_accumulated);
        assert!(frame_data.slot.is_dynamic);
        assert_eq!(frame_data.slot.remainder_zone, 204);
    }

    #[test]
    fn move_member_frame_preserves_structured_params() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "MOVE_MEMBER",
            "attr": {
                "is_optional": 1
            },
            "slot": {
                "target_slot": 4
            },
            "params": {
                "source": "STAGE",
                "destination": "STAGE"
            }
        }));

        assert_eq!(frame.opcode(), O_MOVE_MEMBER);
        assert_eq!(frame.params.get("source").and_then(|value| value.as_str()), Some("STAGE"));
        assert_eq!(
            frame.params.get("destination").and_then(|value| value.as_str()),
            Some("STAGE")
        );
        assert!(frame.components().filter.is_optional);
    }

    #[test]
    #[ignore = "Legacy passthrough bits not yet supported in structured-only mode"]
    fn semantic_filter_params_preserve_passthrough_bits_in_raw_attr() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "LOOK_AND_CHOOSE",
            "value": 1,
            "params": {
                "filter": "COST_LE_REVEALED"
            }
        }));

        assert_ne!(
            frame.attr() & crate::core::logic::constants::FILTER_REVEALED_CONTEXT,
            0
        );
        assert!(frame.components().filter.is_cost_type);
        assert!(frame.components().filter.is_le);

        let mut state = create_test_state();
        let db = CardDatabase::default();
        let ctx = AbilityContext {
            player_id: 0,
            ..Default::default()
        };

        let result = suspend_choice_with_options(
            &mut state,
            &db,
            &ctx,
            &ctx,
            0,
            O_LOOK_AND_CHOOSE,
            0,
            ChoiceType::LookAndChoose,
            frame.attr(),
            1,
            Vec::new(),
            vec![0],
        );

        assert!(matches!(result, crate::core::logic::interpreter::handlers::HandlerResult::Suspend));
        assert_ne!(
            state
                .interaction_stack
                .last()
                .map(|pending| pending.filter_attr & FILTER_REVEALED_CONTEXT)
                .unwrap_or(0),
            0
        );
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
