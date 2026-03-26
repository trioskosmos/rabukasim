use crate::core::enums::ChoiceType;
use crate::core::enums::*;
use crate::core::generated_layout::*;
use crate::core::logic::filter::{filter_attr_from_params, CardFilter};
use crate::core::logic::interpreter::instruction::{
    BytecodeInstruction, BytecodeProgram, DecodedLookAndChoose, DecodedSlot,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Hash)]
pub enum AbilityFrame {
    Return,
    Draw {
        count: i32,
        slot: DecodedSlot,
    },
    Semantic {
        opcode: i32,
        value: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        #[serde(default)]
        is_negated: bool,
        #[serde(default)]
        params: Value,
    },
    RecoverLive {
        count: i32,
        filter: CardFilter,
        slot: DecodedSlot,
    },
    RecoverMember {
        count: i32,
        filter: CardFilter,
        slot: DecodedSlot,
    },
    LookAndChoose {
        params: DecodedLookAndChoose,
        filter: CardFilter,
        slot: DecodedSlot,
    },
    SelectMember {
        count: i32,
        filter: CardFilter,
        slot: DecodedSlot,
    },
    MoveMember {
        filter: CardFilter,
        slot: DecodedSlot,
        #[serde(default)]
        from_slot: i32,
    },
    MetaRule {
        rule_type: i32,
        filter: CardFilter,
        slot: DecodedSlot,
    },
    Raw {
        opcode: i32,
        value: i32,
        attr: u64,
        slot: i32,
    },
}

impl<'de> Deserialize<'de> for AbilityFrame {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let value = Value::deserialize(deserializer)?;
        Ok(Self::from_json_value(&value))
    }
}

impl Default for AbilityFrame {
    fn default() -> Self {
        AbilityFrame::Raw {
            opcode: 0,
            value: 0,
            attr: 0,
            slot: 0,
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
    pub params: Option<&'a Value>,
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
        let mut normalized = String::with_capacity(kind.len() + 4);
        for (index, ch) in kind.chars().enumerate() {
            if ch.is_ascii_uppercase() && index > 0 {
                normalized.push('_');
            }
            normalized.push(ch.to_ascii_uppercase());
        }
        normalized
    }

    fn opcode_id_from_frame_kind(kind: &str) -> i32 {
        match kind {
            "RETURN" => O_RETURN,
            "DRAW" => O_DRAW,
            "RECOVER_LIVE" => O_RECOVER_LIVE,
            "RECOVER_MEMBER" => O_RECOVER_MEMBER,
            "LOOK_AND_CHOOSE" => O_LOOK_AND_CHOOSE,
            "SELECT_MEMBER" => O_SELECT_MEMBER,
            "SELECT_CARDS" => O_SELECT_CARDS,
            "MOVE_MEMBER" => O_MOVE_MEMBER,
            "MOVE_TO_DECK" => O_MOVE_TO_DECK,
            "MOVE_TO_DISCARD" => O_MOVE_TO_DISCARD,
            "META_RULE" => O_META_RULE,
            _ => 0,
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

        let opcode_name = payload
            .get("opcode_name")
            .or_else(|| payload.get("op"))
            .or_else(|| frame.get("opcode_name"))
            .or_else(|| frame.get("op"))
            .and_then(|v| v.as_str())
            .unwrap_or("");
        let opcode_id = payload
            .get("opcode_id")
            .or_else(|| payload.get("opcode"))
            .or_else(|| payload.get("op"))
            .or_else(|| frame.get("opcode_id"))
            .or_else(|| frame.get("opcode"))
            .and_then(|v| v.as_i64())
            .unwrap_or(0) as i32;
        let value = payload
            .get("value")
            .or_else(|| payload.get("count"))
            .or_else(|| payload.get("rule_type"))
            .or_else(|| payload.get("params"))
            .or_else(|| payload.get("v"))
            .or_else(|| frame.get("value"))
            .or_else(|| frame.get("rule_type"))
            .or_else(|| frame.get("v"))
            .and_then(|v| v.as_i64())
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
        let params = payload
            .get("params")
            .or_else(|| frame.get("params"))
            .cloned()
            .unwrap_or(Value::Null);
        let filter = if let Some(filter_attr) = filter_attr_from_params(Some(&params)) {
            CardFilter::from_attr((filter.to_attr() as u64 | filter_attr) as i64)
        } else {
            filter
        };
        let mut slot = slot;
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

        let resolved_opcode_id = if opcode_id != 0 {
            opcode_id
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
                    params,
                };
            }
        }

        match opcode_key.as_str() {
            "RETURN" => AbilityFrame::Return,
            "DRAW" => AbilityFrame::Draw { count: value, slot },
            "RECOVER_LIVE" => AbilityFrame::RecoverLive {
                count: value,
                filter,
                slot,
            },
            "RECOVER_MEMBER" => AbilityFrame::RecoverMember {
                count: value,
                filter,
                slot,
            },
            "LOOK_AND_CHOOSE" => AbilityFrame::LookAndChoose {
                params: serde_json::from_value(params.clone())
                    .ok()
                    .unwrap_or_else(|| DecodedLookAndChoose::decode(value)),
                filter,
                slot,
            },
            "SELECT_MEMBER" => AbilityFrame::SelectMember {
                count: value,
                filter,
                slot,
            },
            "MOVE_MEMBER" => AbilityFrame::MoveMember {
                filter,
                slot,
                from_slot: 0,
            },
            "META_RULE" => AbilityFrame::MetaRule {
                rule_type: value,
                filter: filter,
                slot,
            },
            _ => AbilityFrame::Semantic {
                opcode: resolved_opcode_id,
                value,
                filter,
                slot,
                is_negated,
                params,
            },
        }
    }

