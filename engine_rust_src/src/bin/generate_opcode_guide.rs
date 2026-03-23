use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Default)]
struct OpcodeStat {
    opcode: String,
    opcode_id: i64,
    frame_count: usize,
    sections: BTreeSet<String>,
    value_fields: BTreeSet<String>,
    attr_fields: BTreeSet<String>,
    slot_fields: BTreeSet<String>,
    words_used: BTreeSet<String>,
    examples: Vec<String>,
    cards: Vec<String>,
    negated: bool,
}

impl OpcodeStat {
    fn new(opcode: String, opcode_id: i64) -> Self {
        Self {
            opcode,
            opcode_id,
            ..Self::default()
        }
    }
}

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

fn collect_frames<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {
    match node {
        Value::Object(map) => {
            if map.get("opcode_id").and_then(Value::as_i64).is_some()
                && map.get("opcode").and_then(Value::as_str).is_some()
            {
                out.push(node);
            }

            for key in ["frames", "choices", "options", "branches"] {
                if let Some(child) = map.get(key) {
                    collect_frames(child, out);
                }
            }
        }
        Value::Array(items) => {
            for item in items {
                collect_frames(item, out);
            }
        }
        _ => {}
    }
}

fn add_names_from_value(value: &Value, set: &mut BTreeSet<String>) {
    match value {
        Value::Object(map) => {
            if map.is_empty() {
                set.insert("object".to_string());
                return;
            }

            for (key, child) in map {
                set.insert(key.clone());
                add_names_from_value(child, set);
            }
        }
        Value::Array(items) => {
            if items.is_empty() {
                set.insert("array".to_string());
                return;
            }

            for child in items {
                add_names_from_value(child, set);
            }
        }
        Value::Bool(_) => {
            set.insert("bool".to_string());
        }
        Value::Number(_) => {
            set.insert("scalar".to_string());
        }
        Value::String(_) => {
            set.insert("string".to_string());
        }
        Value::Null => {
            set.insert("null".to_string());
        }
    }
}

fn escape_md(input: &str) -> String {
    input
        .replace('|', "\\|")
        .replace('\r', "")
        .trim()
        .to_string()
}

fn field_description(field: &str) -> &'static str {
    match field {
        "group_enabled" => "group filter toggle bit",
        "group_id" => "group / name-set filter id",
        "zone_mask" => "zone selection bitmask",
        "is_optional" => "optional branch / skip flag",
        "target_slot" => "target zone / board slot",
        "source_zone" => "source zone selector",
        "dest_zone" => "destination zone selector",
        "compare" => "comparison mode selector",
        "negated" => "negated condition wrapper",
        "char_id_3" => "packed character id word 3",
        "char_id_2" => "packed character id word 2",
        "char_id_1" => "packed character id word 1",
        "hearts" => "packed heart-cost triple or list",
        "count" => "count / repeat scalar",
        "min" => "minimum threshold",
        "max" => "maximum threshold",
        "value" => "primary scalar payload",
        "offset" => "relative branch offset",
        "filter" => "nested filter payload",
        "slot" => "nested slot payload",
        "attr" => "nested attr payload",
        "scalar" => "primitive scalar",
        "string" => "literal string",
        "bool" => "boolean flag",
        "null" => "explicit null",
        "object" => "nested object payload",
        "array" => "nested array payload",
        _ => "observed packed field",
    }
}

fn extract_named_ids(value: &Value) -> BTreeMap<String, i64> {
    let mut out = BTreeMap::new();
    if let Value::Object(map) = value {
        for (name, raw) in map {
            if let Some(id) = raw.as_i64() {
                out.insert(name.clone(), id);
            }
        }
    }
    out
}

