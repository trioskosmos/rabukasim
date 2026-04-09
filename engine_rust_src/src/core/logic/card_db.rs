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
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use super::models::*;
use super::rules::ability_has_hand_only_self_cost_modifier;

fn parse_u8_value(value: &serde_json::Value) -> Option<u8> {
    value
        .as_u64()
        .or_else(|| value.as_str().and_then(|s| s.parse::<u64>().ok()))
        .map(|v| v as u8)
}

// Custom deserializers to handle the compiled metadata shape.
//
// The compiler currently emits group/unit metadata as strings (often
// newline-separated for multi-name cards) rather than numeric arrays, so the
// runtime needs to map the authored names back to stable numeric ids.
fn deserialize_group_ids<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    deserialize_named_id_list(deserializer, group_id_from_text)
}

fn deserialize_unit_ids<'de, D>(deserializer: D) -> Result<Vec<u8>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    deserialize_named_id_list(deserializer, unit_id_from_text)
}

fn deserialize_named_id_list<'de, D, F>(deserializer: D, lookup: F) -> Result<Vec<u8>, D::Error>
where
    D: serde::Deserializer<'de>,
    F: Fn(&str) -> Option<u8>,
{
    let value = Value::deserialize(deserializer)?;
    Ok(extract_named_ids(&value, &lookup))
}

fn extract_named_ids<F>(value: &Value, lookup: &F) -> Vec<u8>
where
    F: Fn(&str) -> Option<u8>,
{
    match value {
        Value::Array(arr) => arr
            .iter()
            .flat_map(|item| extract_named_ids(item, lookup))
            .collect(),
        Value::String(text) => text
            .split(['\n', '\r', ',', '/', ';'])
            .map(str::trim)
            .filter(|token| !token.is_empty())
            .filter_map(|token| lookup(token))
            .collect(),
        Value::Number(num) => num.as_u64().map(|num| vec![num as u8]).unwrap_or_default(),
        Value::Object(object) => object
            .values()
            .flat_map(|item| extract_named_ids(item, lookup))
            .collect(),
        _ => Vec::new(),
    }
}

fn normalize_name_token(name: &str) -> String {
    name.trim()
        .replace('　', " ")
        .replace('！', "!")
        .replace('・', "・")
        .replace('　', "")
}

fn group_id_from_text(name: &str) -> Option<u8> {
    match normalize_name_token(name).as_str() {
        "ラブライブ!" => Some(0),
        "ラブライブ!サンシャイン!!" => Some(1),
        "ラブライブ!虹ヶ咲学園スクールアイドル同好会" => Some(2),
        "ラブライブ!スーパースター!!" => Some(3),
        "蓮ノ空女学院スクールアイドルクラブ" => Some(4),
        "ラブライブ!蓮ノ空女学院スクールアイドルクラブ" => Some(4),
        "Aqours" | "AQOURS" => Some(1),
        "Nijigasaki" | "NIJIGASAKI" | "Nijigaku" | "NIJIGAKU" => Some(2),
        "Liella!" | "LIELLA" => Some(3),
        "Hasunosora" | "HASUNOSORA" | "HASU" => Some(4),
        _ => None,
    }
}