    pub fn from_instruction(instr: &BytecodeInstruction) -> Self {
        let is_negated = instr.op >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        let opcode = if is_negated {
            instr.op - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
        } else {
            instr.op
        };

        let filter = CardFilter::from_attr(instr.a);
        let slot = DecodedSlot::decode(instr.raw_s);

        if is_negated {
            return AbilityFrame::Semantic {
                opcode,
                value: instr.v,
                filter,
                slot,
                is_negated: true,
                params: Value::Null,
            };
        }

        match opcode {
            O_RETURN => AbilityFrame::Return,
            O_DRAW => AbilityFrame::Draw {
                count: instr.v,
                slot,
            },
            O_RECOVER_LIVE => AbilityFrame::RecoverLive {
                count: instr.v,
                filter,
                slot,
            },
            O_RECOVER_MEMBER => AbilityFrame::RecoverMember {
                count: instr.v,
                filter,
                slot,
            },
            O_LOOK_AND_CHOOSE => AbilityFrame::LookAndChoose {
                params: DecodedLookAndChoose::decode(instr.v),
                filter,
                slot,
            },
            O_SELECT_MEMBER => AbilityFrame::SelectMember {
                count: instr.v,
                filter,
                slot,
            },
            O_MOVE_MEMBER => AbilityFrame::MoveMember {
                filter,
                slot,
                from_slot: 0,
            },
            O_META_RULE => AbilityFrame::MetaRule {
                rule_type: instr.v,
                filter: CardFilter::from_attr(instr.a),
                slot,
            },
            _ => AbilityFrame::Semantic {
                opcode,
                value: instr.v,
                filter,
                slot,
                is_negated: false,
                params: Value::Null,
            },
        }
    }

    pub fn new(opcode: i32, value: i32, attr: i64, raw_s: i32) -> Self {
        AbilityFrame::Raw {
            opcode,
            value,
            attr: attr as u64,
            slot: raw_s,
        }
    }

