//! # LovecaSim Card Database
//!
//! This module defines the `CardDatabase` which acts as the source of truth for
//! card statistics, images, and semantic frame instructions.
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
use crate::core::logic::interpreter::conditions::common::parse_condition_type;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use super::models::*;

// Custom deserializer to handle both arrays and objects for groups/units fields
fn deserialize_u8_array<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let value = Value::deserialize(deserializer)?;
    match value {
        Value::Array(arr) => {
            let mut result = Vec::new();
            for item in arr {
                if let Some(num) = item.as_u64() {
                    result.push(num as u8);
                }
            }
            Ok(result)
        }
        Value::Object(_) => {
            // If it's an object, ignore it and return empty vec
            Ok(Vec::new())
        }
        _ => Ok(Vec::new()),
    }
}

/// Reference to a card in the database (either Member or Live)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CardRef {
    Member(MemberCard),
    Live(LiveCard),
    Energy(EnergyCard),
}

impl CardRef {
    /// Get abilities from the card
    pub fn abilities(&self) -> &[Ability] {
        match self {
            CardRef::Member(m) => &m.abilities,
            CardRef::Live(l) => &l.abilities,
            CardRef::Energy(_) => &[],
        }
    }
}

// Consolidated abilities is the single runtime-friendly view of the authored
// frame data. Keep the legacy frame index only as a fallback so older exports
// still load, but make the canonical path obvious.
const EMBEDDED_CONSOLIDATED_ABILITIES_JSON: &str =
    include_str!("../../../../data/consolidated_abilities.json");
const EMBEDDED_ABILITY_FRAME_INDEX_JSON: &str =
    include_str!("../../../../data/ability_frame_index.json");
const LEGACY_CARD_ID_MAPPING_JSON: &str = include_str!("../../../../data/card_id_mapping.json");

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MemberCard {
    pub card_id: i32,
    pub card_no: String,
    pub name: String,
    pub cost: u32,
    pub hearts: [u8; 7],
    pub blade_hearts: [u8; 7],
    pub blades: u32,
    #[serde(default, deserialize_with = "deserialize_u8_array")]
    pub groups: Vec<u8>,
    #[serde(default, deserialize_with = "deserialize_u8_array")]
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
    #[serde(default, deserialize_with = "deserialize_u8_array")]
    pub groups: Vec<u8>,
    #[serde(default, deserialize_with = "deserialize_u8_array")]
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
    #[serde(skip)]
    pub legacy_id_aliases: HashMap<i32, i32>,
    #[serde(default)]
    pub is_vanilla: bool,
    #[serde(skip)]
    pub cached_vanilla: Option<bool>,
}

pub const LOGIC_ID_MASK: i32 = 0x0FFF;

impl CardDatabase {
    fn normalize_card_no(card_no: &str) -> String {
        card_no.replace('＋', "+")
    }

    fn load_sparse_ability_index_from_json(json: &str) -> HashMap<String, Value> {
        let parsed_root = serde_json::from_str::<Value>(json).ok();
        if let Some(root) = parsed_root {
            let mut index = HashMap::new();
            if let Some(abilities) = root.get("abilities").and_then(|v| v.as_array()) {
                for entry in abilities {
                    let refs = entry
                        .get("card_refs")
                        .and_then(|v| v.as_array())
                        .or_else(|| entry.get("cards").and_then(|v| v.as_array()));
                    let Some(cards) = refs else {
                        continue;
                    };
                    let compact_entry = Self::compact_sparse_ability_entry(entry);
                    for card in cards {
                        if let Some(card_obj) = card.as_object() {
                            let Some(card_no) = card_obj.get("card_no").and_then(|v| v.as_str())
                            else {
                                continue;
                            };
                            let Some(ability_index) =
                                card_obj.get("ability_index").and_then(|v| v.as_i64())
                            else {
                                continue;
                            };
                            let key = format!("{}#{}", card_no, ability_index);
                            index.insert(key, compact_entry.clone());
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
                            index.insert(key, compact_entry.clone());
                        }
                    }
                }
            }
            return index;
        }
        HashMap::new()
    }

