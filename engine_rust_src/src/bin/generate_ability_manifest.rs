use serde_json::{Map, Value};
use std::collections::BTreeMap;
use std::fs;
use std::time::{SystemTime, UNIX_EPOCH};
use std::path::{Path, PathBuf};

const CONTROL_OPS: &[&str] = &["RETURN", "JUMP", "JUMP_IF_FALSE"];
const PROMPT_OPS: &[&str] = &[
    "SELECT_MODE",
    "SELECT_MEMBER",
    "SELECT_CARDS",
    "LOOK_AND_CHOOSE",
    "SELECT_PLAYER",
    "SELECT_LIVE",
    "OPPONENT_CHOOSE",
];
const COST_OPS: &[&str] = &[
    "PAY_ENERGY",
    "PAY_ENERGY_DYNAMIC",
    "MOVE_TO_DISCARD",
    "SET_TAPPED",
    "TAP_MEMBER",
    "ACTIVATE_ENERGY",
    "REDUCE_COST",
    "INCREASE_COST",
    "INCREASE_HEART_COST",
    "REDUCE_HEART_REQ",
    "REDUCE_LIVE_SET_LIMIT",
    "PREVENT_PLAY_TO_SLOT",
    "PREVENT_ACTIVATE",
    "PREVENT_BATON_TOUCH",
    "PREVENT_SET_TO_SUCCESS_PILE",
];

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("engine_rust_src must have a parent repo root")
        .to_path_buf()
}

fn read_json(path: &Path) -> Value {
    let text = fs::read_to_string(path)
        .unwrap_or_else(|err| panic!("failed to read {}: {err}", path.display()));
    serde_json::from_str(&text)
        .unwrap_or_else(|err| panic!("failed to parse {}: {err}", path.display()))
}

fn write_json(path: &Path, payload: &Value) {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .unwrap_or_else(|err| panic!("failed to create {}: {err}", parent.display()));
    }
    fs::write(
        path,
        serde_json::to_string_pretty(payload).expect("serialize manifest"),
    )
    .unwrap_or_else(|err| panic!("failed to write {}: {err}", path.display()));
}

fn metadata_lookup(map: &Value, section: &str, id: i32) -> String {
    let id = id as i64;
    map.get(section)
        .and_then(|v| v.as_object())
        .and_then(|obj| {
            obj.iter()
                .find_map(|(name, raw)| raw.as_i64().filter(|found| *found == id).map(|_| name.clone()))
        })
        .unwrap_or_else(|| format!("{}_{}", section.to_uppercase(), id))
}

fn trigger_name(metadata: &Value, id: i32) -> String {
    metadata_lookup(metadata, "triggers", id)
}

fn opcode_name(metadata: &Value, frame: &Value) -> String {
    if let Some(name) = frame
        .get("opcode")
        .or_else(|| frame.get("op"))
        .or_else(|| frame.get("opcode_name"))
        .or_else(|| frame.get("kind"))
        .and_then(Value::as_str)
    {
        return name.to_ascii_uppercase();
    }
    if let Some(id) = frame.get("opcode_id").and_then(Value::as_i64) {
        return metadata_lookup(metadata, "opcodes", id as i32);
    }
    "UNKNOWN".to_string()
}

fn frame_attr(frame: &Value) -> Option<&Value> {
    frame.get("attr").and_then(|value| value.is_object().then_some(value)).or_else(|| {
        frame
            .get("semantic")
            .and_then(|semantic| semantic.get("attr"))
            .and_then(|value| value.is_object().then_some(value))
    })
}

fn frame_slot(frame: &Value) -> Option<&Value> {
    frame.get("slot").and_then(|value| value.is_object().then_some(value)).or_else(|| {
        frame
            .get("semantic")
            .and_then(|semantic| semantic.get("slot"))
            .and_then(|value| value.is_object().then_some(value))
    })
}