    pub fn from_effect(effect: &Effect) -> Self {
        let runtime_opcode = if effect.runtime_opcode != 0 {
            effect.runtime_opcode
        } else {
            Self::opcode_from_effect_type(effect.effect_type)
        };
        let runtime_value = effect.value;
        let runtime_attr = effect.runtime_attr;
        let mut runtime_slot = effect.runtime_slot;
        let mut slot = DecodedSlot::decode(runtime_slot);

        let zone_from_text = |value: &str| -> Option<Zone> {
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
        };

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
            .and_then(zone_from_text)
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
            .and_then(zone_from_text)
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

        if !effect.params.is_null() {
            return AbilityFrame::Semantic {
                opcode: runtime_opcode,
                value: runtime_value,
                filter: CardFilter::from_attr(runtime_attr as i64),
                slot,
                is_negated: false,
                params: effect.params.clone(),
            };
        }
        Self::new(
            runtime_opcode,
            runtime_value,
            runtime_attr as i64,
            runtime_slot,
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
                params: None,
            },
            AbilityFrame::Draw { count, slot } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *count,
                filter: CardFilter::default(),
                slot: *slot,
                raw_attr: 0,
                raw_slot: slot.to_raw(),
                is_negated,
                params: None,
            },
            AbilityFrame::Semantic {
                value,
                filter,
                slot,
                params,
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
                params: Some(params),
            },
            AbilityFrame::RecoverLive {
                count,
                filter,
                slot,
            }
            | AbilityFrame::RecoverMember {
                count,
                filter,
                slot,
            }
            | AbilityFrame::SelectMember {
                count,
                filter,
                slot,
            } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *count,
                filter: *filter,
                slot: *slot,
                raw_attr: filter.to_attr() as u64,
                raw_slot: slot.to_raw(),
                is_negated,
                params: None,
            },
            AbilityFrame::LookAndChoose { filter, slot, .. }
            | AbilityFrame::MoveMember { filter, slot, .. } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: self.value(),
                filter: *filter,
                slot: *slot,
                raw_attr: filter.to_attr() as u64,
                raw_slot: slot.to_raw(),
                is_negated,
                params: None,
            },
            AbilityFrame::MetaRule { filter, slot, .. } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: self.value(),
                filter: *filter,
                slot: *slot,
                raw_attr: filter.to_attr() as u64,
                raw_slot: slot.to_raw(),
                is_negated,
                params: None,
            },
            AbilityFrame::Raw {
                value, attr, slot, ..
            } => AbilityFrameComponents {
                raw_opcode,
                opcode,
                value: *value,
                filter: CardFilter::from_attr(*attr as i64),
                slot: DecodedSlot::decode(*slot),
                raw_attr: *attr,
                raw_slot: *slot,
                is_negated,
                params: None,
            },
        }
    }

    pub fn value(&self) -> i32 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { count, .. } => *count,
            AbilityFrame::Semantic { value, .. } => *value,
            AbilityFrame::RecoverLive { count, .. } => *count,
            AbilityFrame::RecoverMember { count, .. } => *count,
            AbilityFrame::LookAndChoose { params, .. } => params.to_raw(),
            AbilityFrame::SelectMember { count, .. } => *count,
            AbilityFrame::MoveMember { .. } => 0,
            AbilityFrame::MetaRule { rule_type, .. } => *rule_type,
            AbilityFrame::Raw { value, .. } => *value,
        }
    }

    pub fn attr(&self) -> u64 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { .. } => 0,
            AbilityFrame::Semantic { filter, .. } => filter.to_attr() as u64,
            AbilityFrame::RecoverLive { filter, .. } => filter.to_attr() as u64,
            AbilityFrame::RecoverMember { filter, .. } => filter.to_attr() as u64,
            AbilityFrame::LookAndChoose { filter, .. } => filter.to_attr() as u64,
            AbilityFrame::SelectMember { filter, .. } => filter.to_attr() as u64,
            AbilityFrame::MoveMember { filter, .. } => filter.to_attr() as u64,
            AbilityFrame::MetaRule { filter, .. } => filter.to_attr() as u64,
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
            AbilityFrame::Semantic { slot, .. } => slot.to_raw(),
            AbilityFrame::RecoverLive { slot, .. } => slot.to_raw(),
            AbilityFrame::RecoverMember { slot, .. } => slot.to_raw(),
            AbilityFrame::LookAndChoose { slot, .. } => slot.to_raw(),
            AbilityFrame::SelectMember { slot, .. } => slot.to_raw(),
            AbilityFrame::MoveMember { slot, .. } => slot.to_raw(),
            AbilityFrame::MetaRule { slot, .. } => slot.to_raw(),
            AbilityFrame::Raw { slot, .. } => *slot,
        }
    }

    pub fn raw_opcode(&self) -> i32 {
        self.opcode()
    }
    pub fn raw_value(&self) -> i32 {
        self.value()
    }
    pub fn raw_attr(&self) -> u64 {
        self.attr()
    }
    pub fn raw_slot(&self) -> i32 {
        self.slot()
    }

    pub fn look_choose(
        &self,
    ) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        match self {
            AbilityFrame::LookAndChoose { params, .. } => *params,
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
            AbilityFrame::Semantic { filter, .. } => *filter,
            AbilityFrame::RecoverLive { filter, .. } => *filter,
            AbilityFrame::RecoverMember { filter, .. } => *filter,
            AbilityFrame::LookAndChoose { filter, .. } => *filter,
            AbilityFrame::SelectMember { filter, .. } => *filter,
            AbilityFrame::MoveMember { filter, .. } => *filter,
            AbilityFrame::MetaRule { filter, .. } => CardFilter::from_attr(filter.to_attr() as i64),
            AbilityFrame::Raw { attr, .. } => CardFilter::from_attr((*attr) as i64),
            _ => CardFilter::default(),
        }
    }

    pub fn dslot(&self) -> DecodedSlot {
        match self {
            AbilityFrame::Semantic { slot, .. } => *slot,
            AbilityFrame::RecoverLive { slot, .. } => *slot,
            AbilityFrame::RecoverMember { slot, .. } => *slot,
            AbilityFrame::LookAndChoose { slot, .. } => *slot,
            AbilityFrame::SelectMember { slot, .. } => *slot,
            AbilityFrame::MoveMember { slot, .. } => *slot,
            AbilityFrame::MetaRule { slot, .. } => *slot,
            AbilityFrame::Raw { slot, .. } => DecodedSlot::decode(*slot),
            _ => DecodedSlot::default(),
        }
    }

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
                .get("frames")
                .and_then(|v| v.as_array())
                .map(|frames| !frames.is_empty())
                .unwrap_or(false);

            if has_structured_frames {
                return raw.serialize(serializer);
            }

            let mut merged = raw.as_object().cloned().unwrap_or_default();
            merged.insert(
                "frames".to_string(),
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
            "frames".to_string(),
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
            .get("frames")
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
    pub fn from_words(words: &[i32]) -> Self {
        let decoded = BytecodeProgram::from_slice(words).decode_all();
        let frames = decoded.iter().map(AbilityFrame::from_instruction).collect();

        Self {
            frames,
            raw_program: Some(serde_json::json!({
                "frames": [],
                "bytecode": words,
            })),
        }
    }

    pub fn from_bytecode(bytecode: &[i32]) -> Self {
        Self::from_words(bytecode)
    }

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
    pub value: i32,
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

impl std::hash::Hash for Effect {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.effect_type.hash(state);
        self.value.hash(state);
        self.value_cond.hash(state);
        self.target.hash(state);
        self.is_optional.hash(state);
        self.runtime_opcode.hash(state);
        self.runtime_value.hash(state);
        self.runtime_attr.hash(state);
        self.runtime_slot.hash(state);
        self.modal_options.to_string().hash(state);
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
    #[serde(default)]
    pub modal_options: serde_json::Value,
    #[serde(default)]
    pub option_names: Vec<String>,
    #[serde(default)]
    pub pseudocode: String,
    #[serde(default)]
    pub requires_selection: bool,
    #[serde(default)]
    pub choice_flags: u8,
    #[serde(default)]
    pub choice_count: u8,
    #[serde(default)]
    pub filters: Vec<crate::core::logic::filter::CardFilter>,
    #[serde(default)]
    pub preparsed_modifiers: Vec<PreparsedModifier>,
    #[serde(default, skip_serializing)]
    pub opcodes_mask: u128,
    #[serde(default, skip_serializing)]
    pub sparse_frame_index: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub frame_program: Option<FrameProgram>,
}

impl std::hash::Hash for Ability {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.raw_text.hash(state);
        self.trigger.hash(state);
        self.effects.hash(state);
        self.conditions.hash(state);
        self.costs.hash(state);
        self.is_once_per_turn.hash(state);
        // modal_options is skipped
        self.option_names.hash(state);
        self.pseudocode.hash(state);
        self.requires_selection.hash(state);
        self.choice_flags.hash(state);
        self.choice_count.hash(state);
        self.preparsed_modifiers.hash(state);
        self.opcodes_mask.hash(state);
        self.sparse_frame_index.hash(state);
        self.frame_program.hash(state);
    }
}

