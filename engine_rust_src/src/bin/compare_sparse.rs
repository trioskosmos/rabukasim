use engine_rust::core::logic::CardDatabase;
use serde_json::Value;
use std::collections::HashMap;
use std::fs;

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
    let sparse: Value = serde_json::from_str(&fs::read_to_string("../data/ability_frame_index.json")?)?;

    let mut sparse_map: HashMap<(String, usize), &Value> = HashMap::new();
    if let Some(abilities) = sparse.get("abilities").and_then(|v| v.as_array()) {
        for entry in abilities {
            if let Some(cards) = entry.get("cards").and_then(|v| v.as_array()) {
                for card in cards {
                    let card_no = card.get("card_no").and_then(|v| v.as_str()).unwrap_or("").to_string();
                    let ability_index = card.get("ability_index").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
                    sparse_map.insert((card_no, ability_index), entry);
                }
            }
        }
    }

    let mut checked = 0usize;
    let mut mismatches = Vec::new();

    for db_name in ["member_db", "live_db"] {
        if let Some(cards) = compiled.get(db_name).and_then(|v| v.as_object()) {
            for card in cards.values() {
                let card_no = card.get("card_no").and_then(|v| v.as_str()).unwrap_or("");
                if let Some(abilities) = card.get("abilities").and_then(|v| v.as_array()) {
                    for (ability_index, ability) in abilities.iter().enumerate() {
                        let original = bytecode_from_value(ability.get("bytecode").unwrap_or(&Value::Null));
                        if original.is_empty() {
                            continue;
                        }
                        checked += 1;
                        let Some(entry) = sparse_map.get(&(card_no.to_string(), ability_index)) else {
                            mismatches.push((card_no.to_string(), ability_index, original, Vec::new()));
                            continue;
                        };
                        let rebuilt = CardDatabase::sparse_entry_to_bytecode(entry);
                        if original != rebuilt {
                            mismatches.push((card_no.to_string(), ability_index, original, rebuilt));
                        }
                    }
                }
            }
        }
    }

    println!("checked={checked}");
    println!("mismatches={}", mismatches.len());
    for (card_no, ability_index, original, rebuilt) in mismatches.into_iter().take(20) {
        println!("--- {card_no}#{ability_index}");
        println!("orig:    {:?}", original);
        println!("rebuilt: {:?}", rebuilt);
        if original.len() == rebuilt.len() {
            for (i, (a, b)) in original.iter().zip(rebuilt.iter()).enumerate() {
                if a != b {
                    println!("first_diff_index={i} orig={a} rebuilt={b}");
                    break;
                }
            }
        } else {
            println!("len_diff orig={} rebuilt={}", original.len(), rebuilt.len());
        }
    }

    Ok(())
}