fn is_optional_frame(frame: &Value) -> bool {
    if frame
        .get("attr")
        .and_then(|attr| attr.get("is_optional"))
        .and_then(Value::as_i64)
        .unwrap_or(0)
        != 0
    {
        return true;
    }

    frame
        .get("semantic")
        .and_then(|semantic| semantic.get("decoded"))
        .and_then(Value::as_str)
        .map(|decoded| decoded.to_ascii_lowercase().contains("optional"))
        .unwrap_or(false)
}

fn is_negated_frame(frame: &Value) -> bool {
    frame
        .get("is_negated")
        .and_then(Value::as_bool)
        .unwrap_or(false)
        || frame
            .get("negated")
            .and_then(Value::as_bool)
            .unwrap_or(false)
        || frame
            .get("semantic")
            .and_then(|semantic| semantic.get("negated"))
            .and_then(Value::as_bool)
            .unwrap_or(false)
}

fn friendly_zone(zone: Option<&Value>) -> String {
    let Some(zone) = zone.and_then(Value::as_str) else {
        return String::new();
    };
    match zone.to_ascii_uppercase().as_str() {
        "HAND" => "hand".to_string(),
        "DISCARD" => "discard".to_string(),
        "STAGE" => "stage".to_string(),
        "DECK" => "deck".to_string(),
        "DECK_TOP" => "top of deck".to_string(),
        "DECK_BOTTOM" => "bottom of deck".to_string(),
        "ENERGY" => "energy".to_string(),
        "LIVE" | "SUCCESS_PILE" => "success pile".to_string(),
        other => other.to_ascii_lowercase().replace('_', " "),
    }
}

fn frame_role(op: &str, optional: bool) -> &'static str {
    if CONTROL_OPS.contains(&op) {
        "control"
    } else if PROMPT_OPS.contains(&op) {
        "prompt"
    } else if COST_OPS.contains(&op) || optional {
        "cost"
    } else {
        "effect"
    }
}

fn compact_value(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut out = Map::new();
            for (key, item) in map {
                let keep = match item {
                    Value::Null => false,
                    Value::String(text) => !text.is_empty(),
                    Value::Array(items) => !items.is_empty(),
                    Value::Object(obj) => !obj.is_empty(),
                    _ => true,
                };
                if keep {
                    out.insert(key.clone(), compact_value(item));
                }
            }
            Value::Object(out)
        }
        Value::Array(items) => Value::Array(items.iter().map(compact_value).collect()),
        other => other.clone(),
    }
}

