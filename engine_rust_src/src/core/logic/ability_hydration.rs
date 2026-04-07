use super::models::*;
use crate::core::enums::{ConditionType, EffectType, TriggerType};
use crate::core::generated_constants::O_NOP;
use crate::core::generated_constants::*;
use crate::core::logic::interpreter::conditions::common::parse_condition_type;
use serde_json::Value;
use std::collections::HashMap;
use std::fmt::Write;
use std::fs;

const EMBEDDED_ABILITY_FRAME_SOURCE_JSON: &str =
    include_str!("../../../../data/ability_frame_source.json");
const EMBEDDED_CARD_122_OVERLAY_JSON: &str =
    include_str!("../../../../data/card_122_overlay.json");

pub(crate) struct SparseAbilityAssets {
    pub ability_index: HashMap<String, Value>,
    pub text_index: HashMap<String, String>,
}

fn raw_text_implies_once_per_turn(text: &str) -> bool {
    text.contains("{{turn1.png") || text.contains("ターン1回")
}

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

fn sparse_entry_card_refs<'a>(
    ability_data: &'a Value,
) -> Box<dyn Iterator<Item = (&'a str, i64)> + 'a> {
    if let Some(card_refs) = ability_data.get("card_refs").and_then(|v| v.as_array()) {
        Box::new(card_refs.iter().filter_map(|card_ref| {
            let card_obj = card_ref.as_object()?;
            let card_no = card_obj.get("card_no").and_then(|v| v.as_str())?;
            let ability_index = card_obj.get("ability_index").and_then(|v| v.as_i64())?;
            Some((card_no, ability_index))
        }))
    } else if let Some(cards) = ability_data.get("cards").and_then(|v| v.as_array()) {
        Box::new(cards.iter().filter_map(|card| {
            let card_entry = card.as_str()?;
            let card_no = card_entry.split(" | ").next()?;
            let ability_index_part = card_entry.split("(ab#").nth(1)?;
            let ability_index = ability_index_part
                .split_whitespace()
                .next()?
                .trim_end_matches(')')
                .parse::<i64>()
                .ok()?;
            Some((card_no, ability_index))
        }))
    } else {
        Box::new(std::iter::empty())
    }
}

fn process_sparse_ability_data(
    ability_data: &Value,
    index: &mut HashMap<String, Value>,
    text_index: &mut HashMap<String, String>,
) {
    let Some(frames) = ability_data.get("frames").and_then(|v| v.as_array()) else {
        return;
    };

    let mut compact_entry = serde_json::Map::new();
    for key in [
        "pseudocode",
        "source_text",
        "source_text_en",
        "trigger",
        "trigger_id",
        "raw_text",
        "is_once_per_turn",
        "requires_selection",
        "choice_flags",
        "choice_count",
    ] {
        if let Some(value) = ability_data.get(key) {
            compact_entry.insert(key.to_string(), value.clone());
        }
    }
    compact_entry.insert("frames".to_string(), Value::Array(frames.clone()));

    if let Some(source_text) = ability_data.get("source_text").and_then(|v| v.as_str()) {
        for (card_no, ability_index) in sparse_entry_card_refs(ability_data) {
            let key = format!("{}#{}", card_no, ability_index);
            text_index.insert(key, source_text.to_string());
        }
    }

    for (card_no, ability_index) in sparse_entry_card_refs(ability_data) {
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

pub(crate) fn load_sparse_assets_from_json(json: &str) -> SparseAbilityAssets {
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
        let mut text_index = HashMap::new();
        if let Some(abilities_arr) = root.get("abilities").and_then(|v| v.as_array()) {
            for ability_data in abilities_arr {
                process_sparse_ability_data(ability_data, &mut index, &mut text_index);
            }
        } else if let Some(abilities_obj) = root.as_object() {
            for ability_data in abilities_obj.values() {
                process_sparse_ability_data(ability_data, &mut index, &mut text_index);
            }
        }

        return SparseAbilityAssets {
            ability_index: index,
            text_index,
        };
    }
    SparseAbilityAssets {
        ability_index: HashMap::new(),
        text_index: HashMap::new(),
    }
}

pub(crate) fn load_sparse_assets() -> SparseAbilityAssets {
    fn load_first_nonempty<'a, I>(sources: I) -> SparseAbilityAssets
    where
        I: IntoIterator<Item = &'a str>,
    {
        for json in sources {
            let assets = load_sparse_assets_from_json(json);
            if !assets.ability_index.is_empty() || !assets.text_index.is_empty() {
                return assets;
            }
        }

        SparseAbilityAssets {
            ability_index: HashMap::new(),
            text_index: HashMap::new(),
        }
    }

    for path in [
        "data/ability_frame_source.json",
        "../data/ability_frame_source.json",
    ] {
        if let Ok(json) = fs::read_to_string(path) {
            let assets = load_sparse_assets_from_json(&json);
            if !assets.ability_index.is_empty() || !assets.text_index.is_empty() {
                return assets;
            }
        }
    }

    load_first_nonempty([EMBEDDED_ABILITY_FRAME_SOURCE_JSON, EMBEDDED_CARD_122_OVERLAY_JSON])
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
            if ability.choice_flags == 0 {
                ability.choice_flags = entry
                    .get("choice_flags")
                    .and_then(parse_u8_value)
                    .unwrap_or(0);
            }
            if ability.choice_count == 0 {
                ability.choice_count = entry
                    .get("choice_count")
                    .and_then(parse_u8_value)
                    .unwrap_or(0);
            }
            if !ability.requires_selection {
                ability.requires_selection = entry
                    .get("requires_selection")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
            }
            if !ability.is_once_per_turn {
                ability.is_once_per_turn = entry
                    .get("is_once_per_turn")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
            }
            let program = sparse_entry_to_frame_program(entry);
            if !program.frames.is_empty() {
                ability.frame_program = Some(program);
            }
        }
        if !ability.is_once_per_turn && raw_text_implies_once_per_turn(&ability.raw_text) {
            ability.is_once_per_turn = true;
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
                if !effect.is_optional {
                    effect.is_optional = components.is_optional();
                }
            }
        }
        if let Some(frame_program) = ability.frame_program.as_ref() {
            ability.conditions = derive_conditions_from_frame_program(frame_program);
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

fn authored_source_text(entry: &Value) -> Option<&str> {
    entry.get("source_text")
        .and_then(|value| value.as_str())
        .or_else(|| entry.get("primary_text_jp").and_then(|value| value.as_str()))
        .or_else(|| {
            entry.get("source_ability_texts")
                .and_then(|value| value.as_array())
                .and_then(|texts| texts.first())
                .and_then(|text| text.get("jp"))
                .and_then(|value| value.as_str())
        })
}

fn authored_nop_raw_conditions(source_text: &str) -> &'static [&'static str] {
    if source_text.contains("ユニット名がそれぞれ異なる") {
        &["UNIQUE_UNIT_NAMES_COUNT"]
    } else if source_text.contains("名前が異なるメンバーが3人以上") {
        &["UNIQUE_NAMES_COUNT"]
    } else if source_text.contains("名前とコストが両方ともそれぞれ異なる") {
        &[
            "UNIQUE_CARD_NAMES_COUNT",
            "UNIQUE_MEMBER_COSTS_COUNT",
        ]
    } else {
        &[]
    }
}

pub(crate) fn annotate_distinctness_nops_from_text(source_text: &str, frames: &mut [AbilityFrame]) {
    let expected_raw_conditions = authored_nop_raw_conditions(source_text);
    if expected_raw_conditions.is_empty() {
        return;
    }

    let mut raw_condition_idx = 0usize;
    for frame in frames.iter_mut() {
        if raw_condition_idx >= expected_raw_conditions.len() {
            break;
        }

        let frame_data = frame.components();
        let has_raw_condition = frame_data
            .params
            .and_then(|value| value.as_object())
            .map(|params| params.get("raw_cond").is_some() || params.get("RAW_COND").is_some())
            .unwrap_or(false);

        if frame_data.opcode != O_NOP
            || has_raw_condition
            || frame_data.value <= 0
        {
            continue;
        }

        frame.params = serde_json::json!({
            "raw_cond": expected_raw_conditions[raw_condition_idx],
            "GE": frame_data.value,
        });
        frame.attr = 0;
        raw_condition_idx += 1;
    }
}

fn annotate_distinctness_nops(entry: &Value, frames: &mut [AbilityFrame]) {
    let Some(source_text) = authored_source_text(entry) else {
        return;
    };
    annotate_distinctness_nops_from_text(source_text, frames);
}

pub(crate) fn sparse_entry_to_frame_program(entry: &Value) -> FrameProgram {
    let mut program_frames = Vec::new();
    if let Some(frames) = entry.get("frames").and_then(|v| v.as_array()) {
        for frame in frames {
            program_frames.push(parse_semantic_frame(frame));
        }
    }
    annotate_distinctness_nops(entry, &mut program_frames);
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