fn flatten_layout(node: &Value, prefix: &str, rows: &mut Vec<(String, String)>) {
    match node {
        Value::Array(items) => {
            if items.len() == 2 && items[0].is_number() && items[1].is_number() {
                let start = items[0].as_i64().unwrap_or(-1);
                let end = items[1].as_i64().unwrap_or(-1);
                rows.push((prefix.to_string(), format!("{start}-{end}")));
                return;
            }

            for (idx, item) in items.iter().enumerate() {
                let next = if prefix.is_empty() {
                    idx.to_string()
                } else {
                    format!("{prefix}[{idx}]")
                };
                flatten_layout(item, &next, rows);
            }
        }
        Value::Object(map) => {
            if map.is_empty() {
                rows.push((prefix.to_string(), "present".to_string()));
                return;
            }

            for (key, child) in map {
                let next = if prefix.is_empty() {
                    key.clone()
                } else {
                    format!("{prefix}.{key}")
                };
                flatten_layout(child, &next, rows);
            }
        }
        Value::Number(n) => {
            rows.push((prefix.to_string(), n.to_string()));
        }
        Value::String(s) => {
            rows.push((prefix.to_string(), s.clone()));
        }
        Value::Bool(b) => {
            rows.push((prefix.to_string(), b.to_string()));
        }
        Value::Null => {
            rows.push((prefix.to_string(), "null".to_string()));
        }
    }
}

fn opcode_note(opcode: &str, stat: &OpcodeStat) -> String {
    match opcode {
        "JUMP" => "value is a relative branch offset; changes control flow only.".to_string(),
        "JUMP_IF_FALSE" => "value is a relative branch offset that is taken when the current condition fails.".to_string(),
        "SELECT_MODE" => "value is the option count; following JUMP frames form the branch table.".to_string(),
        "LOOK_AND_CHOOSE" => "value packs reveal counts and choice behavior; attr and slot decide filtering and destination rules.".to_string(),
        "SET_HEART_COST" => "value and attr pack the heart-cost shape; slot selects which target the change applies to.".to_string(),
        "CALC_SUM_COST" => "value selects the comparison / divisor shape; slot and attr decide how the sum is evaluated.".to_string(),
        "SELECT_MEMBER" => "value is the number of candidates; attr and slot define filters and target area.".to_string(),
        "RECOVER_LIVE" => "value is the card count; attr and slot define the recovery filter and source/destination zones.".to_string(),
        "MOVE_TO_DISCARD" => "value is the card count; attr and slot define optionality and move source/destination.".to_string(),
        "PAY_ENERGY" => "value is the energy cost; attr often carries optional / skip behavior.".to_string(),
        "DRAW_UNTIL" => "value controls the draw limit or stop condition; attr/slot define the search and destination.".to_string(),
        "REVEAL_UNTIL" => "value controls the reveal limit; attr/slot define the qualifying filter and destination.".to_string(),
        "PLACE_ENERGY_UNDER_MEMBER" => "value is the number of energy cards; attr and slot define target placement.".to_string(),
        "TAP_MEMBER" => "value is the number of members to tap; attr and slot define the target set.".to_string(),
        "ACTIVATE_ENERGY" => "value is the number of energy cards; slot resolves the board or player target.".to_string(),
        "SELECT_PLAYER" => "value is the number of choices; attr and slot decide which side can be selected.".to_string(),
        "OPPONENT_CHOOSE" => "value is the number of choices; attr and slot define the opponent-facing choice set.".to_string(),
        "PLAY_MEMBER_FROM_HAND" => "value is the number of members played; attr and slot define source and destination.".to_string(),
        "PLAY_MEMBER_FROM_DISCARD" => "value is the number of members played; attr and slot define source and destination.".to_string(),
        "ENERGY_CHARGE" => "value is the energy count; attr and slot decide where the energy enters.".to_string(),
        "SWAP_AREA" => "value is the swap count; slot decides the source and destination areas.".to_string(),
        "SWAP_ZONE" => "value is the swap count; slot decides the source and destination zones.".to_string(),
        "BOOST_SCORE" => "value is the score delta; attr and slot decide whether it is conditional or targeted.".to_string(),
        "REDUCE_COST" => "value is the cost delta; attr and slot decide the target and filters.".to_string(),
        "INCREASE_COST" => "value is the cost delta; attr and slot decide the target and filters.".to_string(),
        "REDUCE_HEART_REQ" => "value is the requirement delta; attr and slot decide the target and filters.".to_string(),
        "INCREASE_HEART_COST" => "value is the requirement delta; attr and slot decide the target and filters.".to_string(),
        "SET_TAPPED" => "value is the tapped count; slot decides which card or zone is affected.".to_string(),
        "RETURN" => "terminator only.".to_string(),
        "NOP" => "no data words are used.".to_string(),
        _ if stat.negated => "negated wrapper observed; semantics are controlled by the wrapped condition.".to_string(),
        _ => "mixed value / attr / slot usage observed.".to_string(),
    }
}