fn describe_frame(metadata: &Value, frame: &Value) -> String {
    let op = opcode_name(metadata, frame);
    let value = frame.get("value").and_then(Value::as_i64).unwrap_or(0);
    let attr = frame_attr(frame);
    let slot = frame_slot(frame);
    let optional = is_optional_frame(frame);
    let prefix = if optional && !CONTROL_OPS.contains(&op.as_str()) {
        "May "
    } else {
        ""
    };

    match op.as_str() {
        "RETURN" => "Done.".to_string(),
        "JUMP" => format!("Jump ahead {} frame(s).", value),
        "JUMP_IF_FALSE" => format!("Skip ahead {} frame(s) if the preceding condition fails.", value),
        "DRAW" => format!("{prefix}Draw {} card(s).", value),
        "BOOST_SCORE" => format!("{prefix}Gain +{} score.", value),
        "RECOVER_MEMBER" => {
            let source = friendly_zone(slot.and_then(|s| s.get("source_zone"))).if_empty("discard");
            let target = friendly_zone(slot.and_then(|s| s.get("dest_zone"))).if_empty("hand");
            format!("{prefix}Recover {} member(s) from {} to {}.", value, source, target)
        }
        "RECOVER_LIVE" => {
            let target = friendly_zone(slot.and_then(|s| s.get("dest_zone"))).if_empty("success pile");
            format!("{prefix}Recover {} live card(s) to {}.", value, target)
        }
        "MOVE_TO_DISCARD" => {
            let source = friendly_zone(slot.and_then(|s| s.get("source_zone"))).if_empty("hand");
            format!("{prefix}Move {} matching card(s) from {} to discard.", value, source)
        }
        "PAY_ENERGY" => format!("Pay {} energy.", value),
        "PAY_ENERGY_DYNAMIC" => format!("Pay dynamic energy cost ({}).", value),
        "SET_TAPPED" => "Tap the selected member.".to_string(),
        "TAP_MEMBER" => "Tap a member.".to_string(),
        "ACTIVATE_MEMBER" => "Untap the selected member.".to_string(),
        "SELECT_MEMBER" => format!("Choose {} member(s).", value),
        "SELECT_CARDS" => format!("Choose {} card(s).", value),
        "LOOK_AND_CHOOSE" => {
            let choose_count = attr
                .and_then(|a| a.get("choose_count"))
                .and_then(Value::as_i64)
                .unwrap_or(value);
            let look_count = attr
                .and_then(|a| a.get("look_count"))
                .and_then(Value::as_i64)
                .unwrap_or(value);
            format!("Look at {} card(s) and choose {}.", look_count, choose_count)
        }
        "SELECT_MODE" => format!("Choose one of {} mode(s).", value),
        "SELECT_PLAYER" => "Choose a player.".to_string(),
        "SELECT_LIVE" => "Choose a live card.".to_string(),
        "OPPONENT_CHOOSE" => "Opponent chooses.".to_string(),
        "PLAY_MEMBER_FROM_HAND" => "Play a member from hand.".to_string(),
        "PLAY_MEMBER_FROM_DISCARD" => "Play a member from discard.".to_string(),
        "PLAY_LIVE_FROM_DISCARD" => "Play a live card from discard.".to_string(),
        "ADD_TO_HAND" => format!("Add {} card(s) to hand.", value),
        "ADD_STAGE_ENERGY" => format!("Add {} energy to stage.", value),
        "ENERGY_CHARGE" => format!("Charge {} energy card(s).", value),
        "SET_SCORE" => format!("Set score to {}.", value),
        "REDUCE_SCORE" => format!("Reduce score by {}.", value),
        "SET_HEART_COST" => format!("Set heart cost to {}.", value),
        "SET_HEARTS" => format!("Set hearts to {}.", value),
        "SET_BLADES" => format!("Set blades to {}.", value),
        "ADD_BLADES" => format!("Gain {} blade(s).", value),
        "ADD_HEARTS" => format!("Gain {} heart(s).", value),
        "REDUCE_COST" => format!("Reduce cost by {}.", value),
        "INCREASE_COST" => format!("Increase cost by {}.", value),
        "INCREASE_HEART_COST" => format!("Increase heart cost by {}.", value),
        "REDUCE_HEART_REQ" => format!("Reduce heart requirement by {}.", value),
        "REDUCE_LIVE_SET_LIMIT" => format!("Reduce live set limit by {}.", value),
        "PREVENT_PLAY_TO_SLOT" => "Prevent play to the selected slot.".to_string(),
        "PREVENT_ACTIVATE" => "Prevent activation.".to_string(),
        "PREVENT_BATON_TOUCH" => "Prevent baton touch.".to_string(),
        "PREVENT_SET_TO_SUCCESS_PILE" => {
            "Prevent setting a card to the success pile.".to_string()
        }
        "LOOK_DECK" => format!("Look at {} card(s) from the deck.", value),
        "LOOK_DECK_DYNAMIC" => "Look at a dynamic number of cards from the deck.".to_string(),
        "LOOK_REORDER_DISCARD" => "Look and reorder discard.".to_string(),
        "REVEAL_CARDS" => format!("Reveal {} card(s).", value),
        "REVEAL_UNTIL" => "Reveal cards until the target is found.".to_string(),
        "SEARCH_DECK" => "Search the deck.".to_string(),
        "DRAW_UNTIL" => "Draw until a condition is met.".to_string(),
        "REPEAT_ABILITY" => "Repeat the ability.".to_string(),
        "CALC_SUM_COST" => "Calculate the summed cost.".to_string(),
        "TRANSFORM_COLOR" => "Transform color.".to_string(),
        "TRANSFORM_HEART" => "Transform heart.".to_string(),
        "TRANSFORM_BLADES" => "Transform blades.".to_string(),
        "ACTIVATE_ENERGY" => "Activate energy.".to_string(),
        "MOVE_MEMBER" => "Move a member.".to_string(),
        _ => {
            if let Some(decoded) = frame
                .get("semantic")
                .and_then(|semantic| semantic.get("decoded"))
                .and_then(Value::as_str)
            {
                let text = decoded
                    .split_once('|')
                    .map(|(_, tail)| tail.trim())
                    .unwrap_or(decoded);
                return text.chars().take(240).collect();
            }

            let mut fallback = Map::new();
            fallback.insert("value".to_string(), Value::from(value));
            if let Some(attr) = attr {
                fallback.insert("attr".to_string(), compact_value(attr));
            }
            if let Some(slot) = slot {
                fallback.insert("slot".to_string(), compact_value(slot));
            }
            format!("{} {}", op, Value::Object(fallback))
        }
    }
}

