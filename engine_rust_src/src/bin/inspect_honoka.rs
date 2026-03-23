use serde_json::Value;
use std::fs;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let compiled: Value =
        serde_json::from_str(&fs::read_to_string("../data/cards_compiled.json")?)?;
    let sparse: Value =
        serde_json::from_str(&fs::read_to_string("../data/ability_frame_index.json")?)?;

    let mut originals: Vec<(usize, Vec<i32>, String)> = Vec::new();
    for db_name in ["member_db", "live_db"] {
        if let Some(cards) = compiled.get(db_name).and_then(|v| v.as_object()) {
            for card in cards.values() {
                if card.get("card_id").and_then(|v| v.as_i64()) == Some(120) {
                    if let Some(abilities) = card.get("abilities").and_then(|v| v.as_array()) {
                        for (idx, ab) in abilities.iter().enumerate() {
                            originals.push((
                                idx,
                                ab.get("bytecode")
                                    .and_then(|v| v.as_array())
                                    .unwrap()
                                    .iter()
                                    .filter_map(|w| w.as_i64().map(|v| v as i32))
                                    .collect(),
                                ab.get("raw_text")
                                    .and_then(|v| v.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                            ));
                        }
                    }
                }
            }
        }
    }

    let mut sparse_entry: Option<&Value> = None;
    for ability in sparse.get("abilities").and_then(|v| v.as_array()).unwrap() {
        for card in ability.get("cards").and_then(|v| v.as_array()).unwrap() {
            if card.get("card_id").and_then(|v| v.as_str()) == Some("120")
                && card.get("ability_index").and_then(|v| v.as_i64()) == Some(0)
            {
                sparse_entry = Some(ability);
                break;
            }
        }
        if sparse_entry.is_some() {
            break;
        }
    }

    let sparse_entry = sparse_entry.expect("missing sparse Honoka entry");
    for (idx, bytes, text) in originals {
        println!("ability {}: {:?}", idx, bytes);
        println!("{}", text);
    }
    println!("sparse:   {:?}", sparse_entry);
    Ok(())
}
