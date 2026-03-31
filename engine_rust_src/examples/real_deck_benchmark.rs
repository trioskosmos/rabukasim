use std::fs;
use engine_rust::core::logic::game::GameState;
use engine_rust::core::logic::card_db::CardDatabase;
use engine_rust::core::enums::Phase;

fn load_db() -> CardDatabase {
    let db_path = "../data/cards_compiled.json";
    let json_content = fs::read_to_string(db_path).expect("Failed to read database file");
    CardDatabase::from_json(&json_content).expect("Failed to parse database")
}

fn parse_deck_line(line: &str, db: &CardDatabase) -> Vec<i32> {
    let line = line.trim();
    if line.is_empty() || line.starts_with('#') {
        return Vec::new();
    }
    
    // Parse format: "PL!-bp3-026-L x 3"
    let parts: Vec<&str> = line.split(" x ").collect();
    if parts.len() != 2 {
        return Vec::new();
    }
    
    let card_code = parts[0];
    let quantity: usize = parts[1].parse().unwrap_or(1);
    
    // For now, create dummy IDs since we can't look up by code
    // In a real implementation, you'd need to implement code lookup
    println!("Warning: Card code '{}' lookup not implemented, using dummy ID", card_code);
    vec![(1000 + line.len() as i32); quantity]
}

fn load_deck_from_file(deck_path: &str, db: &CardDatabase) -> Vec<i32> {
    let content = fs::read_to_string(deck_path).expect("Failed to read deck file");
    let mut deck_cards = Vec::new();
    
    for line in content.lines() {
        let cards = parse_deck_line(line, db);
        deck_cards.extend(cards);
    }
    
    deck_cards
}

fn create_energy_deck() -> Vec<i32> {
    // Create 20 energy cards with IDs 5000-5019
    (5000..5020).collect()
}

fn create_member_deck() -> Vec<i32> {
    // Create 48 member cards with IDs 1000-1047
    (1000..1048).collect()
}

fn create_live_deck() -> Vec<i32> {
    // Create 12 live cards with IDs 4000-4011
    (4000..4012).collect()
}

fn main() {
    println!("=== REAL DECK BENCHMARK ===\n");
    
    let db = load_db();
    
    // Load deck structure from AI/DECKS
    let deck_path = "../ai/decks/muse_cup.txt";
    println!("Loading deck structure from: {}", deck_path);
    
    let _deck_structure = load_deck_from_file(deck_path, &db);
    println!("Loaded deck structure with {} entries", _deck_structure.len());
    
    // Create proper deck composition
    let members = create_member_deck();
    let lives = create_live_deck();
    let energy_deck = create_energy_deck();
    
    println!("Created proper deck composition:");
    println!("Main deck: {} members + {} lives = {} total", members.len(), lives.len(), members.len() + lives.len());
    println!("Energy deck: {} cards", energy_deck.len());
    
    // Create second deck (copy for simplicity)
    let members2 = members.clone();
    let lives2 = lives.clone();
    let energy_deck2 = energy_deck.clone();
    
    println!("\n=== INITIALIZING GAME ===");
    
    let mut state = GameState::default();
    state.initialize_game(members, members2, energy_deck, energy_deck2, lives, lives2);
    
    println!("After initialization:");
    println!("Phase: {:?}", state.phase);
    println!("Current Player: {}", state.current_player);
    println!("Turn: {}", state.turn);
    
    println!("\n=== INITIAL HANDS ===");
    println!("P0 Hand: {:?} ({} cards)", state.core.players[0].hand, state.core.players[0].hand.len());
    println!("P1 Hand: {:?} ({} cards)", state.core.players[1].hand, state.core.players[1].hand.len());
    
    // Count card types in hands
    let p0_lives = state.core.players[0].hand.iter().filter(|&&cid| cid >= 4000 && cid < 5000).count();
    let p1_lives = state.core.players[1].hand.iter().filter(|&&cid| cid >= 4000 && cid < 5000).count();
    let p0_members = state.core.players[0].hand.iter().filter(|&&cid| cid >= 1000 && cid < 4000).count();
    let p1_members = state.core.players[1].hand.iter().filter(|&&cid| cid >= 1000 && cid < 4000).count();
    
    println!("P0 Hand: {} live cards, {} member cards", p0_lives, p0_members);
    println!("P1 Hand: {} live cards, {} member cards", p1_lives, p1_members);
    
    println!("\n=== SKIPPING TO LIVESET ===");
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    
    // Test legal actions
    let legal_actions = state.get_legal_actions(&db);
    let legal_count = legal_actions.iter().filter(|&&x| x).count();
    println!("Legal actions in LiveSet: {}", legal_count);
    
    // Show first few legal actions
    let mut legal_list = Vec::new();
    for (i, &is_legal) in legal_actions.iter().enumerate().take(50) {
        if is_legal {
            legal_list.push(i);
        }
    }
    println!("Legal action indices: {:?}", legal_list);
    
    // Try to play a live card if available
    if legal_list.len() > 1 {
        // Find a live card in hand
        let p0_hand = &state.core.players[0].hand;
        for (hand_idx, &card_id) in p0_hand.iter().enumerate() {
            if card_id >= 4000 && card_id < 5000 {
                let action = 1000 + hand_idx as i32; // ACTION_BASE_LIVESET + hand_idx
                println!("Playing live card {} from hand position {}", card_id, hand_idx);
                
                let result = state.step(&db, action);
                println!("Result: {:?}", result);
                
                println!("After playing:");
                println!("P0 Hand: {:?} ({} cards)", state.core.players[0].hand, state.core.players[0].hand.len());
                println!("P0 Live: {:?}", state.core.players[0].live_zone);
                break;
            }
        }
    } else {
        println!("No legal actions available except pass");
    }
}