fn summarize_frames(metadata: &Value, frames: &[Value]) -> (String, String) {
    let meaningful: Vec<&Value> = frames
        .iter()
        .filter(|frame| opcode_name(metadata, frame) != "RETURN")
        .collect();
    if meaningful.is_empty() {
        return ("passive".to_string(), "No executable frames.".to_string());
    }

    let roles: Vec<&'static str> = meaningful
        .iter()
        .map(|frame| frame_role(&opcode_name(metadata, frame), is_optional_frame(frame)))
        .collect();
    let has_prompt = roles.iter().any(|role| *role == "prompt");
    let has_control = roles.iter().any(|role| *role == "control");
    let has_optional = meaningful.iter().any(|frame| is_optional_frame(frame));

    let pattern = if has_prompt && has_control {
        "prompted_branching"
    } else if has_prompt {
        "prompted"
    } else if has_control && has_optional {
        "optional_branching"
    } else if has_control {
        "branching"
    } else if has_optional {
        "optional_effect"
    } else {
        "linear"
    }
    .to_string();

    let descriptions: Vec<String> = meaningful
        .iter()
        .map(|frame| describe_frame(metadata, frame))
        .collect();

    let summary = if pattern == "optional_branching" {
        let cost_summary = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "cost")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_else(|| descriptions[0].clone());
        let effect_summary = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "effect")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_else(|| descriptions.last().cloned().unwrap_or_default());
        format!(
            "Optional cost: {}. If paid, {}",
            cost_summary.trim_end_matches('.'),
            lower_first(&effect_summary)
        )
    } else if pattern.starts_with("prompted") {
        let prompt_summary = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "prompt")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_else(|| descriptions[0].clone());
        let tail = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "effect")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_default();
        if tail.is_empty() || tail == prompt_summary {
            prompt_summary
        } else {
            format!("{}. Then {}", prompt_summary.trim_end_matches('.'), lower_first(&tail))
        }
    } else if pattern == "branching" {
        descriptions.join(" ")
    } else if pattern == "optional_effect" {
        descriptions[0].clone()
    } else {
        descriptions.join(" ")
    };

    (pattern, summary.trim().to_string())
}

fn lower_first(text: &str) -> String {
    let mut chars = text.chars();
    match chars.next() {
        Some(first) => format!("{}{}", first.to_ascii_lowercase(), chars.collect::<String>()),
        None => String::new(),
    }
}