impl Ability {
    fn resolved_frame_program(&self) -> Option<FrameProgram> {
        self.frame_program.clone()
    }

    pub fn semantic_frame_program(&self) -> Option<FrameProgram> {
        self.resolved_frame_program()
    }

    pub fn words(&self) -> Vec<i32> {
        self.frame_program
            .as_ref()
            .map_or_else(Vec::new, FrameProgram::to_words)
    }

    pub fn bytecode(&self) -> Vec<i32> {
        self.words()
    }

    pub fn get_frame(&self, frame_idx: usize) -> Option<AbilityFrame> {
        self.frames().get(frame_idx).cloned()
    }

    pub fn frames(&self) -> Vec<AbilityFrame> {
        self.resolved_frame_program()
            .map_or_else(Vec::new, |frame_program| frame_program.frames)
    }

    fn modal_branch_frames_from_program(&self, choice_idx: usize) -> Option<Vec<AbilityFrame>> {
        let program = self.resolved_frame_program()?;
        let select_idx = program
            .frames
            .iter()
            .position(|frame| matches!(frame.opcode(), O_SELECT_MODE | O_OPPONENT_CHOOSE))?;
        let branch_idx = select_idx + 1 + choice_idx;
        let branch = program.frames.get(branch_idx)?;
        let target = if branch.opcode() == O_JUMP {
            let target_idx = branch_idx + 1 + branch.value() as usize;
            program.frames.get(target_idx)?
        } else {
            branch
        };
        Some(vec![target.clone()])
    }

