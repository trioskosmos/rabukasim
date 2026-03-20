use engine_rust::core::enums::*;
use engine_rust::core::logic::interpreter::instruction::{
    DecodedFilterAttr, DecodedHeartCounts, DecodedHeartRequirements, DecodedLookAndChoose,
    DecodedSlot,
};
use serde_json::{json, Map, Value};
use std::fs;
use std::path::PathBuf;

fn reverse_map(value: &Value) -> std::collections::HashMap<i64, String> {
    let mut out = std::collections::HashMap::new();
    if let Some(obj) = value.as_object() {
        for (name, raw) in obj {
            if let Some(id) = raw.as_i64() {
                out.insert(id, name.clone());
            }
        }
    }
    out
}

fn opcode_label(metadata: &Value, opcode_id: i64) -> (&'static str, String) {
    if (1000..2000).contains(&opcode_id) {
        let base_id = opcode_id - 1000;
        for section in ["conditions", "opcodes"] {
            if let Some(obj) = metadata.get(section).and_then(|v| v.as_object()) {
                for (name, raw) in obj {
                    if raw.as_i64() == Some(base_id) {
                        return (section, name.clone());
                    }
                }
            }
        }
    }
    for section in ["opcodes", "action_bases", "conditions", "costs"] {
        if let Some(obj) = metadata.get(section).and_then(|v| v.as_object()) {
            for (name, raw) in obj {
                if raw.as_i64() == Some(opcode_id) {
                    return (section, name.clone());
                }
            }
        }
    }
    ("opcodes", format!("OP_{}", opcode_id))
}

fn sparse_num(map: &mut Map<String, Value>, key: &str, value: i64) {
    if value != 0 {
        map.insert(key.to_string(), json!(value));
    }
}

fn sparse_bool(map: &mut Map<String, Value>, key: &str, value: bool) {
    if value {
        map.insert(key.to_string(), json!(true));
    }
}

fn zone_name(zone: Zone) -> Option<&'static str> {
    match zone {
        Zone::DeckTop => Some("DECK_TOP"),
        Zone::DeckBottom => Some("DECK_BOTTOM"),
        Zone::Energy => Some("ENERGY"),
        Zone::Stage => Some("STAGE"),
        Zone::Deck => Some("DECK"),
        Zone::Hand => Some("HAND"),
        Zone::Discard => Some("DISCARD"),
        Zone::LiveSet => Some("LIVE_SET"),
        Zone::SuccessPile => Some("SUCCESS_PILE"),
        Zone::Yell => Some("YELL"),
        _ => None,
    }
}

fn decode_value(opcode: &str, raw: Option<i64>) -> Option<Value> {
    let raw = raw?;
    if raw == 0 {
        return None;
    }

    match opcode {
        "SET_HEART_COST" => {
            let counts = DecodedHeartCounts::decode(raw as i32);
            let mut obj = Map::new();
            sparse_num(&mut obj, "pink", counts.pink as i64);
            sparse_num(&mut obj, "red", counts.red as i64);
            sparse_num(&mut obj, "yellow", counts.yellow as i64);
            sparse_num(&mut obj, "green", counts.green as i64);
            sparse_num(&mut obj, "blue", counts.blue as i64);
            sparse_num(&mut obj, "purple", counts.purple as i64);
            sparse_num(&mut obj, "any", counts.any as i64);
            Some(Value::Object(obj))
        }
        "LOOK_AND_CHOOSE" => {
            let decoded = DecodedLookAndChoose::decode(raw as i32);
            let mut obj = Map::new();
            sparse_num(&mut obj, "count", decoded.count as i64);
            sparse_num(&mut obj, "char_id_1", decoded.char_id_1 as i64);
            sparse_num(&mut obj, "char_id_2", decoded.char_id_2 as i64);
            sparse_num(&mut obj, "char_id_3", decoded.char_id_3 as i64);
            sparse_bool(&mut obj, "reveal", decoded.reveal);
            sparse_bool(&mut obj, "dest_discard", decoded.dest_discard);
            Some(Value::Object(obj))
        }
        "CALC_SUM_COST" => {
            let base_value = (raw & 0xffff) as i64;
            let divisor = ((raw >> 16) & 0xffff) as i64;
            let mut obj = Map::new();
            sparse_num(&mut obj, "base_value", base_value);
            sparse_num(&mut obj, "divisor", divisor);
            Some(Value::Object(obj))
        }
        _ => Some(json!(raw)),
    }
}