fn normalize_frame(metadata: &Value, frame: &Value, index: usize) -> Value {
    let op = opcode_name(metadata, frame);
    let optional = is_optional_frame(frame);
    let mut normalized = Map::new();
    normalized.insert("index".to_string(), Value::from(index as i64));
    if let Some(id) = frame.get("opcode_id").and_then(Value::as_i64) {
        normalized.insert("opcode_id".to_string(), Value::from(id));
    }
    normalized.insert("opcode".to_string(), Value::String(op.clone()));
    normalized.insert(
        "role".to_string(),
        Value::String(frame_role(&op, optional).to_string()),
    );
    normalized.insert(
        "summary".to_string(),
        Value::String(describe_frame(metadata, frame)),
    );
    normalized.insert("optional".to_string(), Value::Bool(optional));
    normalized.insert("negated".to_string(), Value::Bool(is_negated_frame(frame)));

    if let Some(value) = frame.get("value") {
        normalized.insert("value".to_string(), value.clone());
    }
    if let Some(attr) = frame_attr(frame) {
        normalized.insert("attr".to_string(), compact_value(attr));
    }
    if let Some(slot) = frame_slot(frame) {
        normalized.insert("slot".to_string(), compact_value(slot));
    }
    if let Some(decoded) = frame
        .get("semantic")
        .and_then(|semantic| semantic.get("decoded"))
        .and_then(Value::as_str)
    {
        normalized.insert("decoded".to_string(), Value::String(decoded.to_string()));
    }

    Value::Object(normalized)
}

fn normalize_source_text(card: &Value) -> String {
    for key in ["original_text", "ability_text", "raw_text"] {
        if let Some(text) = card.get(key).and_then(Value::as_str) {
            let trimmed = text.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }
    }
    String::new()
}

fn iter_cards<'a>(cards_payload: &'a Value) -> Vec<(&'a str, &'a Value)> {
    let mut out = Vec::new();
    if let Some(obj) = cards_payload.as_object() {
        for (db_name, db) in obj {
            if !db_name.ends_with("_db") {
                continue;
            }
            if let Some(cards) = db.as_object() {
                for card in cards.values() {
                    if card
                        .get("abilities")
                        .and_then(Value::as_array)
                        .map(|abilities| !abilities.is_empty())
                        .unwrap_or(false)
                    {
                        out.push((db_name.as_str(), card));
                    }
                }
            }
        }
    }
    out
}