fn unit_id_from_text(name: &str) -> Option<u8> {
    match normalize_name_token(name).as_str() {
        "" => None,
        "Printemps" | "PRINTEMPS" => Some(0),
        "lilywhite" | "LILYWHITE" | "LILY_WHITE" => Some(1),
        "BiBi" | "BIBI" => Some(2),
        "CYaRon!" | "CYARON" => Some(3),
        "AZALEA" => Some(4),
        "GuiltyKiss" | "GUILTYKISS" | "GUILTY_KISS" => Some(5),
        "DiverDiva" | "DIVERDIVA" | "DIVER_DIVA" => Some(6),
        "A・ZU・NA" | "AZUNA" | "A_ZU_NA" => Some(7),
        "QU4RTZ" => Some(8),
        "R3BIRTH" => Some(9),
        "CatChu!" | "CATCHU" => Some(10),
        "KALEIDOSCORE" => Some(11),
        "5yncri5e!" | "5YNCRI5E" | "SYNCRISE" => Some(12),
        "スリーズブーケ" | "CERISE_BOUQUET" | "CERISE" => Some(13),
        "DOLLCHESTRA" | "DOLL" => Some(14),
        "みらくらぱーく！" | "みらくらぱーく!" | "MIRA_CRA_PARK" | "MIRAKURA" | "MIRA-CRA" => {
            Some(15)
        }
        "EdelNote" | "EDELNOTE" => Some(16),
        "AiScReam" | "AISCREAM" => Some(17),
        _ => None,
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
    #[serde(default, deserialize_with = "deserialize_group_ids")]
    pub groups: Vec<u8>,
    #[serde(default, deserialize_with = "deserialize_unit_ids")]
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
    pub has_hand_self_cost_modifiers: bool,
    #[serde(default)]
    pub has_monitor_conditions: bool,
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
    #[serde(default, deserialize_with = "deserialize_group_ids")]
    pub groups: Vec<u8>,
    #[serde(default, deserialize_with = "deserialize_unit_ids")]
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
    pub trigger_mask: u32,
    #[serde(default)]
    pub char_mask: u128,
    #[serde(default)]
    pub normalized_name: String,
    #[serde(default)]
    pub has_monitor_conditions: bool,
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
        let mut has_hand_self_cost_modifiers = false;
        let mut has_monitor_conditions = false;

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
            let mut runtime_has_deck_top_window = false;
            let mut runtime_has_frame_cost_checks = false;
            let mut runtime_has_optional_frame = false;
            let mut runtime_has_look_choose_checks = false;
            let mut runtime_has_interactive_prompt = false;
            let mut runtime_prompt_before_count_blades = false;
            let mut runtime_prompt_before_count_hearts = false;

            if ab.trigger == TriggerType::OnPlay {
                s_flags |= 0x01;
            }
            if ab.trigger == TriggerType::Activated {
                s_flags |= 0x02;
            }
            if ab.trigger == TriggerType::TurnStart || ab.trigger == TriggerType::TurnEnd {
                s_flags |= 0x04;
            }
            if ab.per_turn_limit() > 0 {
                s_flags |= 0x08;
            }

            ab.preparsed_modifiers.clear();
            ab.opcodes_mask = 0;

            let mut ability_flags_for_ab = 0u64;
            let mut unflagged_logic_present = false;
            let resolved_frames = ab.resolved_frames().into_owned();
            let mut saw_interactive_prompt = false;

            if !resolved_frames.is_empty() {
                for frame in &resolved_frames {
                    let op = frame.opcode();

                    if frame.components().filter.is_optional {
                        runtime_has_optional_frame = true;
                    }
                    if frame.dslot().source_zone == Zone::DeckTop {
                        runtime_has_deck_top_window = true;
                    }
                    if frame.is_cost()
                        || matches!(
                            op,
                            O_MOVE_MEMBER | O_MOVE_TO_DISCARD | O_MOVE_TO_DECK
                        ) && matches!(
                            frame.dslot().source_zone,
                            Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
                        )
                    {
                        runtime_has_frame_cost_checks = true;
                    }
                    if op == O_LOOK_AND_CHOOSE && !frame.is_cost() {
                        runtime_has_look_choose_checks = true;
                    }
                    if matches!(
                        op,
                        O_SELECT_MEMBER
                            | O_SELECT_LIVE
                            | O_SELECT_PLAYER
                            | O_SELECT_MODE
                            | O_SELECT_CARDS
                            | O_LOOK_AND_CHOOSE
                            | O_COLOR_SELECT
                            | O_TAP_MEMBER
                            | O_TAP_OPPONENT
                            | O_TRIGGER_REMOTE
                    ) {
                        runtime_has_interactive_prompt = true;
                        saw_interactive_prompt = true;
                    }
                    if op == crate::core::generated_constants::C_COUNT_BLADES
                        && saw_interactive_prompt
                    {
                        runtime_prompt_before_count_blades = true;
                    }
                    if op == crate::core::generated_constants::C_COUNT_HEARTS
                        && saw_interactive_prompt
                    {
                        runtime_prompt_before_count_hearts = true;
                    }

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
                            let v = frame.value();
                            let pick = (v >> 8) & 0xFF;
                            let inferred_choice_count = if pick > 0 {
                                pick as u8
                            } else {
                                let effect_pick = ab
                                    .effects
                                    .iter()
                                    .find(|effect| {
                                        effect.runtime_opcode == O_LOOK_AND_CHOOSE
                                            || effect.effect_type == EffectType::LookAndChoose
                                            || effect.params.get("choose_count").is_some()
                                            || effect.params.get("CHOOSE_COUNT").is_some()
                                    })
                                    .and_then(|effect| effect.params.get("choose_count"))
                                    .or_else(|| {
                                        ab.effects.iter().find_map(|effect| {
                                            effect.params.get("CHOOSE_COUNT")
                                        })
                                    })
                                    .and_then(parse_u8_value)
                                    .unwrap_or(1);
                                effect_pick.max(1)
                            };
                            ab.choice_count = ab.choice_count.max(inferred_choice_count);
                            if ab.choice_count == 0 {
                                ab.choice_count = 1;
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

            let runtime_has_optional_cost = ab.costs.iter().any(|cost| cost.is_optional);

            if let Some(frame_program) = ab.frame_program.as_ref() {
                let derived_conditions =
                    crate::core::logic::models::derive_conditions_from_frame_program(frame_program);
                ab.conditions = derived_conditions;
            }

            let runtime_has_activation_conditions = ab.conditions.iter().any(|condition| {
                !matches!(
                    condition.condition_type,
                    ConditionType::SumValue | ConditionType::DiscardedCards
                )
            });

            if ab.choice_count > 0 {
                if let Some(frame_program) = ab.frame_program.as_mut() {
                    for frame in &mut frame_program.frames {
                        if frame.opcode == O_LOOK_AND_CHOOSE {
                            let mut lac = frame.look_choose();
                            if lac.choose_count == 0 {
                                lac.choose_count = ab.choice_count;
                                frame.value = lac.to_raw();
                                if frame.params.is_null() {
                                    frame.params = serde_json::json!({});
                                }
                                if let Some(params) = frame.params.as_object_mut() {
                                    params.insert(
                                        "choose_count".to_string(),
                                        serde_json::Value::from(ab.choice_count),
                                    );
                                    if !params.contains_key("count") {
                                        params.insert(
                                            "count".to_string(),
                                            serde_json::Value::from(lac.count),
                                        );
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if ab.trigger == TriggerType::OnPlay && ab.choice_flags != 0 {
                has_on_play_choice = true;
            }

            if matches!(ab.trigger, TriggerType::Constant | TriggerType::TurnStart)
                && ability_has_hand_only_self_cost_modifier(ab)
            {
                has_hand_self_cost_modifiers = true;
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

            ab.runtime_metadata_ready = true;
            ab.runtime_has_deck_top_window = runtime_has_deck_top_window;
            ab.runtime_has_frame_cost_checks = runtime_has_frame_cost_checks;
            ab.runtime_has_optional_frame = runtime_has_optional_frame;
            ab.runtime_has_optional_cost = runtime_has_optional_cost;
            ab.runtime_has_activation_conditions = runtime_has_activation_conditions;
            ab.runtime_has_look_choose_checks = runtime_has_look_choose_checks;
            ab.runtime_has_interactive_prompt = runtime_has_interactive_prompt;
            ab.runtime_prompt_before_count_blades = runtime_prompt_before_count_blades;
            ab.runtime_prompt_before_count_hearts = runtime_prompt_before_count_hearts;

            flags |= ability_flags_for_ab;
            if unflagged_logic_present {
                s_flags |= 0x10;
            }

            for c in &ab.conditions {
                match c.condition_type {
                    ConditionType::GroupFilter | ConditionType::ScoreTotalCheck => {
                        has_monitor_conditions = true
                    }
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
        card.has_hand_self_cost_modifiers = has_hand_self_cost_modifiers;
        card.has_monitor_conditions = has_monitor_conditions;

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
        let mut trigger_mask = 0u32;
        let mut has_monitor_conditions = false;

        for ab in &mut card.abilities {
            trigger_mask |= 1u32 << (ab.trigger as u32 % 32);

            if let Some(frame_program) = ab.frame_program.as_ref() {
                let derived_conditions =
                    crate::core::logic::models::derive_conditions_from_frame_program(frame_program);
                ab.conditions = derived_conditions;
            }

            if ab.trigger == TriggerType::OnPlay {
                s_flags |= 0x01;
            }

            for c in &ab.conditions {
                match c.condition_type {
                    ConditionType::GroupFilter | ConditionType::ScoreTotalCheck => {
                        has_monitor_conditions = true
                    }
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
        card.trigger_mask = trigger_mask;
        card.has_monitor_conditions = has_monitor_conditions;

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
            legacy_id_aliases: HashMap::new(),
            is_vanilla: false,
            cached_vanilla: None,
        };

        if let Some(members_raw) = raw.get("member_db").and_then(|m| m.as_object()) {
            for (_, val) in members_raw {
                match serde_json::from_value::<MemberCard>(val.clone()) {
                    Ok(mut card) => {
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

