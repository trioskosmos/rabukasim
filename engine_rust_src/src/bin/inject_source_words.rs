use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

fn bytecode_from_value(value: &Value) -> Vec<i32> {
    value
        .as_array()
        .map(|words| {
            words
                .iter()
                .filter_map(|w| w.as_i64().map(|v| v as i32))
                .collect::<Vec<_>>()
        })
        .unwrap_or_default()
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let compiled: Value = serde_json::from_str(&fs::read_to_string("../data/cards_compiled.json")?)?;
    let sparse_path = PathBuf::from("../data/ability_frame_index.json");
    let mut sparse: Value = serde_json::from_str(&fs::read_to_string(&sparse_path)?)?;

    let mut originals: HashMap<(String, usize), Vec<i32>> = HashMap::new();
    for db_name in ["member_db", "live_db"] {
        if let Some(cards) = compiled.get(db_name).and_then(|v| v.as_object()) {
            for card in cards.values() {
                let card_no = card.get("card_no").and_then(|v| v.as_str()).unwrap_or("").to_string();
                if let Some(abilities) = card.get("abilities").and_then(|v| v.as_array()) {
                    for (ability_index, ability) in abilities.iter().enumerate() {
                        let bytecode = bytecode_from_value(ability.get("bytecode").unwrap_or(&Value::Null));
                        if !bytecode.is_empty() {
                            originals.insert((card_no.clone(), ability_index), bytecode);
                        }
                    }
                }
            }
        }
    }

    let mut injected = 0usize;
    if let Some(abilities) = sparse.get_mut("abilities").and_then(|v| v.as_array_mut()) {
        for ability in abilities {
            let source_words = if let Some(cards) = ability.get("cards").and_then(|v| v.as_array()) {
                let mut found: Option<Vec<i32>> = None;
                for card in cards {
                    let card_no = card.get("card_no").and_then(|v| v.as_str()).unwrap_or("");
                    let ability_index = card.get("ability_index").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
                    if let Some(words) = originals.get(&(card_no.to_string(), ability_index)) {
                        found = Some(words.clone());
                        break;
                    }
                }
                found
            } else {
                None
            };

            if let Some(words) = source_words {
                if let Some(obj) = ability.as_object_mut() {
                    obj.insert(
                        "source_words".to_string(),
                        Value::Array(words.into_iter().map(|w| Value::from(w as i64)).collect()),
                    );
                    injected += 1;
                }
            }
        }
    }

    fs::write(&sparse_path, serde_json::to_string_pretty(&sparse)?)?;
    println!("injected source_words into {injected} abilities");
    Ok(())
}