fn render_name_id_table(
    md: &mut String,
    title: &str,
    entries: &BTreeMap<String, i64>,
    stats: &BTreeMap<String, OpcodeStat>,
    include_usage: bool,
) {
    writeln!(md, "### {title}").unwrap();
    writeln!(md).unwrap();
    if include_usage {
        writeln!(md, "| Name | Id | Observed Frames | Words Used | Value Fields | Attr Fields | Slot Fields | Notes |").unwrap();
        writeln!(md, "| --- | ---: | ---: | --- | --- | --- | --- | --- |").unwrap();
    } else {
        writeln!(md, "| Name | Id | Notes |").unwrap();
        writeln!(md, "| --- | ---: | --- |").unwrap();
    }

    for (name, id) in entries {
        if include_usage {
            if let Some(stat) = stats.get(name) {
                let words_used = if stat.words_used.is_empty() {
                    "none".to_string()
                } else {
                    stat.words_used
                        .iter()
                        .cloned()
                        .collect::<Vec<_>>()
                        .join(", ")
                };
                let value_fields = if stat.value_fields.is_empty() {
                    "none".to_string()
                } else {
                    stat.value_fields
                        .iter()
                        .cloned()
                        .collect::<Vec<_>>()
                        .join(", ")
                };
                let attr_fields = if stat.attr_fields.is_empty() {
                    "none".to_string()
                } else {
                    stat.attr_fields
                        .iter()
                        .cloned()
                        .collect::<Vec<_>>()
                        .join(", ")
                };
                let slot_fields = if stat.slot_fields.is_empty() {
                    "none".to_string()
                } else {
                    stat.slot_fields
                        .iter()
                        .cloned()
                        .collect::<Vec<_>>()
                        .join(", ")
                };
                let note = opcode_note(name, stat);
                writeln!(
                    md,
                    "| {} | {} | {} | {} | {} | {} | {} | {} |",
                    escape_md(name),
                    id,
                    stat.frame_count,
                    escape_md(&words_used),
                    escape_md(&value_fields),
                    escape_md(&attr_fields),
                    escape_md(&slot_fields),
                    escape_md(&note),
                )
                .unwrap();
            } else {
                writeln!(
                    md,
                    "| {} | {} | 0 | none | none | none | none | not observed in current compiled cards |",
                    escape_md(name),
                    id
                ).unwrap();
            }
        } else {
            writeln!(
                md,
                "| {} | {} | not a frame family; reference table only |",
                escape_md(name),
                id
            )
            .unwrap();
        }
    }

    writeln!(md).unwrap();
}

fn render_layout_section(md: &mut String, title: &str, node: &Value) {
    let mut rows = Vec::new();
    flatten_layout(node, "", &mut rows);
    writeln!(md, "### {title}").unwrap();
    writeln!(md).unwrap();
    writeln!(md, "| Path | Bits / Value |").unwrap();
    writeln!(md, "| --- | --- |").unwrap();
    for (path, bits) in rows {
        writeln!(md, "| {} | {} |", escape_md(&path), escape_md(&bits)).unwrap();
    }
    writeln!(md).unwrap();
}

