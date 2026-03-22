//! # LovecaSim Card Database
//!
//! This module defines the `CardDatabase` which acts as the source of truth for
//! card statistics, images, and bytecode instructions.
//!
//! ## Key Roles:
//! - **Centralized Card Data**: Stores `MemberCard` and `LiveCard` structures.
//! - **Fast Lookups**: Implements a `card_no_to_id` mapping for O(1) lookups by
//!   collector number (e.g., "LL-bp1-001").
//! - **Data Integrity**: Ensures that card IDs are unique and that all referenced
//!   metadata exists.
//!
//! ## Design Strategy:
//! The `CardDatabase` is typically loaded once at startup and shared across
//! game instances. Test helpers like `create_test_db` provide a minimal subset
//! for unit testing.

use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::interpreter::instruction::{
    BytecodeProgram, DecodedFilterAttr, DecodedLookAndChoose, DecodedSlot, WORDS_PER_INSTRUCTION,
};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs;
use std::collections::HashMap;
// use crate::core::generated_constants::*; // Redundant due to enums.rs re-export
// use crate::core::generated_constants::*; // Re-exported by enums.rs
use super::models::*;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MemberCard {
    pub card_id: i32,
    pub card_no: String,
    pub name: String,
    pub cost: u32,
    pub hearts: [u8; 7],
    pub blade_hearts: [u8; 7],
    pub blades: u32,
    pub groups: Vec<u8>,
    pub units: Vec<u8>,
    pub abilities: Vec<Ability>,
    #[serde(alias = "volume_icons")]
    pub note_icons: u32,
    pub draw_icons: u32,
    #[serde(default)]
    pub ability_text: String,
    #[serde(default)]
    pub original_text: String,
    #[serde(default)]
    pub original_text_en: String,
    #[serde(default)]
    pub char_id: u32,
    #[serde(default)]
    pub img_path: String,
    #[serde(default)]
    pub rarity: u8,
    #[serde(default)]
    pub semantic_flags: u32,
    #[serde(default)]
    pub ability_flags: u64,
    #[serde(default)]
    pub synergy_flags: u32,
    #[serde(default)]
    pub cost_flags: u32,
    #[serde(default)]
    pub hearts_board: HeartBoard,
    #[serde(default)]
    pub blade_hearts_board: HeartBoard,
    #[serde(default)]
    pub effect_mask: u64,
    #[serde(default)]
    pub ability_opcodes_mask: u128,
    #[serde(default)]
    pub trigger_mask: u32,
    #[serde(default)]
    pub char_mask: u128,
    #[serde(default)]
    pub has_on_play_choice: bool,
    #[serde(default)]
    pub has_multi_baton: bool,
    #[serde(default)]
    pub has_activated_hand: bool,
    #[serde(default)]
    pub has_activated_stage: bool,
    #[serde(default)]
    pub normalized_name: String,
    #[serde(default)]
    pub base_potential: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct LiveCard {
    pub card_id: i32,
    pub card_no: String,
    pub name: String,
    pub score: u32,
    pub required_hearts: [u8; 7],
    pub abilities: Vec<Ability>,
    pub groups: Vec<u8>,
    pub units: Vec<u8>,
    #[serde(alias = "volume_icons")]
    pub note_icons: u32,
    pub blade_hearts: [u8; 7],
    #[serde(default)]
    pub rare: String,
    #[serde(default)]
    pub ability_text: String,
    #[serde(default)]
    pub original_text: String,
    #[serde(default)]
    pub original_text_en: String,
    #[serde(default)]
    pub img_path: String,
    #[serde(default)]
    pub semantic_flags: u32,
    #[serde(default)]
    pub synergy_flags: u32,
    #[serde(default)]
    pub hearts_board: HeartBoard,
    #[serde(default)]
    pub blade_hearts_board: HeartBoard,
    #[serde(default)]
    pub effect_mask: u64,
    #[serde(default)]
    pub char_mask: u128,
    #[serde(default)]
    pub normalized_name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Card {
    Member(MemberCard),
    Live(LiveCard),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CardDatabase {
    pub members: HashMap<i32, MemberCard>,
    pub lives: HashMap<i32, LiveCard>,
    // Optimization 1: Fast Lookup Vectors
    pub members_vec: Vec<Option<MemberCard>>,
    pub lives_vec: Vec<Option<LiveCard>>,
    // Optimization 2: String No Lookup
    pub card_no_to_id: HashMap<String, i32>,
    pub energy_db: HashMap<i32, EnergyCard>,
    #[serde(skip)]
    pub sparse_ability_index: HashMap<String, Value>,
    #[serde(default)]
    pub is_vanilla: bool,
    #[serde(skip)]
    pub cached_vanilla: Option<bool>,
}

pub const LOGIC_ID_MASK: i32 = 0x0FFF;

impl CardDatabase {
    fn normalize_legacy_tap_member_ability(ability: &mut Ability) {
        let mentions_tap = ability.raw_text.contains("TAP_MEMBER")
            || ability.pseudocode.contains("TAP_MEMBER");
        let mentions_move = ability.raw_text.contains("MOVE_MEMBER")
            || ability.pseudocode.contains("MOVE_MEMBER");
        let has_stale_tap_effect = ability.effects.iter().any(|effect| {
            effect.effect_type == EffectType::TapMember && effect.runtime_opcode == O_MOVE_MEMBER
        });

        if !has_stale_tap_effect && (!mentions_tap || mentions_move) {
            return;
        }

        for effect in &mut ability.effects {
            if effect.effect_type == EffectType::TapMember && effect.runtime_opcode == O_MOVE_MEMBER {
                effect.runtime_opcode = O_TAP_MEMBER;
            }
        }

        for ip in (0..ability.bytecode.len()).step_by(WORDS_PER_INSTRUCTION) {
            if ability.bytecode[ip] == O_MOVE_MEMBER {
                ability.bytecode[ip] = O_TAP_MEMBER;
            }
        }
    }

    fn normalize_member_runtime_compatibility(card: &mut MemberCard) {
        for ability in &mut card.abilities {
            Self::normalize_legacy_tap_member_ability(ability);
        }
    }

    fn normalize_live_runtime_compatibility(card: &mut LiveCard) {
        for ability in &mut card.abilities {
            Self::normalize_legacy_tap_member_ability(ability);
        }
    }

    fn load_sparse_ability_index() -> HashMap<String, Value> {
        // JSON is the canonical format. YAML paths are legacy fallbacks only.
        for path in [
            "data/ability_frame_index.json",
            "../data/ability_frame_index.json",
            "data/ability_frame_index.yaml",
            "../data/ability_frame_index.yaml",
        ] {
            if let Ok(json) = fs::read_to_string(path) {
                let parsed_root = if path.ends_with(".yaml") {
                    serde_yaml::from_str::<serde_yaml::Value>(&json)
                        .ok()
                        .and_then(|yaml| serde_json::to_value(yaml).ok())
                } else {
                    serde_json::from_str::<Value>(&json).ok()
                };

                if let Some(root) = parsed_root {
                    let mut index = HashMap::new();
                    if let Some(abilities) = root.get("abilities").and_then(|v| v.as_array()) {
                        for entry in abilities {
                            let Some(cards) = entry.get("cards").and_then(|v| v.as_array()) else {
                                continue;
                            };
                            for card in cards {
                                if let Some(card_obj) = card.as_object() {
                                    let Some(card_no) = card_obj.get("card_no").and_then(|v| v.as_str()) else {
                                        continue;
                                    };
                                    let Some(ability_index) = card_obj.get("ability_index").and_then(|v| v.as_i64()) else {
                                        continue;
                                    };
                                    let key = format!("{}#{}", card_no, ability_index);
                                    index.insert(key, entry.clone());
                                    continue;
                                }

                                if let Some(card_str) = card.as_str() {
                                    let Some((card_no_part, tail)) = card_str.split_once(" |") else {
                                        continue;
                                    };
                                    let Some(ab_marker) = tail.rfind("(ab#") else {
                                        continue;
                                    };
                                    let ab_fragment = &tail[ab_marker + 4..];
                                    let Some((ability_index_str, _)) = ab_fragment.split_once(' ') else {
                                        continue;
                                    };
                                    let Some(ability_index) = ability_index_str.parse::<i64>().ok() else {
                                        continue;
                                    };
                                    let key = format!("{}#{}", card_no_part.trim(), ability_index);
                                    index.insert(key, entry.clone());
                                }
                            }
                        }
                    }
                    if !index.is_empty() {
                        return index;
                    }
                }
            }
        }
        HashMap::new()
    }

    fn attach_sparse_ability_index(
        card_no: &str,
        abilities: &mut [Ability],
        index: &HashMap<String, Value>,
    ) -> serde_json::Result<()> {
        for (ability_index, ability) in abilities.iter_mut().enumerate() {
            let key = format!("{}#{}", card_no, ability_index);
            let entry = index.get(&key).ok_or_else(|| {
                serde::de::Error::custom(format!(
                    "missing sparse ability index entry for {} ability {}",
                    card_no, ability_index
                ))
            })?;
            ability.sparse_frame_index = Some(entry.clone());
            ability.frame_program = Some(Self::sparse_entry_to_frame_program(entry));
            let rebuilt = Self::sparse_entry_to_bytecode(entry);
            if rebuilt.is_empty() {
                return Err(serde::de::Error::custom(format!(
                    "sparse ability index entry for {} ability {} has no encodable fields",
                    card_no, ability_index
                )));
            }
            ability.bytecode = rebuilt;
            if ability.effects.is_empty() {
                let derived_effects = Self::frame_program_to_effects(ability.frame_program.as_ref().unwrap());
                if !derived_effects.is_empty() {
                    ability.effects = derived_effects;
                }
            }
            if ability.pseudocode.is_empty() {
                if let Some(pseudo) = entry.get("pseudocode").and_then(|v| v.as_str()) {
                    ability.pseudocode = pseudo.to_string();
                }
            }
        }
        Ok(())
    }

    pub fn sparse_entry_to_bytecode(entry: &Value) -> Vec<i32> {
        // Frame-first: rebuild bytecode from the frame model (canonical).
        // source_words is a migration shim; fall back to it only if frames is absent.
        let mut bytecode = Vec::new();
        if let Some(frames) = entry.get("frames").and_then(|v| v.as_array()) {
            if !frames.is_empty() {
                for frame in frames {
                    bytecode.extend(Self::encode_sparse_frame(frame));
                }
                return bytecode;
            }
        }

        // Legacy fallback: source_words (migration shim — remove after suite is green)
        if let Some(words) = entry.get("source_words").and_then(|v| v.as_array()) {
            let source_words: Vec<i32> = words
                .iter()
                .filter_map(|word| word.as_i64().map(|v| v as i32))
                .collect();
            if !source_words.is_empty() {
                return source_words;
            }
        }

        bytecode
    }

    pub fn sparse_entry_to_frame_program(entry: &Value) -> FrameProgram {
        let mut program_frames = Vec::new();
        if let Some(frames) = entry.get("frames").and_then(|v| v.as_array()) {
            for frame in frames {
                program_frames.push(Self::parse_semantic_frame(frame));
            }
        } else if let Some(words) = entry.get("source_words").and_then(|v| v.as_array()) {
            let mut ip = 0;
            while ip + 4 < words.len() {
                let op = words[ip].as_i64().unwrap_or(0) as i32;
                let v = words[ip + 1].as_i64().unwrap_or(0) as i32;
                let a_low = words[ip + 2].as_i64().unwrap_or(0) as u32;
                let a_high = words[ip + 3].as_i64().unwrap_or(0) as u32;
                let a = (a_low as u64) | ((a_high as u64) << 32);
                let s = words[ip + 4].as_i64().unwrap_or(0) as i32;
                program_frames.push(Self::raw_to_semantic_frame(op, v, a, s));
                ip += 5;
            }
        }
        FrameProgram { frames: program_frames }
    }

    fn frame_program_to_effects(frame_program: &FrameProgram) -> Vec<Effect> {
        frame_program
            .frames
            .iter()
            .filter_map(Self::frame_to_effect)
            .collect()
    }

    fn frame_to_effect(frame: &AbilityFrame) -> Option<Effect> {
        let instr = frame.to_instruction();
        let effect_type = match instr.op {
            O_DRAW => EffectType::Draw,
            O_ADD_BLADES => EffectType::AddBlades,
            O_ADD_HEARTS => EffectType::AddHearts,
            O_REDUCE_COST => EffectType::ReduceCost,
            O_LOOK_DECK => EffectType::LookDeck,
            O_RECOVER_LIVE => EffectType::RecoverLive,
            O_BOOST_SCORE => EffectType::BoostScore,
            O_RECOVER_MEMBER => EffectType::RecoverMember,
            O_BUFF_POWER => EffectType::BuffPower,
            O_IMMUNITY => EffectType::Immunity,
            O_MOVE_MEMBER => EffectType::MoveMember,
            O_SWAP_CARDS => EffectType::SwapCards,
            O_SEARCH_DECK => EffectType::SearchDeck,
            O_ENERGY_CHARGE => EffectType::EnergyCharge,
            O_SET_BLADES => EffectType::SetBlades,
            O_SET_HEARTS => EffectType::SetHearts,
            O_FORMATION_CHANGE => EffectType::FormationChange,
            O_NEGATE_EFFECT => EffectType::NegateEffect,
            O_ORDER_DECK => EffectType::OrderDeck,
            O_META_RULE => EffectType::MetaRule,
            O_SELECT_MODE => EffectType::SelectMode,
            O_MOVE_TO_DECK => EffectType::MoveToDeck,
            O_TAP_OPPONENT => EffectType::TapOpponent,
            O_PLACE_UNDER => EffectType::PlaceUnder,
            O_RESTRICTION => EffectType::Restriction,
            O_BATON_TOUCH_MOD => EffectType::BatonTouchMod,
            O_SET_SCORE => EffectType::SetScore,
            O_SWAP_ZONE => EffectType::SwapZone,
            O_TRANSFORM_COLOR => EffectType::TransformColor,
            O_REVEAL_CARDS => EffectType::RevealCards,
            O_LOOK_AND_CHOOSE => EffectType::LookAndChoose,
            O_CHEER_REVEAL => EffectType::CheerReveal,
            O_ACTIVATE_MEMBER => EffectType::ActivateMember,
            O_ADD_TO_HAND => EffectType::AddToHand,
            O_COLOR_SELECT => EffectType::ColorSelect,
            O_TRIGGER_REMOTE => EffectType::TriggerRemote,
            O_REDUCE_HEART_REQ => EffectType::ReduceHeartReq,
            O_MODIFY_SCORE_RULE => EffectType::ModifyScoreRule,
            O_ADD_STAGE_ENERGY => EffectType::AddStageEnergy,
            O_SET_TAPPED => EffectType::SetTapped,
            O_TAP_MEMBER => EffectType::TapMember,
            O_PLAY_MEMBER_FROM_HAND => EffectType::PlayMemberFromHand,
            O_MOVE_TO_DISCARD => EffectType::MoveToDiscard,
            O_GRANT_ABILITY => EffectType::GrantAbility,
            O_INCREASE_HEART_COST => EffectType::IncreaseHeartCost,
            O_REDUCE_YELL_COUNT => EffectType::ReduceYellCount,
            O_PLAY_MEMBER_FROM_DISCARD => EffectType::PlayMemberFromDiscard,
            O_SELECT_MEMBER => EffectType::SelectMember,
            O_DRAW_UNTIL => EffectType::DrawUntil,
            O_SELECT_PLAYER => EffectType::SelectPlayer,
            O_SELECT_LIVE => EffectType::SelectLive,
            O_REVEAL_UNTIL => EffectType::RevealUntil,
            O_INCREASE_COST => EffectType::IncreaseCost,
            O_PREVENT_PLAY_TO_SLOT => EffectType::PreventPlayToSlot,
            O_SWAP_AREA => EffectType::SwapArea,
            O_TRANSFORM_HEART => EffectType::TransformHeart,
            O_SELECT_CARDS => EffectType::SelectCards,
            O_OPPONENT_CHOOSE => EffectType::OpponentChoose,
            O_PLAY_LIVE_FROM_DISCARD => EffectType::PlayLiveFromDiscard,
            O_REDUCE_LIVE_SET_LIMIT => EffectType::ReduceLiveSetLimit,
            O_SET_TARGET_SELF => EffectType::SetTargetSelf,
            O_SET_TARGET_OPPONENT => EffectType::SetTargetOpponent,
            O_PREVENT_SET_TO_SUCCESS_PILE => EffectType::PreventSetToSuccessPile,
            O_ACTIVATE_ENERGY => EffectType::ActivateEnergy,
            O_PREVENT_ACTIVATE => EffectType::PreventActivate,
            O_SET_HEART_COST => EffectType::SetHeartCost,
            O_PREVENT_BATON_TOUCH => EffectType::PreventBatonTouch,
            O_LOOK_DECK_DYNAMIC => EffectType::LookDeckDynamic,
            O_REDUCE_SCORE => EffectType::ReduceScore,
            O_REPEAT_ABILITY => EffectType::RepeatAbility,
            O_LOSE_EXCESS_HEARTS => EffectType::LoseExcessHearts,
            O_SKIP_ACTIVATE_PHASE => EffectType::SkipActivatePhase,
            O_PAY_ENERGY_DYNAMIC => EffectType::PayEnergyDynamic,
            O_PLACE_ENERGY_UNDER_MEMBER => EffectType::PlaceEnergyUnderMember,
            O_CALC_SUM_COST => EffectType::CalcSumCost,
            O_LOOK_REORDER_DISCARD => EffectType::LookReorderDiscard,
            O_DIV_VALUE => EffectType::DivValue,
            O_TRANSFORM_BLADES => EffectType::TransformBlades,
            O_RETURN | O_JUMP | O_JUMP_IF_FALSE | O_PAY_ENERGY | C_SUM_VALUE => return None,
            _ => return None,
        };

        Some(Effect {
            effect_type,
            value: instr.v,
            value_cond: ConditionType::None,
            target: TargetType::Self_,
            is_optional: false,
            params: serde_json::Value::Null,
            runtime_opcode: instr.op,
            runtime_value: instr.v,
            runtime_attr: instr.a as u64,
            runtime_slot: instr.raw_s,
            modal_options: serde_json::Value::Null,
        })
    }

    fn raw_to_semantic_frame(op: i32, v: i32, a: u64, s: i32) -> AbilityFrame {
        let filter = DecodedFilterAttr::decode(a as i64);
        let slot = DecodedSlot::decode(s);
        match op {
            O_RETURN => AbilityFrame::Return,
            O_DRAW => AbilityFrame::Draw { count: v },
            O_RECOVER_LIVE => AbilityFrame::RecoverLive { count: v, filter, slot },
            O_RECOVER_MEMBER => AbilityFrame::RecoverMember { count: v, filter, slot },
            O_LOOK_AND_CHOOSE => AbilityFrame::LookAndChoose {
                params: DecodedLookAndChoose::decode(v),
                filter,
                slot,
            },
            O_SELECT_MEMBER => AbilityFrame::SelectMember { count: v, filter, slot },
            O_MOVE_MEMBER => AbilityFrame::MoveMember { filter, slot },
            O_META_RULE => AbilityFrame::MetaRule { rule_type: v, filter, slot },
            _ => AbilityFrame::Raw { opcode: op, value: v, attr: a, slot: s },
        }
    }

    fn parse_semantic_frame(frame: &Value) -> AbilityFrame {
        let opcode_name = frame.get("opcode").and_then(|v| v.as_str()).unwrap_or("");
        let opcode_id = frame.get("opcode_id").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
        let v = Self::encode_sparse_value(opcode_name, frame.get("value"));
        let a = Self::encode_sparse_attr(opcode_name, frame.get("attr"));
        let s = Self::encode_sparse_slot(frame.get("slot"));

        Self::raw_to_semantic_frame(opcode_id, v, a, s)
    }

    fn encode_sparse_frame(frame: &Value) -> Vec<i32> {
        let opcode_id = frame.get("opcode_id").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
        let opcode_name = frame.get("opcode").and_then(|v| v.as_str()).unwrap_or("");
        let value = frame.get("value");
        let attr = frame.get("attr");
        let slot = frame.get("slot");

        let v = Self::encode_sparse_value(opcode_name, value);
        let a = Self::encode_sparse_attr(opcode_name, attr);
        let s = Self::encode_sparse_slot(slot);
        let a_low = a as u32 as i32;
        let a_high = (a >> 32) as u32 as i32;

        vec![opcode_id, v, a_low, a_high, s]
    }

    fn encode_sparse_value(opcode_name: &str, value: Option<&Value>) -> i32 {
        let Some(value) = value else { return 0; };
        match opcode_name {
            "LOOK_AND_CHOOSE" => {
                if let Some(obj) = value.as_object() {
                    let count = obj.get("count").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                    let char_id_1 = obj.get("char_id_1").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                    let char_id_2 = obj.get("char_id_2").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                    let char_id_3 = obj.get("char_id_3").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                    let reveal = Self::sparse_boolish(obj.get("reveal"));
                    let dest_discard = Self::sparse_boolish(obj.get("dest_discard"));
                    (count & 0xff)
                        | ((char_id_2 & 0x7f) << 8)
                        | ((char_id_1 & 0x7f) << 16)
                        | ((char_id_3 & 0x7f) << 23)
                        | ((reveal & 0x1) << 30)
                        | ((dest_discard & 0x1) << 31)
                } else {
                    value.as_i64().unwrap_or(0) as i32
                }
            }
            "SET_HEART_COST" => {
                if let Some(obj) = value.as_object() {
                    let hearts = obj.get("hearts").and_then(|v| v.as_array());
                    let mut v = 0i32;
                    if let Some(hearts) = hearts {
                        for (idx, heart) in hearts.iter().enumerate().take(7) {
                            let count = heart.as_i64().unwrap_or(0) as i32 & 0xf;
                            v |= count << (idx * 4);
                        }
                    }
                    v
                } else {
                    value.as_i64().unwrap_or(0) as i32
                }
            }
            "CALC_SUM_COST" => {
                if let Some(obj) = value.as_object() {
                    let base_value = obj.get("base_value").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                    let divisor = obj.get("divisor").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
                    (base_value & 0xffff) | ((divisor & 0xffff) << 16)
                } else {
                    value.as_i64().unwrap_or(0) as i32
                }
            }
            _ => {
                if let Some(obj) = value.as_object() {
                    obj.get("raw").and_then(|v| v.as_i64()).unwrap_or_else(|| value.as_i64().unwrap_or(0)) as i32
                } else {
                    value.as_i64().unwrap_or(0) as i32
                }
            }
        }
    }

    fn encode_sparse_attr(opcode_name: &str, attr: Option<&Value>) -> u64 {
        let Some(attr) = attr else { return 0; };
        match opcode_name {
            "SET_HEART_COST" => {
                if let Some(obj) = attr.as_object() {
                    let mut val: u64 = 0;
                    for idx in 1..=8 {
                        let key = format!("req_{}", idx);
                        let req = obj.get(&key).and_then(|v| v.as_i64()).unwrap_or(0) as u64;
                        val |= (req & 0xf) << ((idx - 1) * 4);
                    }
                    let unit_enabled = Self::sparse_boolish(obj.get("unit_enabled")) as u64;
                    let unit_id = obj.get("unit_id").and_then(|v| v.as_i64()).unwrap_or(0) as u64;
                    val |= (unit_enabled & 0x1) << 48;
                    val |= (unit_id & 0x7f) << 49;
                    val
                } else {
                    attr.as_i64().unwrap_or(0) as u64
                }
            }
            _ => {
                if let Some(obj) = attr.as_object() {
                    let mut decoded = DecodedFilterAttr::default();
                    decoded.target_player = obj.get("target_player").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.card_type = obj.get("card_type").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.group_enabled = Self::sparse_boolish(obj.get("group_enabled")) != 0;
                    decoded.group_id = obj.get("group_id").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.is_tapped = Self::sparse_boolish(obj.get("is_tapped")) != 0;
                    decoded.has_blade_heart = Self::sparse_boolish(obj.get("has_blade_heart")) != 0;
                    decoded.not_has_blade_heart = Self::sparse_boolish(obj.get("not_has_blade_heart")) != 0;
                    decoded.unique_names = Self::sparse_boolish(obj.get("unique_names")) != 0;
                    decoded.unit_enabled = Self::sparse_boolish(obj.get("unit_enabled")) != 0;
                    decoded.unit_id = obj.get("unit_id").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.value_enabled = Self::sparse_boolish(obj.get("value_enabled")) != 0;
                    decoded.value_threshold = obj.get("value_threshold").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.is_le = Self::sparse_boolish(obj.get("is_le")) != 0;
                    decoded.is_cost_type = Self::sparse_boolish(obj.get("is_cost_type")) != 0;
                    decoded.color_mask = obj.get("color_mask").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.char_id_1 = obj.get("char_id_1").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.char_id_2 = obj.get("char_id_2").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.char_id_3 = obj.get("char_id_3").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.zone_mask = obj.get("zone_mask").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.special_id = obj.get("special_id").and_then(|v| v.as_i64()).unwrap_or(0) as u8;
                    decoded.is_setsuna = Self::sparse_boolish(obj.get("is_setsuna")) != 0;
                    decoded.compare_accumulated = Self::sparse_boolish(obj.get("compare_accumulated")) != 0;
                    decoded.is_optional = Self::sparse_boolish(obj.get("is_optional")) != 0;
                    decoded.keyword_energy = Self::sparse_boolish(obj.get("keyword_energy")) != 0;
                    decoded.keyword_member = Self::sparse_boolish(obj.get("keyword_member")) != 0;
                    decoded.to_attr()
                } else {
                    attr.as_i64().unwrap_or(0) as u64
                }
            }
        }
    }

    fn encode_sparse_slot(slot: Option<&Value>) -> i32 {
        let Some(slot) = slot else { return 0; };
        if let Some(obj) = slot.as_object() {
            let target_slot = obj.get("target_slot").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let remainder_zone = obj.get("remainder_zone").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let source_zone = obj
                .get("source_zone")
                .map(Self::zone_value_from_sparse)
                .flatten()
                .unwrap_or(0);
            let dest_zone = obj
                .get("dest_zone")
                .map(Self::zone_value_from_sparse)
                .flatten()
                .unwrap_or(0);
            let is_opponent = Self::sparse_boolish(obj.get("is_opponent"));
            let is_reveal_until_live = Self::sparse_boolish(obj.get("is_reveal_until_live"));
            let is_baton_slot = Self::sparse_boolish(obj.get("is_baton_slot"));
            let is_empty_slot = Self::sparse_boolish(obj.get("is_empty_slot"));
            let is_wait = Self::sparse_boolish(obj.get("is_wait"));
            let is_dynamic = Self::sparse_boolish(obj.get("is_dynamic"));
            let area_idx = obj.get("area_idx").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let reveal_or_baton = if is_reveal_until_live != 0 || is_baton_slot != 0 { 1 } else { 0 };
            (target_slot & 0xff)
                | ((remainder_zone & 0xff) << 8)
                | ((source_zone & 0xf) << 16)
                | ((dest_zone & 0xf) << 20)
                | ((is_opponent & 0x1) << 24)
                | ((reveal_or_baton & 0x1) << 25)
                | ((is_empty_slot & 0x1) << 26)
                | ((is_wait & 0x1) << 27)
                | ((is_dynamic & 0x1) << 28)
                | ((area_idx & 0x7) << 29)
        } else {
            slot.as_i64().unwrap_or(0) as i32
        }
    }

    fn sparse_boolish(value: Option<&Value>) -> i32 {
        match value {
            Some(Value::Bool(flag)) => {
                if *flag { 1 } else { 0 }
            }
            Some(Value::Number(num)) => num.as_i64().unwrap_or(0) as i32,
            Some(other) => other.as_i64().unwrap_or(0) as i32,
            None => 0,
        }
    }

    fn zone_value_from_sparse(value: &Value) -> Option<i32> {
        if let Some(raw) = value.as_i64() {
            return Some(raw as i32);
        }
        let name = value.as_str()?.to_ascii_uppercase();
        Some(match name.as_str() {
            "DECK_TOP" => ZONE_DECK_TOP,
            "DECK_BOTTOM" => ZONE_DECK_BOTTOM,
            "ENERGY" => ZONE_ENERGY,
            "STAGE" => ZONE_STAGE,
            "DECK" => ZONE_DECK,
            "HAND" => ZONE_HAND,
            "DISCARD" => ZONE_DISCARD,
            "LIVE_SET" => ZONE_LIVE_SET,
            "SUCCESS_PILE" => ZONE_SUCCESS_PILE,
            "YELL" => ZONE_YELL,
            _ => 0,
        })
    }

    /// Extract the logical ID (0-4095) from a packed card ID.
    pub fn to_logic_id(packed_id: i32) -> usize {
        (packed_id & LOGIC_ID_MASK) as usize
    }

    /// Extract the variant index (0-15) from a packed card ID.
    pub fn to_variant_idx(packed_id: i32) -> u8 {
        ((packed_id >> 12) & 0x0F) as u8
    }

    pub fn compute_effect_mask(abilities: &[Ability]) -> u64 {
        let mut mask = 0u64;
        for ab in abilities {
            let bc = &ab.bytecode;
            if Self::has_opcode_static_fast(bc, O_ADD_BLADES as i32)
                || Self::has_opcode_static_fast(bc, O_SET_BLADES as i32)
                || Self::has_opcode_static_fast(bc, O_BUFF_POWER as i32)
                || Self::has_opcode_static_fast(bc, O_TRANSFORM_BLADES as i32)
            {
                mask |= EFFECT_MASK_BLADE;
            }
            if Self::has_opcode_static_fast(bc, O_ADD_HEARTS as i32)
                || Self::has_opcode_static_fast(bc, O_SET_HEARTS as i32)
                || Self::has_opcode_static_fast(bc, O_TRANSFORM_HEART as i32)
            {
                mask |= EFFECT_MASK_HEART;
            }
            if Self::has_opcode_static_fast(bc, O_REDUCE_COST as i32)
                || Self::has_opcode_static_fast(bc, O_INCREASE_COST as i32)
                || Self::has_opcode_static_fast(bc, O_CALC_SUM_COST as i32)
            {
                mask |= EFFECT_MASK_COST;
            }
            if Self::has_opcode_static_fast(bc, O_REDUCE_HEART_REQ as i32)
                || Self::has_opcode_static_fast(bc, O_SET_HEART_COST as i32)
                || Self::has_opcode_static_fast(bc, O_INCREASE_HEART_COST as i32)
                || Self::has_opcode_static_fast(bc, O_REDUCE_LIVE_SET_LIMIT as i32)
            {
                mask |= EFFECT_MASK_REQ;
            }
            if Self::has_opcode_static_fast(bc, O_GRANT_ABILITY as i32) {
                mask |= EFFECT_MASK_GRANT;
            }
            if Self::has_opcode_static_fast(bc, O_META_RULE as i32)
                || Self::has_opcode_static_fast(bc, O_RESTRICTION as i32)
                || Self::has_opcode_static_fast(bc, O_PREVENT_PLAY_TO_SLOT as i32)
                || Self::has_opcode_static_fast(bc, O_PREVENT_SET_TO_SUCCESS_PILE as i32)
                || Self::has_opcode_static_fast(bc, O_PREVENT_ACTIVATE as i32)
                || Self::has_opcode_static_fast(bc, O_PREVENT_BATON_TOUCH as i32)
            {
                mask |= EFFECT_MASK_RULE;
            }
            if Self::has_opcode_static_fast(bc, O_BOOST_SCORE as i32)
                || Self::has_opcode_static_fast(bc, O_SET_SCORE as i32)
                || Self::has_opcode_static_fast(bc, O_REDUCE_SCORE as i32)
                || Self::has_opcode_static_fast(bc, O_MODIFY_SCORE_RULE as i32)
            {
                mask |= EFFECT_MASK_SCORE;
            }
            if Self::has_opcode_static_fast(bc, O_DRAW as i32)
                || Self::has_opcode_static_fast(bc, O_LOOK_DECK as i32)
                || Self::has_opcode_static_fast(bc, O_SEARCH_DECK as i32)
                || Self::has_opcode_static_fast(bc, O_LOOK_AND_CHOOSE as i32)
                || Self::has_opcode_static_fast(bc, O_ADD_TO_HAND as i32)
                || Self::has_opcode_static_fast(bc, O_DRAW_UNTIL as i32)
                || Self::has_opcode_static_fast(bc, O_REVEAL_UNTIL as i32)
            {
                mask |= EFFECT_MASK_DRAW;
            }
        }
        mask
    }
}

impl Default for CardDatabase {
    fn default() -> Self {
        Self {
            members: HashMap::new(),
            lives: HashMap::new(),
            members_vec: vec![None; 4096],
            lives_vec: vec![None; 4096],
            card_no_to_id: HashMap::new(),
            energy_db: HashMap::new(),
            sparse_ability_index: HashMap::new(),
            is_vanilla: false,
            cached_vanilla: None,
        }
    }
}

impl CardDatabase {
    pub fn enrich_member(&self, card: &mut MemberCard) {
        Self::enrich_member_runtime_metadata(card)
    }

    pub fn enrich_live(&self, card: &mut LiveCard) {
        Self::enrich_live_runtime_metadata(card)
    }

    pub fn enrich_member_runtime_metadata(card: &mut MemberCard) {
        let mut flags = 0u64;
        let mut s_flags = 0u32;
        let mut synergy_flags = 0u32;
        let mut cost_flags = 0u32;
        let mut ability_opcodes_mask = 0u128;
        let mut trigger_mask = 0u32;
        let mut has_on_play_choice = false;
        let mut has_multi_baton = false;
        let mut has_activated_hand = false;
        let mut has_activated_stage = false;

        let flagged_ops = [
            O_DRAW,
            O_RECOVER_MEMBER,
            O_RECOVER_LIVE,
            O_ADD_BLADES,
            O_ADD_HEARTS,
            O_SEARCH_DECK,
            O_BOOST_SCORE,
            O_ENERGY_CHARGE,
            O_MOVE_MEMBER,
            O_SWAP_CARDS,
            O_TAP_OPPONENT,
            O_MODIFY_SCORE_RULE,
            O_REDUCE_COST,
            O_REDUCE_HEART_REQ,
            O_RETURN,
            O_LOOK_AND_CHOOSE,
            O_TAP_MEMBER,
            O_ACTIVATE_MEMBER,
            O_SET_TAPPED,
            O_TRANSFORM_COLOR,
        ];

        for ab in &mut card.abilities {
            if ab.trigger == TriggerType::OnPlay {
                s_flags |= 0x01;
            }
            if ab.trigger == TriggerType::Activated {
                s_flags |= 0x02;
            }
            if ab.trigger == TriggerType::TurnStart || ab.trigger == TriggerType::TurnEnd {
                s_flags |= 0x04;
            }
            if ab.is_once_per_turn {
                s_flags |= 0x08;
            }

            ab.preparsed_modifiers.clear();
            ab.opcodes_mask = 0;

            let mut ability_flags_for_ab = 0u64;
            let mut unflagged_logic_present = false;

            let program = ab.bytecode_program();
            let mut ip = 0;
            while let Some(instr) = program.instruction_at(ip) {
                let op = instr.op;

                match op {
                    O_RETURN | O_LOOK_AND_CHOOSE => ability_flags_for_ab |= FLAG_DRAW as u64,
                    O_SEARCH_DECK => ability_flags_for_ab |= FLAG_SEARCH as u64,
                    O_RECOVER_LIVE | O_RECOVER_MEMBER => ability_flags_for_ab |= FLAG_RECOVER as u64,
                    O_ADD_BLADES | O_ADD_HEARTS => ability_flags_for_ab |= FLAG_BUFF as u64,
                    O_MOVE_MEMBER | O_SWAP_CARDS => ability_flags_for_ab |= FLAG_MOVE as u64,
                    O_TAP_OPPONENT | O_TAP_MEMBER => ability_flags_for_ab |= FLAG_TAP as u64,
                    O_ENERGY_CHARGE => ability_flags_for_ab |= FLAG_CHARGE as u64,
                    O_ACTIVATE_MEMBER | O_SET_TAPPED => ability_flags_for_ab |= FLAG_TEMPO as u64,
                    O_REDUCE_COST => ability_flags_for_ab |= FLAG_REDUCE as u64,
                    O_BOOST_SCORE => ability_flags_for_ab |= FLAG_BOOST as u64,
                    O_TRANSFORM_COLOR => ability_flags_for_ab |= FLAG_TRANSFORM as u64,
                    O_REDUCE_HEART_REQ => ability_flags_for_ab |= FLAG_WIN_COND as u64,
                    _ => {}
                }

                match op {
                    O_LOOK_AND_CHOOSE => {
                        ab.choice_flags |= CHOICE_FLAG_LOOK;
                        if ab.choice_count == 0 {
                            let v = instr.v;
                            let pick = (v >> 8) & 0xFF;
                            if pick > 0 {
                                ab.choice_count = pick as u8;
                            } else {
                                let effect_pick = ab
                                    .effects
                                    .iter()
                                    .find(|effect| {
                                        effect.runtime_opcode == O_LOOK_AND_CHOOSE
                                            || effect.effect_type == EffectType::LookAndChoose
                                    })
                                    .and_then(|effect| effect.params.get("choose_count"))
                                    .and_then(|value| value.as_u64())
                                    .map(|value| value as u8)
                                    .unwrap_or(0);
                                ab.choice_count = if effect_pick > 0 { effect_pick } else { 3 };
                            }
                        }
                    }
                    O_SELECT_MODE => {
                        ab.choice_flags |= CHOICE_FLAG_MODE;
                        if ab.choice_count == 0 {
                            ab.choice_count = instr.v as u8;
                        }
                    }
                    O_COLOR_SELECT => {
                        ab.choice_flags |= CHOICE_FLAG_COLOR;
                        if ab.choice_count == 0 {
                            ab.choice_count = 6;
                        }
                    }
                    O_ORDER_DECK => {
                        ab.choice_flags |= CHOICE_FLAG_ORDER;
                        if ab.choice_count == 0 {
                            ab.choice_count = 3;
                        }
                    }
                    _ => {}
                }

                ab.opcodes_mask |= 1u128 << (op as u32 % 128);
                ability_opcodes_mask |= ab.opcodes_mask;
                trigger_mask |= 1u32 << (ab.trigger as u32 % 32);

                if op == O_BATON_TOUCH_MOD && instr.v >= 2 {
                    has_multi_baton = true;
                }

                if [O_ADD_BLADES, O_ADD_HEARTS, O_BUFF_POWER, O_REDUCE_COST, O_INCREASE_COST, O_SET_HEART_COST]
                    .contains(&op)
                {
                    let val = instr.v;
                    let attr = instr.a as u64;
                    let slot = instr.raw_s;
                    ab.preparsed_modifiers.push(PreparsedModifier { op, val, attr, slot });
                }

                if !flagged_ops.contains(&op) {
                    unflagged_logic_present = true;
                }

                ip = program.next_ip(ip);
            }

            if ab.trigger == TriggerType::OnPlay && ab.choice_flags != 0 {
                has_on_play_choice = true;
            }

            if ab.trigger == TriggerType::Activated {
                let mut area_hand = false;
                let mut area_stage = false;
                for cond in &ab.conditions {
                    if cond.condition_type == ConditionType::AreaCheck {
                        if let Some(arr) = cond.params.as_array() {
                            if arr.iter().any(|v| v.as_i64() == Some(6)) {
                                area_hand = true;
                            }
                            if arr
                                .iter()
                                .any(|v| (0..3).any(|s| v.as_i64() == Some(s as i64)))
                            {
                                area_stage = true;
                            }
                        }
                    }
                }
                if !area_hand && !area_stage {
                    area_stage = true;
                }
                if area_hand {
                    has_activated_hand = true;
                }
                if area_stage {
                    has_activated_stage = true;
                }
            }

            flags |= ability_flags_for_ab;
            if unflagged_logic_present {
                s_flags |= 0x10;
            }

            for c in &ab.conditions {
                match c.condition_type {
                    ConditionType::CountGroup | ConditionType::SelfIsGroup => {
                        synergy_flags |= SYN_FLAG_GROUP
                    }
                    ConditionType::HasColor => synergy_flags |= SYN_FLAG_COLOR,
                    ConditionType::Baton => synergy_flags |= SYN_FLAG_BATON,
                    ConditionType::IsCenter => synergy_flags |= SYN_FLAG_CENTER,
                    ConditionType::LifeLead => synergy_flags |= SYN_FLAG_LIFE_LEAD,
                    _ => {}
                }
            }

            for c in &ab.costs {
                match c.cost_type {
                    AbilityCostType::DiscardHand | AbilityCostType::DiscardMember => {
                        cost_flags |= COST_FLAG_DISCARD as u32
                    }
                    AbilityCostType::TapSelf | AbilityCostType::TapMember => {
                        cost_flags |= COST_FLAG_TAP as u32
                    }
                    _ => {}
                }
            }
        }

        card.ability_flags = flags;
        card.semantic_flags = s_flags;
        card.synergy_flags = synergy_flags;
        card.cost_flags = cost_flags;
        card.ability_opcodes_mask = ability_opcodes_mask;
        card.trigger_mask = trigger_mask;
        card.has_on_play_choice = has_on_play_choice;
        card.has_multi_baton = has_multi_baton;
        card.has_activated_hand = has_activated_hand;
        card.has_activated_stage = has_activated_stage;

        if card.hearts_board.0 == 0 {
            card.hearts_board = HeartBoard::from_array(&card.hearts);
        }
        if card.blade_hearts_board.0 == 0 {
            card.blade_hearts_board = HeartBoard::from_array(&card.blade_hearts);
        }

        let mut mask = 0u128;
        if card.char_id > 0 && card.char_id < 128 {
            mask |= 1u128 << card.char_id;
        }

        // Parity scan (matches original string-based logic)
        for (idx, char_name) in CHARACTER_NAMES.iter().enumerate() {
            if idx == 0 || char_name.is_empty() {
                continue;
            }
            if card.name.contains(char_name) {
                mask |= 1u128 << idx;
            }
        }
        card.char_mask = mask;

        if card.name.contains("せつ菜") {
            card.semantic_flags |= 0x100; // Bit 8: Setsuna
        }
        if card.name.contains("澁谷かのん") {
            card.semantic_flags |= 0x200; // Bit 9: Kanon
        }
        if card.name.contains("MY舞") {
            card.semantic_flags |= 0x400; // Bit 10: MY舞
        }

        card.effect_mask = Self::compute_effect_mask(&card.abilities);
        card.normalized_name = card.name.replace(" ", "");

        // Precompute base potential
        let mut score = 0.0;
        let stat_sum: u32 = card.hearts.iter().map(|&x| x as u32).sum();
        score += (card.blades as f32 * 10.0 + stat_sum as f32) / (card.cost as f32 + 1.0);

        let f = card.ability_flags;
        if (f & FLAG_DRAW as u64) != 0 { score += 5.0; }
        if (f & FLAG_SEARCH as u64) != 0 { score += 5.0; }
        if (f & FLAG_RECOVER as u64) != 0 { score += 0.5; }
        if (f & FLAG_BUFF as u64) != 0 { score += 0.4; }
        if (f & FLAG_CHARGE as u64) != 0 { score += 1.2; }
        if (f & FLAG_TEMPO as u64) != 0 { score += 0.3; }
        if (f & FLAG_REDUCE as u64) != 0 { score += 0.6; }
        if (f & FLAG_BOOST as u64) != 0 { score += 0.6; }
        if (f & FLAG_TRANSFORM as u64) != 0 { score += 0.4; }
        if (f & FLAG_WIN_COND as u64) != 0 { score += 1.0; }

        if (card.synergy_flags & SYN_FLAG_GROUP) != 0 { score += 0.3; }
        if (card.synergy_flags & SYN_FLAG_CENTER) != 0 { score += 0.5; }
        if (card.cost_flags & COST_FLAG_TAP as u32) != 0 { score += 0.2; }
        
        card.base_potential = score;
    }

    pub fn enrich_live_runtime_metadata(card: &mut LiveCard) {
        let mut s_flags = 0u32;
        let mut synergy_flags = 0u32;

        for ab in &card.abilities {
            if ab.trigger == TriggerType::OnPlay {
                s_flags |= 0x01;
            }

            for c in &ab.conditions {
                match c.condition_type {
                    ConditionType::CountGroup | ConditionType::SelfIsGroup => {
                        synergy_flags |= SYN_FLAG_GROUP
                    }
                    ConditionType::HasColor => synergy_flags |= SYN_FLAG_COLOR,
                    ConditionType::Baton => synergy_flags |= SYN_FLAG_BATON,
                    ConditionType::IsCenter => synergy_flags |= SYN_FLAG_CENTER,
                    ConditionType::LifeLead => synergy_flags |= SYN_FLAG_LIFE_LEAD,
                    _ => {}
                }
            }
        }

        card.semantic_flags = s_flags;
        card.synergy_flags = synergy_flags;

        if card.hearts_board.0 == 0 {
            card.hearts_board = HeartBoard::from_array(&card.required_hearts);
        }
        if card.blade_hearts_board.0 == 0 {
            card.blade_hearts_board = HeartBoard::from_array(&card.blade_hearts);
        }

        let mut mask = 0u128;
        for (idx, char_name) in CHARACTER_NAMES.iter().enumerate() {
            if idx == 0 || char_name.is_empty() {
                continue;
            }
            if card.name.contains(char_name) {
                mask |= 1u128 << idx;
            }
        }
        card.char_mask = mask;

        if card.name.contains("せつ菜") {
            card.semantic_flags |= 0x100; // Bit 8: Setsuna
        }
        if card.name.contains("澁谷かのん") {
            card.semantic_flags |= 0x200; // Bit 9: Kanon
        }
        if card.name.contains("MY舞") {
            card.semantic_flags |= 0x400; // Bit 10: MY舞
        }

        card.effect_mask = Self::compute_effect_mask(&card.abilities);
        card.normalized_name = card.name.replace(" ", "");
    }

    pub fn from_json(json_str: &str) -> serde_json::Result<Self> {
        let raw: serde_json::Value = serde_json::from_str(json_str)?;
        Self::from_value(raw)
    }

    pub fn from_value(raw: serde_json::Value) -> serde_json::Result<Self> {
        let mut db = Self {
            members: HashMap::new(),
            lives: HashMap::new(),
            members_vec: vec![None; 4096],
            lives_vec: vec![None; 4096],
            card_no_to_id: HashMap::new(),
            energy_db: HashMap::new(),
            sparse_ability_index: Self::load_sparse_ability_index(),
            is_vanilla: false,
            cached_vanilla: None,
        };


        if let Some(members_raw) = raw.get("member_db").and_then(|m| m.as_object()) {
            for (_, val) in members_raw {
                match serde_json::from_value::<MemberCard>(val.clone()) {
                    Ok(mut card) => {
                        Self::normalize_member_runtime_compatibility(&mut card);
                        Self::enrich_member_runtime_metadata(&mut card);
                        Self::attach_sparse_ability_index(
                            &card.card_no,
                            &mut card.abilities,
                            &db.sparse_ability_index,
                        )?;

                        db.members.insert(card.card_id, card.clone());
                        db.card_no_to_id.insert(card.card_no.clone(), card.card_id);

                        // Populate Vector (Logic Deduplication)
                        let logic_id = Self::to_logic_id(card.card_id);
                        if logic_id < db.members_vec.len() {
                            if db.members_vec[logic_id].is_none()
                                || Self::to_variant_idx(card.card_id) == 0
                            {
                                db.members_vec[logic_id] = Some(card.clone());
                            }
                        }
                    }
                    Err(e) => {
                        println!(
                            "[DB] ERROR: Failed to parse Member card {}: {}",
                            val["card_no"], e
                        );
                    }
                }
            }
        }

        if let Some(lives_raw) = raw.get("live_db").and_then(|l| l.as_object()) {
            for (_, val) in lives_raw {
                match serde_json::from_value::<LiveCard>(val.clone()) {
                    Ok(mut card) => {
                        Self::normalize_live_runtime_compatibility(&mut card);
                        Self::enrich_live_runtime_metadata(&mut card);
                        Self::attach_sparse_ability_index(
                            &card.card_no,
                            &mut card.abilities,
                            &db.sparse_ability_index,
                        )?;

                        db.lives.insert(card.card_id, card.clone());
                        db.card_no_to_id.insert(card.card_no.clone(), card.card_id);

                        // Populate Vector (Logic Deduplication)
                        let logic_id = Self::to_logic_id(card.card_id);
                        if logic_id < db.lives_vec.len() {
                            if db.lives_vec[logic_id].is_none()
                                || Self::to_variant_idx(card.card_id) == 0
                            {
                                db.lives_vec[logic_id] = Some(card.clone());
                            }
                        }
                    }
                    Err(e) => {
                        println!(
                            "[DB] ERROR: Failed to parse Live card {}: {}",
                            val["card_no"], e
                        );
                    }
                }
            }
        }

        if let Some(energy_raw) = raw.get("energy_db").and_then(|e| e.as_object()) {
            for (_, val) in energy_raw {
                match serde_json::from_value::<EnergyCard>(val.clone()) {
                    Ok(card) => {
                        db.energy_db.insert(card.card_id, card);
                    }
                    Err(e) => {
                        println!(
                            "[DB] ERROR: Failed to parse Energy card {}: {}",
                            val["card_no"], e
                        );
                    }
                }
            }
        }

        db.cached_vanilla = Some(db.is_vanilla || db.detect_abilityless());

        Ok(db)
    }

    // Fast Lookups
    pub fn get_member(&self, id: i32) -> Option<&MemberCard> {
        // Fast path: Try vector (O(1)) and confirm exact ID match
        let logic_id = Self::to_logic_id(id);
        if logic_id < self.members_vec.len() {
            if let Some(m) = &self.members_vec[logic_id] {
                if m.card_id == id {
                    return Some(m);
                }
            }
        }
        
        // Slow path: Try HashMap
        if let Some(m) = self.members.get(&id) {
            return Some(m);
        }
        None
    }

    pub fn get_live(&self, id: i32) -> Option<&LiveCard> {
        // Fast path: Try vector (O(1)) and confirm exact ID match
        let logic_id = Self::to_logic_id(id);
        if logic_id < self.lives_vec.len() {
            if let Some(l) = &self.lives_vec[logic_id] {
                if l.card_id == id {
                    return Some(l);
                }
            }
        }
        
        // Slow path: Try HashMap
        if let Some(l) = self.lives.get(&id) {
            return Some(l);
        }
        None
    }

    pub fn id_by_no(&self, card_no: &str) -> Option<i32> {
        self.card_no_to_id.get(card_no).copied()
    }

    pub fn get_name(&self, id: i32) -> Option<String> {
        if let Some(m) = self.get_member(id) {
            return Some(m.name.clone());
        }
        if let Some(l) = self.get_live(id) {
            return Some(l.name.clone());
        }
        None
    }

    /// Detect vanilla mode by checking if **all** member cards have empty abilities.
    /// This is more reliable than the is_vanilla flag which might not propagate correctly through Arc cloning.
    pub fn detect_abilityless(&self) -> bool {
        if self.members.is_empty() {
            return false; // If no members loaded, not vanilla
        }

        self.members.values().all(|card| card.abilities.is_empty())
    }

    /// Check if vanilla mode is enabled (explicitly set OR detected from database).
    /// Use this instead of just checking is_vanilla flag.
    pub fn is_truly_vanilla(&self) -> bool {
        if let Some(cached) = self.cached_vanilla {
            return cached;
        }
        self.is_vanilla || self.detect_abilityless()
    }

    // Static opcode check
    pub fn has_opcode_static(bytecode: &[i32], target_op: i32) -> bool {
        BytecodeProgram::from_slice(bytecode).has_opcode(target_op)
    }

    // Optimized opcode check that just checks 0th element of chunks(5)
    pub fn has_opcode_static_fast(bytecode: &[i32], target_op: i32) -> bool {
        BytecodeProgram::from_slice(bytecode).has_opcode(target_op)
    }

    pub fn to_binary(&self) -> bincode::Result<Vec<u8>> {
        bincode::serialize(self)
    }

    pub fn from_binary(data: &[u8]) -> bincode::Result<Self> {
        bincode::deserialize(data)
    }
}

pub fn bytecode_has_choice(bytecode: &[i32]) -> bool {
    let program = BytecodeProgram::from_slice(bytecode);
    let mut ip = 0;
    while let Some(instr) = program.instruction_at(ip) {
        let op = instr.op;
        if op == O_SELECT_MODE
            || op == O_LOOK_AND_CHOOSE
            || op == O_COLOR_SELECT
            || op == O_TAP_OPPONENT
            || op == O_ORDER_DECK
            || op == O_PLAY_MEMBER_FROM_HAND
            || op == O_PLAY_MEMBER_FROM_DISCARD
            || op == O_OPPONENT_CHOOSE
        {
            return true;
        }
        ip = program.next_ip(ip);
    }
    false
}

pub fn bytecode_needs_early_pause(bytecode: &[i32]) -> bool {
    let program = BytecodeProgram::from_slice(bytecode);
    let mut ip = 0;
    while let Some(instr) = program.instruction_at(ip) {
        let op = instr.op;
        if op == O_SELECT_MODE || op == O_COLOR_SELECT || op == O_LOOK_AND_CHOOSE {
            return true;
        }
        ip = program.next_ip(ip);
    }
    false
}

pub fn bytecode_needs_early_pause_opcode(bytecode: &[i32]) -> i32 {
    let program = BytecodeProgram::from_slice(bytecode);
    let mut ip = 0;
    while let Some(instr) = program.instruction_at(ip) {
        let op = instr.op;
        if op == O_SELECT_MODE || op == O_COLOR_SELECT || op == O_LOOK_AND_CHOOSE {
            return op;
        }
        ip = program.next_ip(ip);
    }
    -1
}

pub const CHARACTER_NAMES: [&str; 78] = [
    "", // 0
    "高坂穂乃果",
    "絢瀬絵里",
    "南ことり",
    "園田海未",
    "星空凛", // 1-5
    "西木野真姫",
    "東條希",
    "小泉花陽",
    "矢澤にこ",
    "", // 6-10
    "高海千歌",
    "桜内梨子",
    "松浦果南",
    "黒澤ダイヤ",
    "渡辺曜", // 11-15
    "津島善子",
    "国木田花丸",
    "小原鞠莉",
    "黒澤ルビィ",
    "", // 16-20
    "上原歩夢",
    "中須かすみ",
    "桜坂しずく",
    "朝香果林",
    "宮下愛", // 21-25
    "近江彼方",
    "優木せつ菜",
    "エマ・ヴェルデ",
    "天王寺璃奈",
    "三船栞子", // 26-30
    "ミア・テイラー",
    "鐘嵐珠",
    "高咲侑",
    "",
    "",
    "",
    "",
    "",
    "",
    "", // 31-40
    "澁谷かのん",
    "唐可可",
    "嵐千砂都",
    "平安名すみれ",
    "葉月恋", // 41-45
    "桜小路きな子",
    "米女メイ",
    "若菜四季",
    "鬼塚夏美",
    "ウィーン・マルガレーテ", // 46-50
    "鬼塚冬毬",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "", // 51-60
    "日野下花帆",
    "村野さやか",
    "乙宗梢",
    "夕霧綴理",
    "大沢瑠璃乃", // 61-65
    "藤島慈",
    "百生吟子",
    "徒町小鈴",
    "安養寺姫芽", // 66-69
    "", // 70
    "綺羅ツバサ",
    "統堂英玲奈",
    "優木あんじゅ",
    "聖澤悠奈",
    "柊摩央",
    "鹿角聖良",
    "鹿角理亞", // 71-77
];

pub fn get_character_name(id: u8) -> &'static str {
    CHARACTER_NAMES.get(id as usize).copied().unwrap_or("")
}

pub fn get_trigger_label(trigger: TriggerType) -> &'static str {
    match trigger {
        TriggerType::OnPlay => "【登場】",
        TriggerType::OnLiveStart => "【開始】",
        TriggerType::OnLiveSuccess => "【成功】",
        TriggerType::TurnStart => "【ターン開始】",
        TriggerType::TurnEnd => "【ターン終了】",
        TriggerType::Constant => "【常時】",
        TriggerType::Activated => "【起動】",
        TriggerType::OnLeaves => "【退場】",
        TriggerType::OnReveal => "【公開】",
        TriggerType::OnPositionChange => "【移動】",
        TriggerType::OnAbilityResolve => "【解決】",
        TriggerType::OnAbilitySuccess => "【成功】",
        TriggerType::OnMoveToDiscard => "【控え室】",
        TriggerType::OnMemberTap => "【タップ】",
        TriggerType::None => "",
    }
}