fn decode_attr(opcode: &str, attr_low: Option<i64>, attr_high: Option<i64>) -> Option<Value> {
    let low = attr_low.unwrap_or(0) as u64;
    let high = attr_high.unwrap_or(0) as u64;
    let raw = ((high & 0xffff_ffff) << 32) | (low & 0xffff_ffff);
    if raw == 0 {
        return None;
    }

    if opcode == "SET_HEART_COST" {
        let decoded = DecodedHeartRequirements::decode(raw as i64);
        let mut obj = Map::new();
        for (idx, req) in decoded.reqs.iter().enumerate() {
            sparse_num(&mut obj, &format!("req_{}", idx + 1), *req as i64);
        }
        return Some(Value::Object(obj));
    }

    let decoded = DecodedFilterAttr::decode(raw as i64);
    let mut obj = Map::new();
    sparse_num(&mut obj, "target_player", decoded.target_player as i64);
    sparse_num(&mut obj, "card_type", decoded.card_type as i64);
    sparse_bool(&mut obj, "group_enabled", decoded.group_enabled);
    sparse_num(&mut obj, "group_id", decoded.group_id as i64);
    sparse_bool(&mut obj, "is_tapped", decoded.is_tapped);
    sparse_bool(&mut obj, "has_blade_heart", decoded.has_blade_heart);
    sparse_bool(&mut obj, "not_has_blade_heart", decoded.not_has_blade_heart);
    sparse_bool(&mut obj, "unique_names", decoded.unique_names);
    sparse_bool(&mut obj, "unit_enabled", decoded.unit_enabled);
    sparse_num(&mut obj, "unit_id", decoded.unit_id as i64);
    sparse_bool(&mut obj, "value_enabled", decoded.value_enabled);
    sparse_num(&mut obj, "value_threshold", decoded.value_threshold as i64);
    sparse_bool(&mut obj, "is_le", decoded.is_le);
    sparse_bool(&mut obj, "is_cost_type", decoded.is_cost_type);
    sparse_num(&mut obj, "color_mask", decoded.color_mask as i64);
    sparse_num(&mut obj, "char_id_1", decoded.char_id_1 as i64);
    sparse_num(&mut obj, "char_id_2", decoded.char_id_2 as i64);
    sparse_num(&mut obj, "char_id_3", decoded.char_id_3 as i64);
    sparse_num(&mut obj, "zone_mask", decoded.zone_mask as i64);
    sparse_num(&mut obj, "special_id", decoded.special_id as i64);
    sparse_bool(&mut obj, "is_setsuna", decoded.is_setsuna);
    sparse_bool(&mut obj, "compare_accumulated", decoded.compare_accumulated);
    sparse_bool(&mut obj, "is_optional", decoded.is_optional);
    sparse_bool(&mut obj, "keyword_energy", decoded.keyword_energy);
    sparse_bool(&mut obj, "keyword_member", decoded.keyword_member);
    Some(Value::Object(obj))
}

fn decode_slot(raw_slot: Option<i64>) -> Option<Value> {
    let raw = raw_slot.unwrap_or(0);
    if raw == 0 {
        return None;
    }

    let decoded = DecodedSlot::decode(raw as i32);
    let mut obj = Map::new();
    sparse_num(&mut obj, "target_slot", decoded.target_slot as i64);
    sparse_num(&mut obj, "remainder_zone", decoded.remainder_zone as i64);
    if let Some(name) = zone_name(decoded.source_zone) {
        obj.insert("source_zone".to_string(), json!(name));
    }
    if let Some(name) = zone_name(decoded.dest_zone) {
        obj.insert("dest_zone".to_string(), json!(name));
    }
    sparse_bool(&mut obj, "is_opponent", decoded.is_opponent);
    sparse_bool(&mut obj, "is_reveal_until_live", decoded.is_reveal_until_live);
    sparse_bool(&mut obj, "is_baton_slot", decoded.is_baton_slot);
    sparse_bool(&mut obj, "is_empty_slot", decoded.is_empty_slot);
    sparse_bool(&mut obj, "is_wait", decoded.is_wait);
    sparse_bool(&mut obj, "is_dynamic", decoded.is_dynamic);
    sparse_num(&mut obj, "area_idx", decoded.area_idx as i64);
    Some(Value::Object(obj))
}

fn semanticize_frame(frame: &Value, metadata: &Value) -> Value {
    let mut obj = Map::new();
    let opcode_id = frame.get("opcode_id").and_then(|v| v.as_i64()).unwrap_or(0);
    let negated = (1000..2000).contains(&opcode_id);
    let (opcode_section, opcode_name) = opcode_label(metadata, opcode_id);

    obj.insert("opcode_id".to_string(), json!(opcode_id));
    obj.insert("opcode".to_string(), json!(opcode_name.clone()));
    obj.insert("opcode_section".to_string(), json!(opcode_section));
    if negated {
        obj.insert("negated".to_string(), json!(true));
    }

    if let Some(value) = decode_value(&opcode_name, frame.get("value").and_then(|v| v.as_i64())) {
        obj.insert("value".to_string(), value);
    }
    if let Some(attr) = decode_attr(
        &opcode_name,
        frame.get("attr_low").and_then(|v| v.as_i64()),
        frame.get("attr_high").and_then(|v| v.as_i64()),
    ) {
        obj.insert("attr".to_string(), attr);
    }
    if let Some(slot) = decode_slot(frame.get("slot").and_then(|v| v.as_i64())) {
        obj.insert("slot".to_string(), slot);
    }
    if let Some(decoded) = frame.get("decoded").and_then(|v| v.as_str()) {
        obj.insert("decoded".to_string(), json!(decoded));
    }

    Value::Object(obj)
}