fn build_manifest(cards_payload: &Value, metadata: &Value) -> Value {
    let mut cards_out = Vec::new();
    let mut trigger_counts: BTreeMap<String, usize> = BTreeMap::new();
    let mut flow_counts: BTreeMap<String, usize> = BTreeMap::new();
    let mut opcode_counts: BTreeMap<String, usize> = BTreeMap::new();

    for (db_name, card) in iter_cards(cards_payload) {
        let card_no = card
            .get("card_no")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim()
            .to_string();
        let card_id = card.get("card_id").and_then(Value::as_i64).unwrap_or(0);
        let name = card
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string();
        let source_text = normalize_source_text(card);
        let source_text_en = card
            .get("original_text_en")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim()
            .to_string();
        let abilities = card
            .get("abilities")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();

        let mut abilities_out = Vec::new();

        for (ability_index, ability) in abilities.iter().enumerate() {
            let trigger_id = ability.get("trigger").and_then(Value::as_i64).unwrap_or(0) as i32;
            let trigger = trigger_name(metadata, trigger_id);
            let frames = ability
                .get("frame_program")
                .and_then(|program| program.get("frames"))
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();

            let mut frame_values = Vec::new();
            let mut opcode_sequence = Vec::new();
            for (idx, frame) in frames.iter().enumerate() {
                if !frame.is_object() {
                    continue;
                }
                let norm = normalize_frame(metadata, frame, idx);
                if let Some(op) = norm.get("opcode").and_then(Value::as_str) {
                    opcode_sequence.push(op.to_string());
                }
                frame_values.push(norm);
            }

            let (flow_pattern, summary) = summarize_frames(metadata, &frames);

            *trigger_counts.entry(trigger.clone()).or_default() += 1;
            *flow_counts.entry(flow_pattern.clone()).or_default() += 1;
            for opcode in &opcode_sequence {
                *opcode_counts.entry(opcode.clone()).or_default() += 1;
            }

            let ability_obj = serde_json::json!({
                "ability_index": ability_index,
                "trigger_id": trigger_id,
                "trigger": trigger,
                "flow_pattern": flow_pattern,
                "summary": summary,
                "frame_count": frame_values.len(),
                "opcode_sequence": opcode_sequence,
                "source_text": source_text,
                "source_text_en": source_text_en,
                "frames": frame_values,
                "choice_flags": ability.get("choice_flags").cloned().unwrap_or(Value::from(0)),
                "choice_count": ability.get("choice_count").cloned().unwrap_or(Value::from(0)),
                "requires_selection": ability.get("requires_selection").cloned().unwrap_or(Value::Bool(false)),
                "is_once_per_turn": ability.get("is_once_per_turn").cloned().unwrap_or(Value::Bool(false)),
                "card_no": card_no,
                "card_id": card_id,
                "name": name,
                "db": db_name,
            });
            abilities_out.push(ability_obj);
        }

        if !abilities_out.is_empty() {
            cards_out.push(serde_json::json!({
                "card_id": card_id,
                "card_no": card_no,
                "name": name,
                "db": db_name,
                "ability_count": abilities_out.len(),
                "source_text": source_text,
                "source_text_en": source_text_en,
                "abilities": abilities_out,
            }));
        }
    }

    cards_out.sort_by(|a, b| {
        let a_no = a.get("card_no").and_then(Value::as_str).unwrap_or("");
        let b_no = b.get("card_no").and_then(Value::as_str).unwrap_or("");
        a_no.cmp(b_no)
            .then_with(|| a.get("card_id").and_then(Value::as_i64).cmp(&b.get("card_id").and_then(Value::as_i64)))
    });

    let total_abilities: usize = cards_out
        .iter()
        .map(|card| card.get("ability_count").and_then(Value::as_u64).unwrap_or(0) as usize)
        .sum();

    serde_json::json!({
        "generated_at": SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
            .to_string(),
        "source_cards": repo_root().join("data").join("cards_compiled.json").display().to_string(),
        "source_metadata": repo_root().join("data").join("metadata.json").display().to_string(),
        "schema": "ability_manifest.v1",
        "summary": {
            "card_count": cards_out.len(),
            "ability_count": total_abilities,
            "trigger_counts": trigger_counts,
            "flow_counts": flow_counts,
            "opcode_counts": opcode_counts,
        },
        "cards": cards_out,
    })
}

