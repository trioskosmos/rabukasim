use super::models::*;
use crate::core::enums::{ConditionType, EffectType, TriggerType, Zone};
use crate::core::generated_constants::*;
use crate::core::logic::interpreter::conditions::common::parse_condition_type;
use crate::core::models::interpreter::instruction::DecodedSlot;
use serde_json::Value;
use std::collections::HashMap;
use std::fmt::Write;
use std::fs;

/// Runtime hydration for authored ability frames.
///
/// This module is the boundary between the authored sparse frame index and the
/// normalized runtime `Ability` shape that the interpreter consumes. It keeps
/// card loading focused on database construction while gathering the repair and
/// attachment logic in one place.

fn sanitize_sparse_json_text(json: &str) -> String {
    let mut sanitized = String::with_capacity(json.len());
    let mut in_string = false;
    let mut escaped = false;

    for ch in json.chars() {
        if in_string {
            if escaped {
                sanitized.push(ch);
                escaped = false;
                continue;
            }

            match ch {
                '\\' => {
                    sanitized.push(ch);
                    escaped = true;
                }
                '"' => {
                    sanitized.push(ch);
                    in_string = false;
                }
                c if c.is_control() => {
                    let _ = write!(&mut sanitized, "\\u{:04x}", c as u32);
                }
                _ => sanitized.push(ch),
            }
        } else {
            match ch {
                '"' => {
                    sanitized.push(ch);
                    in_string = true;
                }
                c if c.is_control() && !matches!(c, '\n' | '\r' | '\t') => {}
                _ => sanitized.push(ch),
            }
        }
    }

    sanitized
}

fn normalize_card_no(card_no: &str) -> String {
    card_no.replace('＋', "+")
}

