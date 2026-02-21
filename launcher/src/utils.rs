
use crate::models::ParsedDecks;
use tiny_http::Request;
use engine_rust::core::logic::CardDatabase;

pub fn resolve_deck(main_codes: &[String], energy_codes: &[String], db: &CardDatabase) -> ParsedDecks {
    let mut members = Vec::new();
    let mut lives = Vec::new();

    for code in main_codes {
        let trimmed_code = code.trim().to_uppercase();
        if trimmed_code.is_empty() { continue; }
        
        if let Some(id) = db.members.iter().find(|(_, m)| m.card_no.trim().to_uppercase() == trimmed_code).map(|(id, _)| *id) {
            members.push(id);
        } else if let Some(id) = db.lives.iter().find(|(_, l)| l.card_no.trim().to_uppercase() == trimmed_code).map(|(id, _)| *id) {
            lives.push(id);
        } else {
            println!("[Deck] WARNING: Failed to resolve card code: '{}'", trimmed_code);
        }
    }

    let mut energy = Vec::new();
    for code in energy_codes {
        if let Some(id) = db.energy_db.iter().find(|(_, v)| v.card_no == *code).map(|(id, _)| *id) {
            energy.push(id);
        }
    }
    
    // Ensure exactly 12 energy cards
    if energy.len() < 12 {
        let fallback_id = if !energy.is_empty() {
            energy[0]
        } else if let Some(id) = db.energy_db.keys().next() {
            *id
        } else {
            40000
        };
        
        println!("[Deck] Energy deck too small ({} cards). Filling with ID: {} to reach 12.", energy.len(), fallback_id);
        while energy.len() < 12 {
            energy.push(fallback_id);
        }
    } else if energy.len() > 12 {
        println!("[Deck] Energy deck too large ({} cards). Truncating to 12.", energy.len());
        energy.truncate(12);
    } else {
        println!("[Deck] Resolved exactly 12 energy cards.");
    }

    ParsedDecks { members, lives, energy }
}

pub fn get_local_ip() -> Result<String, ()> {
    use std::net::UdpSocket;
    let socket = UdpSocket::bind("0.0.0.0:0").map_err(|_| ())?;
    socket.connect("8.8.8.8:80").map_err(|_| ())?;
    socket.local_addr().map(|addr| addr.ip().to_string()).map_err(|_| ())
}

pub fn parse_body<T: serde::de::DeserializeOwned>(request: &mut Request) -> Result<T, String> {
    let mut content = String::new();
    request.as_reader().read_to_string(&mut content).map_err(|e| e.to_string())?;
    serde_json::from_str(&content).map_err(|e| format!("Serde Error: {} | Body: {}", e, content))
}

pub fn get_header(request: &tiny_http::Request, name: &str) -> Option<String> {
    request.headers().iter()
        .find(|h| h.field.as_str().as_str().eq_ignore_ascii_case(name))
        .map(|h| h.value.as_str().trim().to_string())
}

pub fn generate_room_code() -> String {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let code: u32 = rng.gen_range(1000..9999);
    code.to_string()
}

pub fn parse_deck_content(content: &str, db: &CardDatabase) -> ParsedDecks {
    let codes: Vec<String> = content.split(|c: char| c == ',' || c == '\n' || c == '\r')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();
    resolve_deck(&codes, &[], db)
}

pub fn load_named_deck(name: &str) -> Option<(Vec<String>, Vec<String>)> {
    use crate::Decks;
    let path = format!("{}.txt", name);
    if let Some(file) = Decks::get(&path) {
        let content = std::str::from_utf8(file.data.as_ref()).ok()?;
        let mut main = Vec::new();
        let mut energy = Vec::new();
        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') { continue; }
            
            let current_code;
            let mut current_count = 1;

            // Handle "CardCode x N" or "N x CardCode" or just "CardCode"
            // Using regex or more robust splitting
            let line_lower = line.to_lowercase();
            if let Some(idx) = line_lower.find(" x ") {
                let part1 = line[..idx].trim();
                let part2 = line[idx+3..].trim();
                
                if let Ok(count) = part1.parse::<usize>() {
                    // N x CardCode
                    current_count = count;
                    current_code = part2.to_string();
                } else if let Ok(count) = part2.parse::<usize>() {
                    // CardCode x N
                    current_count = count;
                    current_code = part1.to_string();
                } else {
                    // Fallback
                    current_code = line.to_string();
                }
            } else {
                current_code = line.to_string();
            }

            if current_code.is_empty() { continue; }

            if current_code.ends_with("-PE") || current_code.ends_with("-PE＋") {
                for _ in 0..current_count {
                    energy.push(current_code.clone());
                }
            } else {
                for _ in 0..current_count {
                    main.push(current_code.clone());
                }
            }
        }
        return Some((main, energy));
    }
    None
}

pub fn get_random_valid_deck(db: &CardDatabase) -> ParsedDecks {
    use rand::seq::SliceRandom;
    let mut rng = rand::thread_rng();

    // 1. Members: 48 cards (12 distinct types x 4 copies)
    let mut m_ids: Vec<i32> = db.members.keys().cloned().collect();
    if m_ids.is_empty() { m_ids.push(1); } // Safety fallback
    m_ids.shuffle(&mut rng);

    let needed_types = 12;
    let type_pool: Vec<i32> = m_ids.iter().cycle().take(needed_types).cloned().collect();

    let mut members = Vec::new();
    for &mid in &type_pool {
        members.extend(std::iter::repeat(mid).take(4));
    }
    members.shuffle(&mut rng); // Shuffle the final list

    // 2. Lives: 12 cards (3 distinct types x 4 copies)
    let mut l_ids: Vec<i32> = db.lives.keys().cloned().collect();
    if l_ids.is_empty() { l_ids.push(10001); }
    l_ids.shuffle(&mut rng);

    let needed_lives = 3;
    let live_pool: Vec<i32> = l_ids.iter().cycle().take(needed_lives).cloned().collect();

    let mut lives = Vec::new();
    for &lid in &live_pool {
        lives.extend(std::iter::repeat(lid).take(4));
    }
    lives.shuffle(&mut rng);

    // 3. Energy: 12 cards
    let def_e = if let Some(id) = db.energy_db.keys().next() {
        *id
    } else { 40000 };
    let energy = vec![def_e; 12];

    ParsedDecks { members, lives, energy }
}