fn render_markdown(manifest: &Value) -> String {
    let summary = manifest.get("summary").and_then(Value::as_object).cloned().unwrap_or_default();
    let cards = manifest.get("cards").and_then(Value::as_array).cloned().unwrap_or_default();
    let mut out = String::new();
    out.push_str("# Ability System Manifest\n\n");
    out.push_str(&format!(
        "Generated: {}  Cards with abilities: {}  Total abilities: {}\n\n",
        manifest.get("generated_at").and_then(Value::as_str).unwrap_or(""),
        summary.get("card_count").and_then(Value::as_u64).unwrap_or(0),
        summary.get("ability_count").and_then(Value::as_u64).unwrap_or(0)
    ));
    out.push_str("## Summary\n\n");
    out.push_str("| Metric | Value |\n");
    out.push_str("| :-- | --: |\n");
    out.push_str(&format!(
        "| Cards | {} |\n",
        summary.get("card_count").and_then(Value::as_u64).unwrap_or(0)
    ));
    out.push_str(&format!(
        "| Abilities | {} |\n",
        summary.get("ability_count").and_then(Value::as_u64).unwrap_or(0)
    ));

    out.push_str("\n### Trigger Counts\n");
    if let Some(map) = summary.get("trigger_counts").and_then(Value::as_object) {
        for (name, count) in map {
            out.push_str(&format!("- `{}`: {}\n", name, count.as_u64().unwrap_or(0)));
        }
    }
    out.push_str("\n### Flow Counts\n");
    if let Some(map) = summary.get("flow_counts").and_then(Value::as_object) {
        for (name, count) in map {
            out.push_str(&format!("- `{}`: {}\n", name, count.as_u64().unwrap_or(0)));
        }
    }

    out.push_str("\n## Cards\n");
    for card in cards {
        let card_no = card.get("card_no").and_then(Value::as_str).unwrap_or("");
        let name = card.get("name").and_then(Value::as_str).unwrap_or("");
        out.push_str(&format!("\n### {} - {}\n\n", card_no, name));
        out.push_str(&format!(
            "- `card_id`: {}\n",
            card.get("card_id").and_then(Value::as_i64).unwrap_or(0)
        ));
        out.push_str(&format!(
            "- `db`: `{}`\n",
            card.get("db").and_then(Value::as_str).unwrap_or("")
        ));

        if let Some(source_text) = card.get("source_text").and_then(Value::as_str) {
            if !source_text.is_empty() {
                out.push_str(&format!("\n```text\n{}\n```\n", source_text));
            }
        }

        if let Some(abilities) = card.get("abilities").and_then(Value::as_array) {
            for ability in abilities {
                let summary = ability.get("summary").and_then(Value::as_str).unwrap_or("");
                let opcode_sequence = ability
                    .get("opcode_sequence")
                    .and_then(Value::as_array)
                    .map(|ops| {
                        ops.iter()
                            .filter_map(Value::as_str)
                            .collect::<Vec<_>>()
                            .join(", ")
                    })
                    .unwrap_or_default();
                out.push_str(&format!(
                    "\n#### Ability {}\n\n",
                    ability.get("ability_index").and_then(Value::as_u64).unwrap_or(0) + 1
                ));
                out.push_str(&format!(
                    "- `trigger`: `{}`\n",
                    ability.get("trigger").and_then(Value::as_str).unwrap_or("")
                ));
                out.push_str(&format!(
                    "- `flow_pattern`: `{}`\n",
                    ability.get("flow_pattern").and_then(Value::as_str).unwrap_or("")
                ));
                out.push_str(&format!("- `summary`: {}\n", summary));
                out.push_str(&format!("- `opcode_sequence`: `{}`\n", opcode_sequence));
                if let Some(source_text_en) = ability.get("source_text_en").and_then(Value::as_str) {
                    if !source_text_en.is_empty() {
                        out.push_str(&format!("- `source_text_en`: {}\n", source_text_en));
                    }
                }

                out.push_str("\n| # | Role | Opcode | Summary |\n");
                out.push_str("| :-- | :-- | :-- | :-- |\n");
                if let Some(frames) = ability.get("frames").and_then(Value::as_array) {
                    for frame in frames {
                        out.push_str(&format!(
                            "| {} | {} | `{}` | {} |\n",
                            frame.get("index").and_then(Value::as_u64).unwrap_or(0),
                            frame.get("role").and_then(Value::as_str).unwrap_or(""),
                            frame.get("opcode").and_then(Value::as_str).unwrap_or(""),
                            frame
                                .get("summary")
                                .and_then(Value::as_str)
                                .unwrap_or("")
                                .replace('|', "\\|")
                        ));
                    }
                }
            }
        }
    }

    out
}

fn main() {
    let root = repo_root();
    let cards_path = root.join("data").join("cards_compiled.json");
    let metadata_path = root.join("data").join("metadata.json");
    let out_json = root.join("reports").join("ability_manifest.json");
    let out_md = root.join("reports").join("ability_manifest.md");

    let cards_payload = read_json(&cards_path);
    let metadata = read_json(&metadata_path);
    let manifest = build_manifest(&cards_payload, &metadata);

    write_json(&out_json, &manifest);
    fs::write(&out_md, render_markdown(&manifest))
        .unwrap_or_else(|err| panic!("failed to write {}: {err}", out_md.display()));

    println!("Wrote {}", out_json.display());
    println!("Wrote {}", out_md.display());
}

trait IfEmpty {
    fn if_empty(self, fallback: &str) -> String;
}

impl IfEmpty for String {
    fn if_empty(self, fallback: &str) -> String {
        if self.is_empty() {
            fallback.to_string()
        } else {
            self
        }
    }
}