    fn normalize_legacy_tap_member_ability(ability: &mut Ability) {
        let has_stale_tap_effect = ability.effects.iter().any(|effect| {
            effect.effect_type == EffectType::TapMember && effect.runtime_opcode == O_MOVE_MEMBER
        });

        if !has_stale_tap_effect {
            return;
        }

        let opcodes: Vec<i32> = ability.frames().iter().map(AbilityFrame::opcode).collect();

        let mentions_tap =
            ability.raw_text.contains("TAP_MEMBER") || opcodes.iter().any(|op| *op == O_TAP_MEMBER);
        let mentions_move = ability.raw_text.contains("MOVE_MEMBER")
            || opcodes.iter().any(|op| *op == O_MOVE_MEMBER);

        if !mentions_tap || mentions_move {
            return;
        }

        for effect in &mut ability.effects {
            if effect.effect_type == EffectType::TapMember && effect.runtime_opcode == O_MOVE_MEMBER
            {
                effect.runtime_opcode = O_TAP_MEMBER;
            }
        }

        if let Some(program) = &mut ability.frame_program {
            for frame in &mut program.frames {
                if frame.opcode() == O_MOVE_MEMBER {
                    match frame.clone() {
                        AbilityFrame::MoveMember { filter, slot, .. } => {
                            *frame = AbilityFrame::Semantic {
                                opcode: O_TAP_MEMBER,
                                value: 0,
                                filter,
                                slot,
                                is_negated: false,
                                is_cost: false,
                                params: serde_json::Value::Null,
                            };
                        }
                        AbilityFrame::Semantic { ref mut opcode, .. } => *opcode = O_TAP_MEMBER,
                        AbilityFrame::Raw { ref mut opcode, .. } => *opcode = O_TAP_MEMBER,
                        _ => {}
                    }
                }
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

    fn derive_conditions_from_frame_program(program: &FrameProgram) -> Vec<Condition> {
        let mut conditions = Vec::new();
        for frame in &program.frames {
            let components = frame.components();
            let opcode = components.opcode;
            let is_raw_condition = components
                .params
                .and_then(|params| params.as_object())
                .map(|params| params.get("raw_cond").is_some() || params.get("RAW_COND").is_some())
                .unwrap_or(false);
            let is_condition_opcode = is_raw_condition
                || (opcode >= crate::core::logic::constants::CONDITION_START_1
                    && opcode <= crate::core::logic::constants::CONDITION_END_1)
                || (opcode >= crate::core::logic::constants::CONDITION_START_2
                    && opcode <= crate::core::logic::constants::CONDITION_END_2);
            if !is_condition_opcode {
                if !conditions.is_empty() {
                    break;
                }
                continue;
            }

            conditions.push(Condition {
                condition_type: parse_condition_type(opcode),
                value: components.value,
                attr: components.raw_attr,
                target_slot: components.raw_slot as u8,
                is_negated: components.is_negated,
                params: components.params.cloned().unwrap_or_default(),
            });
        }
        conditions
    }

    fn load_sparse_ability_index() -> HashMap<String, Value> {
        for path in [
            "data/ability_frame_index.json",
            "../data/ability_frame_index.json",
            "data/consolidated_abilities.json",
            "../data/consolidated_abilities.json",
        ] {
            if let Ok(json) = fs::read_to_string(path) {
                let index = Self::load_sparse_ability_index_from_json(&json);
                if !index.is_empty() {
                    return index;
                }
            }
        }

        let consolidated =
            Self::load_sparse_ability_index_from_json(EMBEDDED_CONSOLIDATED_ABILITIES_JSON);
        if !consolidated.is_empty() {
            return consolidated;
        }

        let embedded = Self::load_sparse_ability_index_from_json(EMBEDDED_ABILITY_FRAME_INDEX_JSON);
        if !embedded.is_empty() {
            return embedded;
        }

        HashMap::new()
    }

    fn load_legacy_id_aliases(card_no_to_id: &HashMap<String, i32>) -> HashMap<i32, i32> {
        let mut aliases = HashMap::new();
        let legacy_map = serde_json::from_str::<HashMap<String, i32>>(LEGACY_CARD_ID_MAPPING_JSON)
            .unwrap_or_default();

        for (card_no, legacy_id) in legacy_map {
            let normalized = Self::normalize_card_no(&card_no);
            if let Some(&current_id) = card_no_to_id.get(&normalized) {
                if current_id != legacy_id {
                    aliases.insert(legacy_id, current_id);
                }
            }
        }

        aliases
    }

    fn compact_sparse_ability_entry(entry: &Value) -> Value {
        let mut compact = serde_json::Map::new();

        for key in [
            "pseudocode",
            "signature",
            "signature_hash",
            "signature_source",
            "round_trip_matches",
            "source_words",
            "trigger_id",
            "trigger",
            "frame_count",
            "opcode_sequence",
            "opcode_names",
            "rust_opcode_sequence",
            "is_once_per_turn",
            "requires_selection",
            "choice_flags",
            "choice_count",
        ] {
            if let Some(value) = entry.get(key) {
                compact.insert(key.to_string(), value.clone());
            }
        }

        if let Some(cards) = entry.get("cards").and_then(|v| v.as_array()) {
            compact.insert(
                "cards".to_string(),
                Value::Array(
                    cards
                        .iter()
                        .filter_map(|card| {
                            card.as_str()
                                .map(|card_no| Value::String(card_no.to_string()))
                        })
                        .collect(),
                ),
            );
        }

        if let Some(frames) = entry.get("frames").and_then(|v| v.as_array()) {
            compact.insert(
                "frames".to_string(),
                Value::Array(frames.iter().map(Self::compact_sparse_frame).collect()),
            );
        }

        Value::Object(compact)
    }

    fn synthesize_sparse_ability_entry(
        card_no: &str,
        ability_index: usize,
        ability: &Ability,
    ) -> Value {
        let mut compact = serde_json::Map::new();
        compact.insert("trigger".to_string(), Value::from(ability.trigger as i64));
        compact.insert(
            "trigger_id".to_string(),
            Value::from(ability.trigger as i64),
        );
        compact.insert(
            "pseudocode".to_string(),
            Value::from(if ability.pseudocode.is_empty() {
                ability.raw_text.clone()
            } else {
                ability.pseudocode.clone()
            }),
        );
        compact.insert(
            "card_refs".to_string(),
            Value::Array(vec![serde_json::json!({
                "card_no": card_no,
                "ability_index": ability_index,
            })]),
        );

        let frame_program_value = if let Some(program) = ability.frame_program.as_ref() {
            serde_json::to_value(program).unwrap_or_else(|_| Value::Object(serde_json::Map::new()))
        } else {
            Value::Object(serde_json::Map::new())
        };
        compact.insert("frame_program".to_string(), frame_program_value.clone());

        let source_words = ability.words();
        compact.insert(
            "source_words".to_string(),
            Value::Array(source_words.iter().copied().map(Value::from).collect()),
        );
        compact.insert(
            "frames".to_string(),
            frame_program_value
                .get("frames")
                .cloned()
                .unwrap_or(Value::Array(vec![])),
        );

        Value::Object(compact)
    }

    fn compact_sparse_frame(frame: &Value) -> Value {
        let mut compact = serde_json::Map::new();

        if let Some(value) = frame.get("op") {
            compact.insert("op".to_string(), value.clone());
        }

        for key in [
            "kind",
            "opcode_id",
            "opcode",
            "rust_opcode",
            "value",
            "filter",
            "slot",
            "is_negated",
            "params",
            "attr",
            "source_words",
        ] {
            if let Some(value) = frame.get(key) {
                compact.insert(key.to_string(), value.clone());
            }
        }

        if !compact.contains_key("opcode") {
            if let Some(value) = compact.get("op").cloned() {
                compact.insert("opcode".to_string(), value);
            }
        }

        Value::Object(compact)
    }

    fn attach_sparse_ability_index(
        card_no: &str,
        abilities: &mut [Ability],
        index: &HashMap<String, Value>,
    ) -> serde_json::Result<()> {
        for (ability_index, ability) in abilities.iter_mut().enumerate() {
            let key = format!("{}#{}", card_no, ability_index);
            let entry = index.get(&key).cloned().unwrap_or_else(|| {
                Self::synthesize_sparse_ability_entry(card_no, ability_index, ability)
            });
            if ability
                .frame_program
                .as_ref()
                .map(|program| program.frames.is_empty())
                .unwrap_or(true)
            {
                let program = Self::sparse_entry_to_frame_program(&entry);
                // FIX: If sparse entry produces empty frames, synthesize from ability data
                if program.frames.is_empty() {
                    // Try to create frames from ability effects
                    let mut synthesized_frames = Vec::new();
                    for effect in &ability.effects {
                        synthesized_frames.push(AbilityFrame::from_effect(effect));
                    }
                    // Add RETURN frame at the end
                    synthesized_frames.push(AbilityFrame::Return);
                    
                    if synthesized_frames.len() > 1 {
                        // We have real frames from effects
                        ability.frame_program = Some(FrameProgram {
                            frames: synthesized_frames,
                            raw_program: Some(entry.clone()),
                        });
                    } else {
                        // Last resort: create minimal RETURN frame for abilities without effects
                        ability.frame_program = Some(FrameProgram {
                            frames: vec![AbilityFrame::Return],
                            raw_program: Some(entry.clone()),
                        });
                    }
                } else {
                    ability.frame_program = Some(program);
                }
            }
            if let Some(choose_count) = ability
                .effects
                .iter()
                .find(|effect| {
                    effect.runtime_opcode == O_LOOK_AND_CHOOSE
                        || effect.effect_type == EffectType::LookAndChoose
                })
                .and_then(|effect| effect.params.get("choose_count"))
                .and_then(Self::parse_u8_value)
            {
                if let Some(program) = ability.frame_program.as_mut() {
                    if let Some(AbilityFrame::LookAndChoose { choose_count: frame_choose_count, .. }) = program
                        .frames
                        .iter_mut()
                        .find(|frame| frame.opcode() == O_LOOK_AND_CHOOSE)
                    {
                        if *frame_choose_count == 0 {
                            *frame_choose_count = choose_count as i32;
                        }
                    }
                }
            }
            // Only sync frame_program data to effects if effects are not already populated
            // (i.e., from the new semantic compiler output)
            if ability.effects.is_empty() {
                if let Some(program) = ability.frame_program.as_ref() {
                    let mut meaningful_frames = program
                        .frames
                        .iter()
                        .filter(|frame| frame.opcode() != O_RETURN);
                    for effect in ability.effects.iter_mut() {
                        let Some(frame) = meaningful_frames.next() else {
                            break;
                        };
                        let components = frame.components();
                        let needs_params = effect.params.is_null()
                            || effect
                                .params
                                .as_object()
                                .map(|params| !params.contains_key("choices"))
                                .unwrap_or(true);
                        if needs_params {
                            if let Some(params) = components.params {
                                effect.params = params.clone();
                            }
                        }
                        if effect.runtime_opcode == 0 {
                            effect.runtime_opcode = components.raw_opcode;
                        }
                        if effect.runtime_value == 0 {
                            effect.runtime_value = components.value;
                        }
                        if effect.runtime_attr == 0 {
                            effect.runtime_attr = components.raw_attr;
                        }
                        if effect.runtime_slot == 0 {
                            effect.runtime_slot = components.raw_slot;
                        }
                    }
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

    pub fn sparse_entry_to_frame_program(entry: &Value) -> FrameProgram {
        let mut program_frames = Vec::new();
        if let Some(frames) = entry.get("frames").and_then(|v| v.as_array()) {
            for frame in frames {
                program_frames.push(Self::parse_semantic_frame(frame));
            }
        }
        FrameProgram {
            frames: program_frames,
            raw_program: Some(entry.clone()),
        }
    }

    fn parse_semantic_frame(frame: &Value) -> AbilityFrame {
        AbilityFrame::from_json_value(frame)
    }

    fn parse_u8_value(value: &Value) -> Option<u8> {
        value
            .as_u64()
            .or_else(|| value.as_str().and_then(|s| s.parse::<u64>().ok()))
            .map(|v| v as u8)
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
            if Self::has_opcode_static_fast(ab, O_ADD_BLADES as i32)
                || Self::has_opcode_static_fast(ab, O_SET_BLADES as i32)
                || Self::has_opcode_static_fast(ab, O_BUFF_POWER as i32)
                || Self::has_opcode_static_fast(ab, O_TRANSFORM_BLADES as i32)
            {
                mask |= EFFECT_MASK_BLADE;
            }
            if Self::has_opcode_static_fast(ab, O_ADD_HEARTS as i32)
                || Self::has_opcode_static_fast(ab, O_SET_HEARTS as i32)
                || Self::has_opcode_static_fast(ab, O_TRANSFORM_HEART as i32)
            {
                mask |= EFFECT_MASK_HEART;
            }
            if Self::has_opcode_static_fast(ab, O_REDUCE_COST as i32)
                || Self::has_opcode_static_fast(ab, O_INCREASE_COST as i32)
                || Self::has_opcode_static_fast(ab, O_CALC_SUM_COST as i32)
            {
                mask |= EFFECT_MASK_COST;
            }
            if Self::has_opcode_static_fast(ab, O_REDUCE_HEART_REQ as i32)
                || Self::has_opcode_static_fast(ab, O_SET_HEART_COST as i32)
                || Self::has_opcode_static_fast(ab, O_INCREASE_HEART_COST as i32)
                || Self::has_opcode_static_fast(ab, O_REDUCE_LIVE_SET_LIMIT as i32)
            {
                mask |= EFFECT_MASK_REQ;
            }
            if Self::has_opcode_static_fast(ab, O_GRANT_ABILITY as i32) {
                mask |= EFFECT_MASK_GRANT;
            }
            if Self::has_opcode_static_fast(ab, O_META_RULE as i32)
                || Self::has_opcode_static_fast(ab, O_RESTRICTION as i32)
                || Self::has_opcode_static_fast(ab, O_PREVENT_PLAY_TO_SLOT as i32)
                || Self::has_opcode_static_fast(ab, O_PREVENT_SET_TO_SUCCESS_PILE as i32)
                || Self::has_opcode_static_fast(ab, O_PREVENT_ACTIVATE as i32)
                || Self::has_opcode_static_fast(ab, O_PREVENT_BATON_TOUCH as i32)
            {
                mask |= EFFECT_MASK_RULE;
            }
            if Self::has_opcode_static_fast(ab, O_BOOST_SCORE as i32)
                || Self::has_opcode_static_fast(ab, O_SET_SCORE as i32)
                || Self::has_opcode_static_fast(ab, O_REDUCE_SCORE as i32)
                || Self::has_opcode_static_fast(ab, O_MODIFY_SCORE_RULE as i32)
            {
                mask |= EFFECT_MASK_SCORE;
            }
            if Self::has_opcode_static_fast(ab, O_DRAW as i32)
                || Self::has_opcode_static_fast(ab, O_LOOK_DECK as i32)
                || Self::has_opcode_static_fast(ab, O_SEARCH_DECK as i32)
                || Self::has_opcode_static_fast(ab, O_LOOK_AND_CHOOSE as i32)
                || Self::has_opcode_static_fast(ab, O_ADD_TO_HAND as i32)
                || Self::has_opcode_static_fast(ab, O_DRAW_UNTIL as i32)
                || Self::has_opcode_static_fast(ab, O_REVEAL_UNTIL as i32)
            {
                mask |= EFFECT_MASK_DRAW;
            }
        }
        mask
    }

    /// Get all member card IDs
    pub fn all_member_ids(&self) -> Vec<i32> {
        self.members.keys().copied().collect()
    }

    /// Get all live card IDs  
    pub fn all_live_ids(&self) -> Vec<i32> {
        self.lives.keys().copied().collect()
    }

    /// Get all energy card IDs
    pub fn all_energy_ids(&self) -> Vec<i32> {
        self.energy_db.keys().copied().collect()
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
            legacy_id_aliases: HashMap::new(),
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

            // Primary path: derive from frame_program if available
            if let Some(frame_program) = ab.frame_program.as_ref() {
                for frame in &frame_program.frames {
                    let op = frame.opcode();

                    match op {
                        O_RETURN | O_LOOK_AND_CHOOSE => ability_flags_for_ab |= FLAG_DRAW as u64,
                        O_SEARCH_DECK => ability_flags_for_ab |= FLAG_SEARCH as u64,
                        O_RECOVER_LIVE | O_RECOVER_MEMBER => {
                            ability_flags_for_ab |= FLAG_RECOVER as u64
                        }
                        O_ADD_BLADES | O_ADD_HEARTS => ability_flags_for_ab |= FLAG_BUFF as u64,
                        O_MOVE_MEMBER | O_SWAP_CARDS => ability_flags_for_ab |= FLAG_MOVE as u64,
                        O_TAP_OPPONENT | O_TAP_MEMBER => ability_flags_for_ab |= FLAG_TAP as u64,
                        O_ENERGY_CHARGE => ability_flags_for_ab |= FLAG_CHARGE as u64,
                        O_ACTIVATE_MEMBER | O_SET_TAPPED => {
                            ability_flags_for_ab |= FLAG_TEMPO as u64
                        }
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
                                let v = frame.value();
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
                                        .and_then(Self::parse_u8_value)
                                        .unwrap_or(0);
                                    ab.choice_count = if effect_pick > 0 { effect_pick } else { 1 };
                                }
                            }
                        }
                        O_RECOVER_MEMBER
                        | O_RECOVER_LIVE
                        | O_MOVE_TO_DISCARD
                        | O_SELECT_MEMBER
                        | O_SELECT_LIVE
                        | O_SELECT_PLAYER
                        | O_SELECT_CARDS
                        | O_PLAY_MEMBER_FROM_HAND
                        | O_PLAY_MEMBER_FROM_DISCARD
                        | O_PLAY_LIVE_FROM_DISCARD
                        | O_MOVE_MEMBER
                        | O_SWAP_CARDS
                        | O_TAP_MEMBER
                        | O_TAP_OPPONENT
                        | O_SET_TAPPED
                        | O_ACTIVATE_MEMBER => {
                            ab.requires_selection = true;
                            if ab.choice_count == 0 {
                                let v = frame.value();
                                if v > 0 {
                                    ab.choice_count = v as u8;
                                }
                            }
                        }
                        O_SELECT_MODE => {
                            ab.choice_flags |= CHOICE_FLAG_MODE;
                            if ab.choice_count == 0 {
                                ab.choice_count = frame.value() as u8;
                            }
                        }
                        O_COLOR_SELECT => {
                            ab.choice_flags |= CHOICE_FLAG_COLOR;
                            if ab.choice_count == 0 {
                                ab.choice_count = frame
                                    .components()
                                    .params
                                    .and_then(|value| value.as_object())
                                    .and_then(|params| {
                                        params.get("choices").or_else(|| params.get("CHOICES"))
                                    })
                                    .and_then(|value| value.as_array())
                                    .map(|choices| choices.len() as u8)
                                    .unwrap_or(6);
                            }
                        }
                        O_ORDER_DECK => {
                            ab.choice_flags |= CHOICE_FLAG_ORDER;
                            if ab.choice_count == 0 {
                                ab.choice_count = 1;
                            }
                        }
                        _ => {}
                    }

                    ab.opcodes_mask |= 1u128 << (op as u32 % 128);
                    ability_opcodes_mask |= ab.opcodes_mask;
                    trigger_mask |= 1u32 << (ab.trigger as u32 % 32);

                    if op == O_BATON_TOUCH_MOD && frame.value() >= 2 {
                        has_multi_baton = true;
                    }

                    if [
                        O_ADD_BLADES,
                        O_ADD_HEARTS,
                        O_BUFF_POWER,
                        O_REDUCE_COST,
                        O_INCREASE_COST,
                        O_SET_HEART_COST,
                    ]
                    .contains(&op)
                    {
                        let val = frame.value();
                        let attr = frame.attr();
                        let slot = frame.slot();
                        ab.preparsed_modifiers.push(PreparsedModifier {
                            op,
                            val,
                            attr,
                            slot,
                        });
                    }

                    if !flagged_ops.contains(&op) {
                        unflagged_logic_present = true;
                    }
                }
            }

            // Frame program fallback for conditions (if effects/conditions not populated)
            let semantic_program = ab.frame_program.as_ref().cloned();
            if let Some(frame_program) = semantic_program.as_ref() {
                if ab.conditions.is_empty() {
                    ab.conditions = Self::derive_conditions_from_frame_program(frame_program);
                }
                // Handle special case for NotHasExcessHeart condition
                if ab
                    .raw_text
                    .contains("相手が余剰のハートを持たず")
                    || ab
                        .raw_text
                        .contains("opponent succeeded a Live without excess Hearts this turn")
                {
                    if !ab
                        .conditions
                        .iter()
                        .any(|cond| cond.condition_type == ConditionType::NotHasExcessHeart)
                    {
                        ab.conditions.push(Condition {
                            condition_type: ConditionType::NotHasExcessHeart,
                            value: 0,
                            attr: TARGET_PLAYER_OPPONENT as u64,
                            target_slot: 0,
                            is_negated: false,
                            params: serde_json::Value::Null,
                        });
                    }
                }
            }

            if ab.choice_count > 0 {
                if let Some(frame_program) = ab.frame_program.as_mut() {
                    for frame in &mut frame_program.frames {
                        if let AbilityFrame::LookAndChoose { choose_count, .. } = frame {
                            if *choose_count == 0 {
                                *choose_count = ab.choice_count as i32;
                            }
                        }
                    }
                }
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
        if (f & FLAG_DRAW as u64) != 0 {
            score += 5.0;
        }
        if (f & FLAG_SEARCH as u64) != 0 {
            score += 5.0;
        }
        if (f & FLAG_RECOVER as u64) != 0 {
            score += 0.5;
        }
        if (f & FLAG_BUFF as u64) != 0 {
            score += 0.4;
        }
        if (f & FLAG_CHARGE as u64) != 0 {
            score += 1.2;
        }
        if (f & FLAG_TEMPO as u64) != 0 {
            score += 0.3;
        }
        if (f & FLAG_REDUCE as u64) != 0 {
            score += 0.6;
        }
        if (f & FLAG_BOOST as u64) != 0 {
            score += 0.6;
        }
        if (f & FLAG_TRANSFORM as u64) != 0 {
            score += 0.4;
        }
        if (f & FLAG_WIN_COND as u64) != 0 {
            score += 1.0;
        }

        if (card.synergy_flags & SYN_FLAG_GROUP) != 0 {
            score += 0.3;
        }
        if (card.synergy_flags & SYN_FLAG_CENTER) != 0 {
            score += 0.5;
        }
        if (card.cost_flags & COST_FLAG_TAP as u32) != 0 {
            score += 0.2;
        }

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
            legacy_id_aliases: HashMap::new(),
            is_vanilla: false,
            cached_vanilla: None,
        };

        if let Some(members_raw) = raw.get("member_db").and_then(|m| m.as_object()) {
            for (_, val) in members_raw {
                match serde_json::from_value::<MemberCard>(val.clone()) {
                    Ok(mut card) => {
                        Self::attach_sparse_ability_index(
                            &card.card_no,
                            &mut card.abilities,
                            &db.sparse_ability_index,
                        )?;
                        Self::normalize_member_runtime_compatibility(&mut card);
                        Self::enrich_member_runtime_metadata(&mut card);

                        db.members.insert(card.card_id, card.clone());
                        db.card_no_to_id
                            .insert(Self::normalize_card_no(&card.card_no), card.card_id);

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
                        eprintln!(
                            "[DB] ERROR: Failed to parse Member card {}: {}",
                            val["card_no"], e
                        );
                        // Skip this card and continue parsing others
                        continue;
                    }
                }
            }
        }

        if let Some(lives_raw) = raw.get("live_db").and_then(|l| l.as_object()) {
            for (_, val) in lives_raw {
                match serde_json::from_value::<LiveCard>(val.clone()) {
                    Ok(mut card) => {
                        Self::attach_sparse_ability_index(
                            &card.card_no,
                            &mut card.abilities,
                            &db.sparse_ability_index,
                        )?;
                        Self::normalize_live_runtime_compatibility(&mut card);
                        Self::enrich_live_runtime_metadata(&mut card);

                        db.lives.insert(card.card_id, card.clone());
                        db.card_no_to_id
                            .insert(Self::normalize_card_no(&card.card_no), card.card_id);

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

        db.inject_missing_ability_conditions();

        db.legacy_id_aliases = Self::load_legacy_id_aliases(&db.card_no_to_id);

        let legacy_aliases: Vec<(i32, i32)> = db
            .legacy_id_aliases
            .iter()
            .map(|(&legacy_id, &current_id)| (legacy_id, current_id))
            .collect();

        for (legacy_id, current_id) in legacy_aliases {
            if !db.members.contains_key(&legacy_id) {
                if let Some(card) = db.members.get(&current_id).cloned() {
                    db.members.insert(legacy_id, card);
                }
            }
            if !db.lives.contains_key(&legacy_id) {
                if let Some(card) = db.lives.get(&current_id).cloned() {
                    db.lives.insert(legacy_id, card);
                }
            }
        }

        db.cached_vanilla = Some(db.is_vanilla || db.detect_abilityless());

        Ok(db)
    }

    // Fast Lookups
    pub fn get_member(&self, id: i32) -> Option<&MemberCard> {
        let resolved_id = self.legacy_id_aliases.get(&id).copied().unwrap_or(id);

        // Fast path: Try vector (O(1)) and confirm exact ID match
        let logic_id = Self::to_logic_id(resolved_id);
        if logic_id < self.members_vec.len() {
            if let Some(m) = &self.members_vec[logic_id] {
                if m.card_id == resolved_id || m.card_id == id {
                    return Some(m);
                }
            }
        }

        // Slow path: Try HashMap
        if let Some(m) = self.members.get(&resolved_id) {
            return Some(m);
        }
        if let Some(m) = self.members.get(&id) {
            return Some(m);
        }
        None
    }

    pub fn get_live(&self, id: i32) -> Option<&LiveCard> {
        let resolved_id = self.legacy_id_aliases.get(&id).copied().unwrap_or(id);

        // Fast path: Try vector (O(1)) and confirm exact ID match
        let logic_id = Self::to_logic_id(resolved_id);
        if logic_id < self.lives_vec.len() {
            if let Some(l) = &self.lives_vec[logic_id] {
                if l.card_id == resolved_id || l.card_id == id {
                    return Some(l);
                }
            }
        }

        // Slow path: Try HashMap
        if let Some(l) = self.lives.get(&resolved_id) {
            return Some(l);
        }
        if let Some(l) = self.lives.get(&id) {
            return Some(l);
        }
        None
    }

    pub fn id_by_no(&self, card_no: &str) -> Option<i32> {
        let normalized = Self::normalize_card_no(card_no);
        self.card_no_to_id.get(&normalized).copied()
    }

    fn inject_missing_ability_conditions(&mut self) {
        let tiny_stars_id = self
            .id_by_no("PL!SP-bp1-024-L")
            .or_else(|| {
                self.lives
                    .values()
                    .find(|live| live.name == "Tiny Stars")
                    .map(|live| live.card_id)
            });
        let strawberry_trapper_id = self
            .id_by_no("PL!S-pb1-021-L")
            .or_else(|| {
                self.lives
                    .values()
                    .find(|live| live.name == "Strawberry Trapper")
                    .map(|live| live.card_id)
            });
        let kanon_id = self.id_by_no("PL!SP-PR-003-PR");
        let keke_id = self.id_by_no("PL!SP-PR-004-PR");

        if let (Some(live_id), Some(kanon_id), Some(keke_id)) =
            (tiny_stars_id, kanon_id, keke_id)
        {
            if let Some(live) = self.lives.get_mut(&live_id) {
                for ab in &mut live.abilities {
                    if ab.trigger != TriggerType::OnLiveSuccess {
                        continue;
                    }
                    ab.conditions.clear();
                    ab.conditions.push(Condition {
                        condition_type: ConditionType::HasMember,
                        value: kanon_id,
                        attr: TARGET_PLAYER_SELF as u64,
                        target_slot: 0,
                        is_negated: false,
                        params: serde_json::Value::Null,
                    });
                    ab.conditions.push(Condition {
                        condition_type: ConditionType::HasMember,
                        value: keke_id,
                        attr: TARGET_PLAYER_SELF as u64,
                        target_slot: 0,
                        is_negated: false,
                        params: serde_json::Value::Null,
                    });
                }
                let logic_id = Self::to_logic_id(live.card_id);
                if logic_id < self.lives_vec.len() {
                    self.lives_vec[logic_id] = Some(live.clone());
                }
            }
        }

        if let Some(live_id) = self.id_by_no("PL!N-bp1-006-P") {
            if let Some(live) = self.lives.get_mut(&live_id) {
                for ab in &mut live.abilities {
                    if ab.trigger != TriggerType::OnLiveStart {
                        continue;
                    }
                    ab.conditions.clear();
                    ab.conditions.push(Condition {
                        condition_type: ConditionType::CostCompare,
                        value: 0,
                        attr: 0,
                        target_slot: 1,
                        is_negated: false,
                        params: serde_json::Value::Null,
                    });
                }
                let logic_id = Self::to_logic_id(live.card_id);
                if logic_id < self.lives_vec.len() {
                    self.lives_vec[logic_id] = Some(live.clone());
                }
            }
        }

        if let Some(live_id) = strawberry_trapper_id {
            if let Some(live) = self.lives.get_mut(&live_id) {
                for ab in &mut live.abilities {
                    if ab.trigger != TriggerType::OnLiveSuccess {
                        continue;
                    }
                    if !ab
                        .conditions
                        .iter()
                        .any(|cond| cond.condition_type == ConditionType::NotHasExcessHeart)
                    {
                        ab.conditions.push(Condition {
                            condition_type: ConditionType::NotHasExcessHeart,
                            value: 0,
                            attr: TARGET_PLAYER_OPPONENT as u64,
                            target_slot: 0,
                            is_negated: false,
                            params: serde_json::Value::Null,
                        });
                    }
                }
                let logic_id = Self::to_logic_id(live.card_id);
                if logic_id < self.lives_vec.len() {
                    self.lives_vec[logic_id] = Some(live.clone());
                }
            }
        }

        if let Some(member_id) = self.id_by_no("PL!-bp5-003-P") {
            if let Some(member) = self.members.get_mut(&member_id) {
                for ab in &mut member.abilities {
                    if ab.trigger != TriggerType::Constant {
                        continue;
                    }
                    let has_unique_names_gate = ab.conditions.iter().any(|cond| {
                        cond.params
                            .as_object()
                            .and_then(|params| params.get("raw_cond"))
                            .and_then(|value| value.as_str())
                            == Some("UNIQUE_NAMES_COUNT")
                    });
                    if !has_unique_names_gate {
                        ab.conditions.push(Condition {
                            condition_type: ConditionType::None,
                            value: 0,
                            attr: 0,
                            target_slot: 0,
                            is_negated: false,
                            params: serde_json::json!({
                                "raw_cond": "UNIQUE_NAMES_COUNT",
                                "MIN": 3
                            }),
                        });
                    }
                }
                let logic_id = Self::to_logic_id(member.card_id);
                if logic_id < self.members_vec.len() {
                    self.members_vec[logic_id] = Some(member.clone());
                }
            }
        }
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

    /// Get a card by ID (returns either MemberCard or LiveCard)
    pub fn get_card(&self, id: i32) -> Option<CardRef> {
        if let Some(member) = self.members.get(&id) {
            return Some(CardRef::Member(member.clone()));
        }
        if let Some(live) = self.lives.get(&id) {
            return Some(CardRef::Live(live.clone()));
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
    pub fn has_opcode_static_fast(ab: &Ability, target_op: i32) -> bool {
        if let Some(program) = ab.frame_program.as_ref() {
            for frame in &program.frames {
                if frame.opcode() == target_op {
                    return true;
                }
            }
        }
        false
    }

    pub fn to_binary(&self) -> bincode::Result<Vec<u8>> {
        bincode::serialize(self)
    }

    pub fn from_binary(data: &[u8]) -> bincode::Result<Self> {
        bincode::deserialize(data)
    }
}

pub fn program_has_choice(program: &FrameProgram) -> bool {
    for frame in &program.frames {
        let op = frame.opcode();
        if op == O_SELECT_MODE
            || op == O_LOOK_AND_CHOOSE
            || op == O_COLOR_SELECT
            || op == O_TAP_OPPONENT
            || op == O_ORDER_DECK
            || op == O_PLAY_MEMBER_FROM_HAND
            || op == O_PLAY_MEMBER_FROM_DISCARD
            || op == O_OPPONENT_CHOOSE
            || op == O_RECOVER_LIVE
            || op == O_RECOVER_MEMBER
            || op == O_MOVE_MEMBER
            || op == O_SELECT_MEMBER
            || op == O_SELECT_LIVE
            || op == O_SELECT_PLAYER
            || op == O_SELECT_CARDS
            || op == O_MOVE_TO_DISCARD
            || op == O_TAP_MEMBER
            || op == O_ACTIVATE_MEMBER
            || op == O_SET_TAPPED
            || op == O_PAY_ENERGY
            || op == O_MOVE_TO_DECK
        {
            return true;
        }
    }
    false
}

pub fn program_needs_early_pause(program: &FrameProgram) -> bool {
    for frame in &program.frames {
        let op = frame.opcode();
        if op == O_SELECT_MODE
            || op == O_COLOR_SELECT
            || op == O_LOOK_AND_CHOOSE
            || op == O_SELECT_CARDS
            || op == O_SELECT_MEMBER
            || op == O_SELECT_LIVE
            || op == O_SELECT_PLAYER
            || op == O_RECOVER_LIVE
            || op == O_RECOVER_MEMBER
            || op == O_MOVE_MEMBER
            || op == O_MOVE_TO_DISCARD
            || op == O_MOVE_TO_DECK
        {
            return true;
        }
    }
    false
}

pub fn program_needs_early_pause_opcode(program: &FrameProgram) -> i32 {
    for frame in &program.frames {
        let op = frame.opcode();
        if op == O_SELECT_MODE
            || op == O_COLOR_SELECT
            || op == O_LOOK_AND_CHOOSE
            || op == O_SELECT_CARDS
            || op == O_SELECT_MEMBER
            || op == O_SELECT_LIVE
            || op == O_SELECT_PLAYER
            || op == O_RECOVER_LIVE
            || op == O_RECOVER_MEMBER
            || op == O_MOVE_MEMBER
            || op == O_MOVE_TO_DISCARD
            || op == O_MOVE_TO_DECK
        {
            return op;
        }
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
    "",           // 70
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
