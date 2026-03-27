use engine_rust::core::logic::ability_manifest::AbilityManifest;
use serde_json::{Map, Value};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("engine_rust_src must have a parent repo root")
        .to_path_buf()
}

fn read_json(path: &Path) -> Value {
    let text =
        fs::read_to_string(path).unwrap_or_else(|err| panic!("failed to read {}: {err}", path.display()));
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

fn normalize_group_key(text: &str) -> String {
    text.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn build_grouped_ability_input(manifest: &AbilityManifest) -> Value {
    let mut groups: BTreeMap<String, Map<String, Value>> = BTreeMap::new();

    for card in &manifest.cards {
        for ability in &card.abilities {
            let source_text = if !ability.source_text.trim().is_empty() {
                ability.source_text.as_str()
            } else if !ability.source_text_en.trim().is_empty() {
                ability.source_text_en.as_str()
            } else {
                ability.summary.as_str()
            };
            let key = normalize_group_key(source_text);

            let entry = groups.entry(key.clone()).or_insert_with(|| {
                let mut map = Map::new();
                map.insert("source_text".to_string(), Value::String(key.clone()));
                map.insert("cards".to_string(), Value::Array(Vec::new()));
                map.insert("card_refs".to_string(), Value::Array(Vec::new()));
                map.insert("pseudocode".to_string(), Value::String(String::new()));
                map.insert("summary".to_string(), Value::String(String::new()));
                map.insert("ability_count".to_string(), Value::from(0));
                map
            });

            if let Some(cards) = entry.get_mut("cards").and_then(Value::as_array_mut) {
                if !cards.iter().any(|existing| existing.as_str() == Some(card.card_no.as_str())) {
                    cards.push(Value::String(card.card_no.clone()));
                }
            }

            if let Some(card_refs) = entry.get_mut("card_refs").and_then(Value::as_array_mut) {
                card_refs.push(serde_json::json!({
                    "card_no": card.card_no,
                    "card_id": card.card_id,
                    "name": card.name,
                    "ability_index": ability.ability_index,
                    "trigger": ability.trigger,
                    "trigger_id": ability.trigger_id,
                }));
            }

            if entry
                .get("pseudocode")
                .and_then(Value::as_str)
                .map(|text| text.is_empty())
                .unwrap_or(true)
            {
                entry.insert("pseudocode".to_string(), Value::String(ability.summary.clone()));
                entry.insert("summary".to_string(), Value::String(ability.summary.clone()));
                entry.insert("trigger".to_string(), Value::String(ability.trigger.clone()));
                entry.insert("trigger_id".to_string(), Value::from(ability.trigger_id));
                entry.insert(
                    "opcode_sequence".to_string(),
                    Value::Array(
                        ability
                            .opcode_sequence
                            .iter()
                            .cloned()
                            .map(Value::String)
                            .collect(),
                    ),
                );
                entry.insert(
                    "frames".to_string(),
                    serde_json::to_value(&ability.frames).expect("serialize frames"),
                );
                entry.insert(
                    "source_text_en".to_string(),
                    Value::String(ability.source_text_en.clone()),
                );
            }

            let count = entry
                .get("ability_count")
                .and_then(Value::as_i64)
                .unwrap_or(0)
                + 1;
            entry.insert("ability_count".to_string(), Value::from(count));
        }
    }

    let mut out = Map::new();
    out.insert(
        "_metadata".to_string(),
        serde_json::json!({
            "generated_by": "generate_ability_manifest",
            "generated_at": SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs()
                .to_string(),
            "schema": "consolidated_abilities.semantic.v1",
        }),
    );

    for (key, entry) in groups {
        out.insert(key, Value::Object(entry));
    }

    Value::Object(out)
}

fn main() {
    let root = repo_root();
    let cards_path = root.join("data").join("cards_compiled.json");
    let metadata_path = root.join("data").join("metadata.json");
    let manifest_out = root.join("reports").join("ability_manifest.json");
    let manifest_md_out = root.join("reports").join("ability_manifest.md");
    let consolidated_out = root.join("data").join("consolidated_abilities.json");

    let cards_payload = read_json(&cards_path);
    let metadata = read_json(&metadata_path);

    let manifest = AbilityManifest::build(
        &cards_payload,
        &metadata,
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
            .to_string(),
        cards_path.display().to_string(),
        metadata_path.display().to_string(),
    );

    write_json(
        &manifest_out,
        &serde_json::to_value(&manifest).expect("serialize manifest"),
    );
    let grouped = build_grouped_ability_input(&manifest);
    write_json(&consolidated_out, &grouped);
    fs::write(&manifest_md_out, manifest.render_markdown())
        .unwrap_or_else(|err| panic!("failed to write {}: {err}", manifest_md_out.display()));

    println!("Wrote {}", manifest_out.display());
    println!("Wrote {}", consolidated_out.display());
    println!("Wrote {}", manifest_md_out.display());
}
