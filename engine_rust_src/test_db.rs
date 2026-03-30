use std::fs;

fn main() {
    let json = fs::read_to_string("../data/cards_compiled.json").unwrap();
    println!("JSON length: {}", json.len());
    println!("First 100 chars: {}", &json[..100]);
    
    // Try to parse as serde_json::Value
    match serde_json::from_str::<serde_json::Value>(&json) {
        Ok(v) => {
            println!("JSON is valid");
            if let Some(member_db) = v.get("member_db") {
                println!("member_db exists with {} members", member_db.as_object().unwrap().len());
            }
            if let Some(live_db) = v.get("live_db") {
                println!("live_db exists with {} lives", live_db.as_object().unwrap().len());
            }
        }
        Err(e) => {
            println!("JSON parsing failed: {}", e);
        }
    }
}