    fn legacy_modal_option_frames_from_effects(
        &self,
        choice_idx: usize,
    ) -> Option<Vec<AbilityFrame>> {
        let effect = self.effects.first()?;
        let options = effect.modal_options.as_array()?;
        options
            .get(choice_idx)
            .and_then(|option| option.as_array())
            .map(|effects| {
                let mut frames = Vec::new();
                for effect_val in effects {
                    if let Ok(effect) = serde_json::from_value::<Effect>(effect_val.clone()) {
                        let mut frame = AbilityFrame::from_effect(&effect);
                        if matches!(frame.opcode(), O_REVEAL_UNTIL)
                            && effect_val
                                .get("params")
                                .and_then(|value| value.as_object())
                                .and_then(|params| params.get("card_type"))
                                .and_then(|value| value.as_str())
                                .map(|value| value.eq_ignore_ascii_case("live"))
                                .unwrap_or(false)
                        {
                            frame = match frame {
                                AbilityFrame::Semantic {
                                    opcode,
                                    value,
                                    filter,
                                    mut slot,
                                    is_negated,
                                    params,
                                } => {
                                    slot.is_reveal_until_live = true;
                                    AbilityFrame::Semantic {
                                        opcode,
                                        value,
                                        filter,
                                        slot,
                                        is_negated,
                                        params,
                                    }
                                }
                                AbilityFrame::Raw {
                                    opcode,
                                    value,
                                    attr,
                                    slot,
                                } => {
                                    let mut decoded_slot = DecodedSlot::decode(slot);
                                    decoded_slot.is_reveal_until_live = true;
                                    AbilityFrame::Raw {
                                        opcode,
                                        value,
                                        attr,
                                        slot: decoded_slot.to_raw(),
                                    }
                                }
                                other => other,
                            };
                        }
                        frames.push(frame);
                    }
                }
                frames
            })
    }

    fn semantic_optional_mode_frames(&self) -> Option<Vec<AbilityFrame>> {
        if self.trigger != TriggerType::OnLiveSuccess {
            return None;
        }

        let frames = self.frames();
        if frames.iter().any(|frame| frame.opcode() == O_SELECT_MODE) {
            return None;
        }

        let option_frames: Vec<AbilityFrame> = frames
            .into_iter()
            .filter(|frame| {
                frame.filter().is_optional
                    && matches!(frame.opcode(), O_ENERGY_CHARGE | O_RECOVER_MEMBER)
            })
            .collect();

        if option_frames.is_empty() {
            None
        } else {
            Some(option_frames)
        }
    }

    fn resolve_modal_option_frames(&self, choice_idx: usize) -> Option<Vec<AbilityFrame>> {
        if let Some(effect) = self.effects.first() {
            if let Some(options) = effect.modal_options.as_array() {
                return options
                    .get(choice_idx)
                    .and_then(|option| option.as_array())
                    .map(|effects| {
                        let mut frames = Vec::new();
                        for effect_val in effects {
                            if let Ok(effect) = serde_json::from_value::<Effect>(effect_val.clone())
                            {
                                let mut frame = AbilityFrame::from_effect(&effect);
                                if matches!(frame.opcode(), O_REVEAL_UNTIL)
                                    && effect_val
                                        .get("params")
                                        .and_then(|value| value.as_object())
                                        .and_then(|params| params.get("card_type"))
                                        .and_then(|value| value.as_str())
                                        .map(|value| value.eq_ignore_ascii_case("live"))
                                        .unwrap_or(false)
                                {
                                    frame = match frame {
                                        AbilityFrame::Semantic {
                                            opcode,
                                            value,
                                            filter,
                                            mut slot,
                                            is_negated,
                                            params,
                                        } => {
                                            slot.is_reveal_until_live = true;
                                            AbilityFrame::Semantic {
                                                opcode,
                                                value,
                                                filter,
                                                slot,
                                                is_negated,
                                                params,
                                            }
                                        }
                                        AbilityFrame::Raw {
                                            opcode,
                                            value,
                                            attr,
                                            slot,
                                        } => {
                                            let mut decoded_slot = DecodedSlot::decode(slot);
                                            decoded_slot.is_reveal_until_live = true;
                                            AbilityFrame::Raw {
                                                opcode,
                                                value,
                                                attr,
                                                slot: decoded_slot.to_raw(),
                                            }
                                        }
                                        other => other,
                                    };
                                }
                                frames.push(frame);
                            }
                        }
                        frames
                    });
            }
        }

        if let Some(frames) = self.semantic_optional_mode_frames() {
            return frames.get(choice_idx).cloned().map(|frame| vec![frame]);
        }

        if let Some(options) = self.modal_options.as_array() {
            return options
                .get(choice_idx)
                .and_then(|option| option.as_array())
                .map(|effects| {
                    effects
                        .iter()
                        .filter_map(|effect_val| {
                            serde_json::from_value::<Effect>(effect_val.clone())
                                .ok()
                                .map(|effect| AbilityFrame::from_effect(&effect))
                        })
                        .collect()
                });
        }

        if let Some(frames) = self.modal_branch_frames_from_program(choice_idx) {
            return Some(frames);
        }

        if let Some(frames) = self.legacy_modal_option_frames_from_effects(choice_idx) {
            return Some(frames);
        }

        None
    }