pub(crate) fn load_sparse_ability_index_from_json(json: &str) -> HashMap<String, Value> {
    let json = sanitize_sparse_json_text(json);
    let json = json.trim_start_matches(|c: char| c.is_whitespace() || c == '\u{feff}' || c == '\0');
    let json = if let Some(start) = json.find('{') {
        &json[start..]
    } else if let Some(start) = json.find('[') {
        &json[start..]
    } else {
        json
    };

    let parsed_root = match serde_json::from_str::<Value>(json) {
        Ok(root) => Some(root),
        Err(json_err) => match serde_yaml::from_str::<Value>(json) {
            Ok(root) => Some(root),
            Err(yaml_err) => {
                eprintln!("[SPARSE_DBG] parse_error={}", json_err);
                eprintln!("[SPARSE_DBG] yaml_parse_error={}", yaml_err);
                None
            }
        },
    };
    if let Some(root) = parsed_root {
        let mut index = HashMap::new();

        if let Some(abilities_arr) = root.get("abilities").and_then(|v| v.as_array()) {
            for ability_data in abilities_arr {
                if let Some(frames) = ability_data.get("frames").and_then(|v| v.as_array()) {
                    let mut compact_entry = serde_json::Map::new();

                    for key in [
                        "pseudocode",
                        "source_text",
                        "source_text_en",
                        "trigger",
                        "trigger_id",
                    ] {
                        if let Some(value) = ability_data.get(key) {
                            compact_entry.insert(key.to_string(), value.clone());
                        }
                    }

                    compact_entry.insert("frames".to_string(), Value::Array(frames.clone()));

                    if let Some(card_refs) = ability_data.get("card_refs").and_then(|v| v.as_array()) {
                        for card_ref in card_refs {
                            if let Some(card_obj) = card_ref.as_object() {
                                if let Some(card_no) = card_obj.get("card_no").and_then(|v| v.as_str()) {
                                    if let Some(ability_index) = card_obj.get("ability_index").and_then(|v| v.as_i64()) {
                                        let mut keyed_entry = compact_entry.clone();
                                        if let Some(trigger) = ability_data.get("trigger") {
                                            keyed_entry.insert("trigger".to_string(), trigger.clone());
                                        }
                                        if let Some(trigger_id) = ability_data.get("trigger_id") {
                                            keyed_entry.insert("trigger_id".to_string(), trigger_id.clone());
                                        }
                                        let key = format!("{}#{}", card_no, ability_index);
                                        index.insert(key, Value::Object(keyed_entry));
                                    }
                                }
                            }
                        }
                    } else if let Some(cards) = ability_data.get("cards").and_then(|v| v.as_array()) {
                        for card in cards {
                            let Some(card_entry) = card.as_str() else {
                                continue;
                            };
                            let Some(card_no) = card_entry.split(" | ").next() else {
                                continue;
                            };
                            let Some(ability_index_part) = card_entry.split("(ab#").nth(1) else {
                                continue;
                            };
                            let ability_index = ability_index_part
                                .split_whitespace()
                                .next()
                                .and_then(|value| value.trim_end_matches(')').parse::<i64>().ok());
                            let Some(ability_index) = ability_index else {
                                continue;
                            };

                            let mut keyed_entry = compact_entry.clone();
                            if let Some(trigger) = ability_data.get("trigger") {
                                keyed_entry.insert("trigger".to_string(), trigger.clone());
                            }
                            if let Some(trigger_id) = ability_data.get("trigger_id") {
                                keyed_entry.insert("trigger_id".to_string(), trigger_id.clone());
                            }
                            let key = format!("{}#{}", card_no, ability_index);
                            index.insert(key, Value::Object(keyed_entry));
                        }
                    }
                }
            }

            return index;
        }

        if let Some(abilities_obj) = root.as_object() {
            for (_ability_key, ability_data) in abilities_obj {
                if let Some(frames) = ability_data.get("frames").and_then(|v| v.as_array()) {
                    let mut compact_entry = serde_json::Map::new();

                    for key in ["pseudocode", "source_text", "source_text_en", "trigger", "trigger_id"] {
                        if let Some(value) = ability_data.get(key) {
                            compact_entry.insert(key.to_string(), value.clone());
                        }
                    }

                    compact_entry.insert("frames".to_string(), Value::Array(frames.clone()));

                    if let Some(card_refs) = ability_data.get("card_refs").and_then(|v| v.as_array()) {
                        for card_ref in card_refs {
                            if let Some(card_obj) = card_ref.as_object() {
                                if let Some(card_no) = card_obj.get("card_no").and_then(|v| v.as_str()) {
                                    if let Some(ability_index) = card_obj.get("ability_index").and_then(|v| v.as_i64()) {
                                        let mut keyed_entry = compact_entry.clone();
                                        if let Some(trigger) = card_obj.get("trigger") {
                                            keyed_entry.insert("trigger".to_string(), trigger.clone());
                                        }
                                        if let Some(trigger_id) = card_obj.get("trigger_id") {
                                            keyed_entry.insert("trigger_id".to_string(), trigger_id.clone());
                                        }
                                        let key = format!("{}#{}", card_no, ability_index);
                                        index.insert(key, Value::Object(keyed_entry));
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        return index;
    }
    HashMap::new()
}

pub(crate) fn load_sparse_text_index() -> HashMap<String, String> {
    let mut text_index = HashMap::new();

    for candidates in [
        ["data/ability_runtime_index.json", "../data/ability_runtime_index.json"],
        ["data/ability_frame_index.json", "../data/ability_frame_index.json"],
    ] {
        let mut loaded_group = false;
        for path in candidates {
            if let Ok(json) = fs::read_to_string(path) {
                if let Ok(parsed_root) = serde_json::from_str::<Value>(&json) {
                    if let Some(abilities) = parsed_root.get("abilities").and_then(|v| v.as_array()) {
                        for ability_data in abilities {
                            if let Some(source_text) = ability_data.get("source_text").and_then(|v| v.as_str()) {
                                if let Some(card_refs) = ability_data.get("card_refs").and_then(|v| v.as_array()) {
                                    for card_ref in card_refs {
                                        if let Some(card_obj) = card_ref.as_object() {
                                            if let Some(card_no) = card_obj.get("card_no").and_then(|v| v.as_str()) {
                                                if let Some(ability_index) = card_obj.get("ability_index").and_then(|v| v.as_i64()) {
                                                    let key = format!("{}#{}", card_no, ability_index);
                                                    text_index.insert(key, source_text.to_string());
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                if !text_index.is_empty() {
                    loaded_group = true;
                    break;
                }
            }
        }

        if loaded_group {
            break;
        }
    }

    text_index
}

pub(crate) fn derive_conditions_from_frame_program(program: &FrameProgram) -> Vec<Condition> {
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

pub(crate) fn attach_sparse_ability_index(
    card_no: &str,
    abilities: &mut [Ability],
    index: &HashMap<String, Value>,
    text_index: &HashMap<String, String>,
) -> serde_json::Result<()> {
    let mut lookup_keys = vec![format!("{}#", card_no)];
    let normalized_card_no = normalize_card_no(card_no);
    if normalized_card_no != card_no {
        lookup_keys.push(format!("{}#", normalized_card_no));
    }
    if card_no.contains('+') {
        lookup_keys.push(format!("{}#", card_no.replace('+', "＋")));
    }
    if card_no.contains('＋') {
        lookup_keys.push(format!("{}#", card_no.replace('＋', "+")));
    }
    if let Some(rest) = card_no.strip_prefix("PL!-") {
        lookup_keys.push(format!("PL!HS-{}#", rest));
    }

    for (ability_index, ability) in abilities.iter_mut().enumerate() {
        let key_suffix = ability_index.to_string();
        let key_candidates: Vec<String> = lookup_keys
            .iter()
            .map(|prefix| format!("{}{}", prefix, key_suffix))
            .collect();
        let key = key_candidates
            .iter()
            .find(|candidate| index.contains_key(candidate.as_str()))
            .cloned()
            .unwrap_or_else(|| format!("{}#{}", card_no, ability_index));
        let entry = index.get(&key);
        let matching_entry = entry.filter(|entry| entry_matches_ability_trigger(entry, ability));

        if ability.raw_text.is_empty() {
            if let Some(source_text) = matching_entry
                .and_then(|value| value.get("source_text"))
                .and_then(|v| v.as_str())
            {
                ability.raw_text = source_text.to_string();
            } else if let Some(source_text_en) = matching_entry
                .and_then(|value| value.get("source_text_en"))
                .and_then(|v| v.as_str())
            {
                ability.raw_text = source_text_en.to_string();
            } else if let Some(source_text) = entry.and_then(|value| value.get("source_text")).and_then(|v| v.as_str()) {
                ability.raw_text = source_text.to_string();
            } else if let Some(source_text_en) = entry.and_then(|value| value.get("source_text_en")).and_then(|v| v.as_str()) {
                ability.raw_text = source_text_en.to_string();
            } else if let Some(text) = key_candidates
                .iter()
                .find_map(|candidate| text_index.get(candidate))
            {
                ability.raw_text = text.clone();
            }
        }

        if let Some(entry) = matching_entry {
            let program = sparse_entry_to_frame_program(entry);
            if !program.frames.is_empty() {
                ability.frame_program = Some(program);
            }
        }
        if let Some(choose_count) = ability
            .effects
            .iter()
            .find(|effect| {
                effect.runtime_opcode == O_LOOK_AND_CHOOSE
                    || effect.effect_type == EffectType::LookAndChoose
                    || effect.params.get("choose_count").is_some()
                    || effect.params.get("CHOOSE_COUNT").is_some()
            })
            .and_then(|effect| {
                effect
                    .params
                    .get("choose_count")
                    .or_else(|| effect.params.get("CHOOSE_COUNT"))
            })
            .and_then(parse_u8_value)
        {
            if let Some(program) = ability.frame_program.as_mut() {
                if let Some(frame) = program
                    .frames
                    .iter_mut()
                    .find(|f| f.opcode == O_LOOK_AND_CHOOSE)
                {
                    let mut lac = frame.look_choose();
                    if lac.choose_count == 0 {
                        lac.choose_count = choose_count;
                        frame.value = lac.to_raw();
                        if frame.params.is_null() {
                            frame.params = serde_json::json!({});
                        }
                        if let Some(params) = frame.params.as_object_mut() {
                            params.insert(
                                "choose_count".to_string(),
                                serde_json::Value::from(choose_count),
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
        if let Some(program) = ability.frame_program.as_ref() {
            let meaningful_frames: Vec<_> = program
                .frames
                .iter()
                .filter(|frame| frame_matches_effect_metadata(frame))
                .collect();
            let mut next_frame_idx = 0usize;
            for effect in ability.effects.iter_mut() {
                let expected_opcode = if effect.runtime_opcode != 0 {
                    effect.runtime_opcode
                } else {
                    AbilityFrame::opcode_from_effect_type(effect.effect_type)
                };
                let Some((matched_idx, frame)) = meaningful_frames
                    .iter()
                    .enumerate()
                    .skip(next_frame_idx)
                    .find(|(_, frame)| frame.opcode() == expected_opcode)
                else {
                    continue;
                };
                next_frame_idx = matched_idx + 1;
                let components = frame.components();
                let needs_params = effect.params.is_null()
                    || effect
                        .params
                        .as_object()
                        .map(|params| params.is_empty() || !params.contains_key("choices"))
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
                if effect.runtime_opcode == O_MOVE_TO_DISCARD && effect.runtime_slot == 0 {
                    let raw_text = ability.raw_text.to_ascii_lowercase();
                    if ability.raw_text.contains("手札") || raw_text.contains("hand") {
                        let mut slot = DecodedSlot::decode(effect.runtime_slot);
                        slot.source_zone = Zone::Hand;
                        effect.runtime_slot = slot.to_raw();
                    }
                }
                if !effect.is_optional {
                    let raw_text = ability.raw_text.to_ascii_lowercase();
                    effect.is_optional = components.is_optional()
                        || (
                            matches!(
                                effect.runtime_opcode,
                                O_MOVE_TO_DISCARD
                                    | O_SELECT_MODE
                                    | O_SELECT_CARDS
                                    | O_LOOK_AND_CHOOSE
                                    | O_SELECT_MEMBER
                                    | O_SELECT_LIVE
                                    | O_SELECT_PLAYER
                                    | O_PAY_ENERGY
                            )
                                && (ability.raw_text.contains("もよい")
                                    || raw_text.contains("may")
                                    || raw_text.contains("optional"))
                        );
                }
            }
        }
        if ability.pseudocode.is_empty() {
            if let Some(pseudo) = matching_entry
                .and_then(|value| value.get("pseudocode"))
                .and_then(|v| v.as_str())
            {
                ability.pseudocode = pseudo.to_string();
            } else if let Some(pseudo) = entry.and_then(|value| value.get("pseudocode")).and_then(|v| v.as_str()) {
                ability.pseudocode = pseudo.to_string();
            }
        }
    }

    Ok(())
}

pub(crate) fn entry_matches_ability_trigger(entry: &Value, ability: &Ability) -> bool {
    if let Some(trigger_id) = entry.get("trigger_id").and_then(|value| value.as_u64()) {
        return trigger_id == ability.trigger as u64;
    }

    let Some(trigger_name) = entry.get("trigger").and_then(|value| value.as_str()) else {
        return true;
    };

    trigger_name.eq_ignore_ascii_case(trigger_name_for_ability(ability.trigger))
}

fn trigger_name_for_ability(trigger: TriggerType) -> &'static str {
    match trigger {
        TriggerType::None => "NONE",
        TriggerType::OnPlay => "ON_PLAY",
        TriggerType::OnLiveStart => "ON_LIVE_START",
        TriggerType::OnLiveSuccess => "ON_LIVE_SUCCESS",
        TriggerType::TurnStart => "TURN_START",
        TriggerType::TurnEnd => "TURN_END",
        TriggerType::Constant => "CONSTANT",
        TriggerType::Activated => "ACTIVATED",
        TriggerType::OnLeaves => "ON_LEAVES",
        TriggerType::OnReveal => "ON_REVEAL",
        TriggerType::OnPositionChange => "ON_POSITION_CHANGE",
        TriggerType::OnAbilityResolve => "ON_ABILITY_RESOLVE",
        TriggerType::OnAbilitySuccess => "ON_ABILITY_SUCCESS",
        TriggerType::OnMoveToDiscard => "ON_MOVE_TO_DISCARD",
        TriggerType::OnMemberTap => "ON_MEMBER_TAP",
    }
}

pub(crate) fn frame_matches_effect_metadata(frame: &AbilityFrame) -> bool {
    let opcode = frame.opcode();
    opcode != O_RETURN
        && opcode != O_JUMP
        && opcode != O_JUMP_IF_FALSE
        && parse_condition_type(opcode) == ConditionType::None
}

pub(crate) fn sparse_entry_to_frame_program(entry: &Value) -> FrameProgram {
    let mut program_frames = Vec::new();
    if let Some(frames) = entry.get("frames").and_then(|v| v.as_array()) {
        for frame in frames {
            program_frames.push(parse_semantic_frame(frame));
        }
    }
    FrameProgram {
        frames: program_frames,
        raw_program: Some(entry.clone()),
    }
}

pub(crate) fn parse_semantic_frame(frame: &Value) -> AbilityFrame {
    AbilityFrame::from_json_value(frame)
}

pub(crate) fn parse_u8_value(value: &Value) -> Option<u8> {
    value
        .as_u64()
        .or_else(|| value.as_str().and_then(|s| s.parse::<u64>().ok()))
        .map(|v| v as u8)
}