fn collect_choice_blocks(frames: &[Value]) -> Vec<Value> {
    let mut blocks = Vec::new();
    let mut i = 0usize;

    while i < frames.len() {
        let frame = &frames[i];
        if frame.get("opcode").and_then(|v| v.as_str()) == Some("SELECT_MODE") {
            let option_count = frame.get("value").and_then(|v| v.as_i64()).unwrap_or(0).max(0) as usize;
            if option_count > 0 && i + 1 + option_count <= frames.len() {
                let jump_table = &frames[i + 1..i + 1 + option_count];
                if jump_table.iter().all(|j| j.get("opcode").and_then(|v| v.as_str()) == Some("JUMP")) {
                    let mut targets: Vec<usize> = Vec::new();
                    for (jump_index, jump) in jump_table.iter().enumerate() {
                        let jump_value = jump.get("value").and_then(|v| v.as_i64()).unwrap_or(0);
                        let target = (i as i64 + 1 + jump_index as i64 + jump_value).max(0) as usize;
                        targets.push(target);
                    }

                    let mut end_index = frames.len();
                    for idx in i + 1 + option_count..frames.len() {
                        if frames[idx].get("opcode").and_then(|v| v.as_str()) == Some("RETURN") {
                            end_index = idx + 1;
                            break;
                        }
                    }

                    let mut options = Vec::new();
                    for (option_index, target_index) in targets.iter().enumerate() {
                        let mut next_target = end_index;
                        for future_target in targets.iter().skip(option_index + 1) {
                            if future_target > target_index {
                                next_target = *future_target;
                                break;
                            }
                        }

                        let start = (*target_index).min(frames.len());
                        let end = next_target.min(frames.len());
                        let body: Vec<Value> = frames[start..end].iter().cloned().collect();
                        let mut option = Map::new();
                        option.insert("index".to_string(), json!(option_index));
                        option.insert("jump_target".to_string(), json!(target_index));
                        option.insert("frames".to_string(), Value::Array(body));
                        options.push(Value::Object(option));
                    }

                    let mut block = Map::new();
                    block.insert("selector_frame_index".to_string(), json!(i));
                    block.insert("option_count".to_string(), json!(option_count));
                    block.insert("jump_table".to_string(), Value::Array(jump_table.iter().cloned().collect()));
                    block.insert("options".to_string(), Value::Array(options));
                    blocks.push(Value::Object(block));
                    i += 1 + option_count;
                    continue;
                }
            }
        }
        i += 1;
    }

    blocks
}

fn strip_entry(value: &mut Value, metadata: &Value) {
    if let Some(abilities) = value.get_mut("abilities").and_then(|v| v.as_array_mut()) {
        for ability in abilities {
            if let Some(obj) = ability.as_object_mut() {
                obj.remove("bytecode");
                obj.remove("model");
                obj.remove("sparse_model");
                obj.remove("signature_source");
                obj.remove("round_trip_bytecode");

                if let Some(frames) = obj.get_mut("frames").and_then(|v| v.as_array_mut()) {
                    let mut opcode_names = Vec::new();
                    for frame in frames {
                        let semantic = semanticize_frame(frame, metadata);
                        if let Some(opcode_name) = semantic.get("opcode").and_then(|v| v.as_str()) {
                            if !opcode_names.iter().any(|name: &String| name == opcode_name) {
                                opcode_names.push(opcode_name.to_string());
                            }
                        }
                        *frame = semantic;
                    }
                    obj.insert("opcode_names".to_string(), Value::Array(opcode_names.into_iter().map(Value::String).collect()));
                    let choice_blocks = collect_choice_blocks(frames);
                    if !choice_blocks.is_empty() {
                        obj.insert("choices".to_string(), Value::Array(choice_blocks));
                    }
                }
            }
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let path = PathBuf::from("../data/ability_frame_index.json");
    let metadata_path = PathBuf::from("../data/metadata.json");
    let raw = fs::read_to_string(&path)?;
    let metadata_raw = fs::read_to_string(&metadata_path)?;
    let metadata: Value = serde_json::from_str(&metadata_raw)?;
    let mut value: Value = serde_json::from_str(&raw)?;
    strip_entry(&mut value, &metadata);
    fs::write(&path, serde_json::to_string_pretty(&value)?)?;
    println!("rewrote {}", path.display());
    Ok(())
}