    pub fn get_modal_option_frames(&self, choice_idx: usize) -> Option<Vec<AbilityFrame>> {
        self.resolve_modal_option_frames(choice_idx)
    }

    pub fn modal_option_count(&self) -> usize {
        if let Some(frames) = self.semantic_optional_mode_frames() {
            return frames.len();
        }

        if let Some(effect) = self.effects.first() {
            if let Some(options) = effect.modal_options.as_array() {
                return options.len();
            }
        }

        if let Some(options) = self.modal_options.as_array() {
            return options.len();
        }

        let mut count = 0;
        while self.resolve_modal_option_frames(count).is_some() {
            count += 1;
        }
        count
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::logic::interpreter::instruction::{BytecodeInstruction, BytecodeProgram};

    #[test]
    fn frame_program_to_words_roundtrips_through_fixed_layout_decoder() {
        let program = FrameProgram {
            frames: vec![
                AbilityFrame::Return,
                AbilityFrame::Raw {
                    opcode: 204,
                    value: 3,
                    attr: 0x1122_3344_5566_7788,
                    slot: 9,
                },
            ],
            raw_program: None,
        };

        let words = program.to_words();
        assert_eq!(words.len(), 10);

        let decoded = BytecodeProgram::from_slice(&words).decode_all();
        assert_eq!(decoded.len(), 2);
        assert_eq!(decoded[0], AbilityFrame::Return.to_instruction());
        assert_eq!(
            decoded[1],
            AbilityFrame::Raw {
                opcode: 204,
                value: 3,
                attr: 0x1122_3344_5566_7788,
                slot: 9
            }
            .to_instruction()
        );
    }

    #[test]
    fn frame_program_from_words_preserves_structured_slots() {
        let bytecode = vec![
            BytecodeInstruction::new(O_RECOVER_LIVE, 1, 0, 0x0001_0080),
            BytecodeInstruction::new(O_RETURN, 0, 0, 0),
        ];
        let program = BytecodeProgram::from_slice(
            &bytecode
                .iter()
                .flat_map(|instr| {
                    [
                        instr.op,
                        instr.v,
                        instr.a as i32,
                        (instr.a >> 32) as i32,
                        instr.raw_s,
                    ]
                })
                .collect::<Vec<_>>(),
        );

        let frame_program = FrameProgram::from_words(program.words());
        assert_eq!(frame_program.frames.len(), 2);
        match &frame_program.frames[0] {
            AbilityFrame::RecoverLive { count, slot, .. } => {
                assert_eq!(*count, 1);
                assert_eq!(slot, &DecodedSlot::decode(0x0001_0080));
            }
            other => panic!("expected RecoverLive frame, got {:?}", other),
        }

        let serialized = serde_json::to_value(&frame_program).unwrap();
        assert_eq!(
            serialized
                .get("frames")
                .and_then(|v| v.as_array())
                .map(|v| v.len()),
            Some(2)
        );
        assert_eq!(
            serialized
                .get("frames")
                .and_then(|v| v.as_array())
                .and_then(|frames| frames.first())
                .and_then(|frame| frame.get("RecoverLive"))
                .and_then(|frame| frame.get("slot"))
                .map(|slot| slot.is_object()),
            Some(true)
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