fn main() {
    let root = repo_root();
    let metadata_path = root.join("data").join("metadata.json");
    let index_path = root.join("data").join("ability_frame_index.json");
    let output_path = root.join("ability_codec_system").join("opcode_guide.md");

    let metadata = read_json(&metadata_path);
    let index = read_json(&index_path);
    let layout = metadata
        .get("bytecode_layout")
        .cloned()
        .unwrap_or(Value::Null);
    let opcode_entries = extract_named_ids(metadata.get("opcodes").unwrap_or(&Value::Null));
    let condition_entries = extract_named_ids(metadata.get("conditions").unwrap_or(&Value::Null));
    let cost_entries = extract_named_ids(metadata.get("costs").unwrap_or(&Value::Null));
    let action_base_entries =
        extract_named_ids(metadata.get("action_bases").unwrap_or(&Value::Null));
    let trigger_entries = extract_named_ids(metadata.get("triggers").unwrap_or(&Value::Null));
    let target_entries = extract_named_ids(metadata.get("targets").unwrap_or(&Value::Null));
    let slot_entries = extract_named_ids(metadata.get("slot_indices").unwrap_or(&Value::Null));
    let comparison_entries = extract_named_ids(metadata.get("comparisons").unwrap_or(&Value::Null));
    let zone_entries = extract_named_ids(metadata.get("zones").unwrap_or(&Value::Null));

    let abilities = index
        .get("abilities")
        .and_then(Value::as_array)
        .unwrap_or_else(|| panic!("{} missing abilities array", index_path.display()));

    let mut stats: BTreeMap<String, OpcodeStat> = BTreeMap::new();
    let mut field_usage: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();

    for ability in abilities {
        let mut frames = Vec::new();
        collect_frames(ability, &mut frames);

        let cards = ability
            .get("cards")
            .and_then(Value::as_array)
            .map(|items| {
                items
                    .iter()
                    .take(3)
                    .filter_map(|card| {
                        let card_no = card.get("card_no").and_then(Value::as_str)?;
                        let name = card.get("name").and_then(Value::as_str).unwrap_or("");
                        Some(format!("{card_no} ({name})"))
                    })
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();

        for frame in frames {
            let opcode = frame
                .get("opcode")
                .and_then(Value::as_str)
                .unwrap_or("UNKNOWN")
                .to_string();
            let opcode_id = frame.get("opcode_id").and_then(Value::as_i64).unwrap_or(-1);

            let stat = stats
                .entry(opcode.clone())
                .or_insert_with(|| OpcodeStat::new(opcode.clone(), opcode_id));
            stat.frame_count += 1;
            if let Some(section) =
                frame
                    .get("opcode_section")
                    .and_then(Value::as_str)
                    .or_else(|| {
                        frame
                            .get("semantic")
                            .and_then(|s| s.get("opcode_section"))
                            .and_then(Value::as_str)
                    })
            {
                stat.sections.insert(section.to_string());
            }

            if let Some(value) = frame.get("value") {
                if !value.is_null() {
                    stat.words_used.insert("value".to_string());
                    add_names_from_value(value, &mut stat.value_fields);
                    for field in stat.value_fields.iter().cloned().collect::<Vec<_>>() {
                        field_usage.entry(field).or_default().insert(opcode.clone());
                    }
                }
            }

            if let Some(attr) = frame.get("attr") {
                if !attr.is_null() {
                    stat.words_used.insert("attr".to_string());
                    add_names_from_value(attr, &mut stat.attr_fields);
                    for field in stat.attr_fields.iter().cloned().collect::<Vec<_>>() {
                        field_usage.entry(field).or_default().insert(opcode.clone());
                    }
                }
            }

            if let Some(slot) = frame.get("slot") {
                if !slot.is_null() {
                    stat.words_used.insert("slot".to_string());
                    add_names_from_value(slot, &mut stat.slot_fields);
                    for field in stat.slot_fields.iter().cloned().collect::<Vec<_>>() {
                        field_usage.entry(field).or_default().insert(opcode.clone());
                    }
                }
            }

            if frame
                .get("negated")
                .and_then(Value::as_bool)
                .unwrap_or(false)
            {
                stat.negated = true;
            }

            if stat.examples.len() < 3 {
                if let Some(decoded) = frame
                    .get("semantic")
                    .and_then(|s| s.get("decoded"))
                    .and_then(Value::as_str)
                {
                    stat.examples.push(decoded.to_string());
                } else if let Some(decoded) = frame.get("decoded").and_then(Value::as_str) {
                    stat.examples.push(decoded.to_string());
                }
            }

            for card in &cards {
                if !stat.cards.contains(card) {
                    stat.cards.push(card.clone());
                }
            }
        }
    }

    let mut md = String::new();
    writeln!(&mut md, "# Opcode Guide").unwrap();
    writeln!(&mut md).unwrap();
    writeln!(
        &mut md,
        "Generated from `data/metadata.json` and `data/ability_frame_index.json`."
    )
    .unwrap();
    writeln!(&mut md).unwrap();
    writeln!(&mut md, "This guide is field-based, not just byte-based: it shows which frame words and decoded fields each opcode family actually uses in the current compiled cards.").unwrap();
    writeln!(&mut md).unwrap();
    writeln!(&mut md, "## Frame Layout").unwrap();
    writeln!(&mut md).unwrap();
    writeln!(&mut md, "- Word 0: opcode id").unwrap();
    writeln!(&mut md, "- Word 1: value word").unwrap();
    writeln!(&mut md, "- Words 2-3: attr low / attr high words").unwrap();
    writeln!(&mut md, "- Word 4: slot word").unwrap();
    writeln!(&mut md, "- `source_words` stays in the sparse index so current cards stay exact while the semantic rewrite grows.").unwrap();

    writeln!(&mut md).unwrap();
    writeln!(&mut md, "## Current Coverage").unwrap();
    writeln!(&mut md).unwrap();
    writeln!(&mut md, "| Opcode | Id | Frames | Words Used | Value Fields | Attr Fields | Slot Fields | What Changes | Example Cards |").unwrap();
    writeln!(
        &mut md,
        "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |"
    )
    .unwrap();

    for stat in stats.values() {
        let mut words_used = stat
            .words_used
            .iter()
            .cloned()
            .collect::<Vec<_>>()
            .join(", ");
        if words_used.is_empty() {
            words_used = "none".to_string();
        }
        let mut value_fields = stat
            .value_fields
            .iter()
            .cloned()
            .collect::<Vec<_>>()
            .join(", ");
        if value_fields.is_empty() {
            value_fields = "none".to_string();
        }
        let mut attr_fields = stat
            .attr_fields
            .iter()
            .cloned()
            .collect::<Vec<_>>()
            .join(", ");
        if attr_fields.is_empty() {
            attr_fields = "none".to_string();
        }
        let mut slot_fields = stat
            .slot_fields
            .iter()
            .cloned()
            .collect::<Vec<_>>()
            .join(", ");
        if slot_fields.is_empty() {
            slot_fields = "none".to_string();
        }

        let note = opcode_note(&stat.opcode, stat);
        let examples = if stat.cards.is_empty() {
            "".to_string()
        } else {
            stat.cards.join(" ; ")
        };
        writeln!(
            &mut md,
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} |",
            escape_md(&stat.opcode),
            stat.opcode_id,
            stat.frame_count,
            escape_md(&words_used),
            escape_md(&value_fields),
            escape_md(&attr_fields),
            escape_md(&slot_fields),
            escape_md(&note),
            escape_md(&examples),
        )
        .unwrap();
    }

    writeln!(&mut md).unwrap();
    writeln!(&mut md, "## Bit Packing Reference").unwrap();
    writeln!(&mut md).unwrap();
    writeln!(
        &mut md,
        "These tables are the exact packed-word definitions from `data/metadata.json`."
    )
    .unwrap();
    writeln!(&mut md).unwrap();
    if let Some(words) = layout.get("words") {
        render_layout_section(&mut md, "Word Layout", words);
    }
    if let Some(v) = layout.get("V") {
        render_layout_section(&mut md, "V Word Layout", v);
    }
    if let Some(a) = layout.get("A") {
        render_layout_section(&mut md, "A Word Layout", a);
    }
    if let Some(s) = layout.get("S") {
        render_layout_section(&mut md, "S Word Layout", s);
    }
    if let Some(overrides) = layout.get("overrides") {
        render_layout_section(&mut md, "Per-Opcode Layout Overrides", overrides);
    }

    writeln!(&mut md, "## Complete Metadata Families").unwrap();
    writeln!(&mut md).unwrap();
    writeln!(&mut md, "### Instruction Families").unwrap();
    writeln!(&mut md).unwrap();
    render_name_id_table(&mut md, "Opcodes", &opcode_entries, &stats, true);
    render_name_id_table(&mut md, "Conditions", &condition_entries, &stats, true);
    render_name_id_table(&mut md, "Costs", &cost_entries, &stats, true);
    render_name_id_table(&mut md, "Action Bases", &action_base_entries, &stats, true);

    writeln!(&mut md, "### Lookup Tables").unwrap();
    writeln!(&mut md).unwrap();
    render_name_id_table(&mut md, "Triggers", &trigger_entries, &stats, false);
    render_name_id_table(&mut md, "Targets", &target_entries, &stats, false);
    render_name_id_table(&mut md, "Slot Indices", &slot_entries, &stats, false);
    render_name_id_table(&mut md, "Comparisons", &comparison_entries, &stats, false);
    render_name_id_table(&mut md, "Zones", &zone_entries, &stats, false);

    writeln!(&mut md).unwrap();
    writeln!(&mut md, "## Opcode Details").unwrap();
    writeln!(&mut md).unwrap();

    for stat in stats.values() {
        writeln!(
            &mut md,
            "### {} (`{}`)",
            escape_md(&stat.opcode),
            stat.opcode_id
        )
        .unwrap();
        writeln!(&mut md).unwrap();
        writeln!(&mut md, "{}", opcode_note(&stat.opcode, stat)).unwrap();
        writeln!(&mut md).unwrap();
        writeln!(&mut md, "- Frames observed: {}", stat.frame_count).unwrap();
        writeln!(
            &mut md,
            "- Words used: {}",
            if stat.words_used.is_empty() {
                "none".to_string()
            } else {
                stat.words_used
                    .iter()
                    .cloned()
                    .collect::<Vec<_>>()
                    .join(", ")
            }
        )
        .unwrap();
        writeln!(
            &mut md,
            "- Value fields: {}",
            if stat.value_fields.is_empty() {
                "none".to_string()
            } else {
                stat.value_fields
                    .iter()
                    .cloned()
                    .collect::<Vec<_>>()
                    .join(", ")
            }
        )
        .unwrap();
        writeln!(
            &mut md,
            "- Attr fields: {}",
            if stat.attr_fields.is_empty() {
                "none".to_string()
            } else {
                stat.attr_fields
                    .iter()
                    .cloned()
                    .collect::<Vec<_>>()
                    .join(", ")
            }
        )
        .unwrap();
        writeln!(
            &mut md,
            "- Slot fields: {}",
            if stat.slot_fields.is_empty() {
                "none".to_string()
            } else {
                stat.slot_fields
                    .iter()
                    .cloned()
                    .collect::<Vec<_>>()
                    .join(", ")
            }
        )
        .unwrap();
        writeln!(
            &mut md,
            "- Example frames: {}",
            if stat.examples.is_empty() {
                "none".to_string()
            } else {
                stat.examples.join(" | ")
            }
        )
        .unwrap();
        writeln!(
            &mut md,
            "- Example cards: {}",
            if stat.cards.is_empty() {
                "none".to_string()
            } else {
                stat.cards.join(" | ")
            }
        )
        .unwrap();
        writeln!(&mut md).unwrap();
    }

    writeln!(&mut md, "## Field Glossary").unwrap();
    writeln!(&mut md).unwrap();
    writeln!(&mut md, "| Field | Meaning | Opcodes |").unwrap();
    writeln!(&mut md, "| --- | --- | --- |").unwrap();
    for (field, opcodes) in field_usage.iter() {
        let meaning = field_description(field);
        let opcode_list = opcodes.iter().cloned().collect::<Vec<_>>().join(", ");
        writeln!(
            &mut md,
            "| {} | {} | {} |",
            escape_md(field),
            escape_md(meaning),
            escape_md(&opcode_list)
        )
        .unwrap();
    }

    fs::write(&output_path, md)
        .unwrap_or_else(|err| panic!("failed to write {}: {err}", output_path.display()));
    println!("Wrote opcode guide to {}", output_path.display());
}
