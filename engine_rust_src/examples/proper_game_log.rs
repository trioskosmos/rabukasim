use engine_rust::core::logic::game::GameState;
use engine_rust::core::logic::card_db::CardDatabase;
use engine_rust::core::enums::Phase;

fn load_db() -> CardDatabase {
    let db_path = "../data/cards_compiled.json";
    let json_content = std::fs::read_to_string(db_path).expect("Failed to read database file");
    CardDatabase::from_json(&json_content).expect("Failed to parse database")
}

fn create_proper_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>, Vec<i32>, Vec<i32>, Vec<i32>) {
    // Get real member cards (1000-3999 range)
    let mut member_cards: Vec<i32> = db.all_member_ids().iter().cloned().collect();
    // Get real live cards (4000-4999 range) 
    let mut live_cards: Vec<i32> = db.all_live_ids().iter().cloned().collect();
    // Get real energy cards (5000-5999 range)
    let mut energy_cards: Vec<i32> = db.all_energy_ids().iter().cloned().collect();
    
    // Take exactly 48 member cards and 12 live cards for each player
    member_cards.sort();
    live_cards.sort();
    energy_cards.sort();
    
    let p0_members: Vec<i32> = member_cards.iter().take(48).cloned().collect();
    let p1_members: Vec<i32> = member_cards.iter().skip(48).take(48).cloned().collect();
    
    let p0_lives: Vec<i32> = live_cards.iter().take(12).cloned().collect();
    let p1_lives: Vec<i32> = live_cards.iter().skip(12).take(12).cloned().collect();
    
    let p0_energy: Vec<i32> = energy_cards.iter().take(20).cloned().collect();
    let p1_energy: Vec<i32> = energy_cards.iter().skip(20).take(20).cloned().collect();
    
    println!("Deck sizes:");
    println!("P0: {} members + {} lives = {} total", p0_members.len(), p0_lives.len(), p0_members.len() + p0_lives.len());
    println!("P1: {} members + {} lives = {} total", p1_members.len(), p1_lives.len(), p1_members.len() + p1_lives.len());
    println!("P0 energy: {} cards", p0_energy.len());
    println!("P1 energy: {} cards", p1_energy.len());
    
    (p0_members, p1_members, p0_energy, p1_energy, p0_lives, p1_lives)
}

fn main() {
    println!("=== PROPER GAME SETUP LOG ===\n");
    
    let db = load_db();
    let (p0_members, p1_members, p0_energy, p1_energy, p0_lives, p1_lives) = create_proper_decks(&db);
    
    let mut state = GameState::default();
    
    // Proper game initialization
    state.initialize_game(p0_members, p1_members, p0_energy, p1_energy, p0_lives, p1_lives);
    
    println!("\n=== AFTER INITIALIZATION ===");
    println!("Phase: {:?}", state.phase);
    println!("Current Player: {}", state.current_player);
    println!("Turn: {}", state.turn);
    
    println!("\n=== DECKS ===");
    println!("P0 Deck: {} cards", state.core.players[0].deck.len());
    println!("P1 Deck: {} cards", state.core.players[1].deck.len());
    println!("P0 Energy Deck: {} cards", state.core.players[0].energy_deck.len());
    println!("P1 Energy Deck: {} cards", state.core.players[1].energy_deck.len());
    
    println!("\n=== INITIAL HANDS ===");
    println!("P0 Hand: {:?}", state.core.players[0].hand);
    println!("P1 Hand: {:?}", state.core.players[1].hand);
    
    println!("\n=== ENERGY ZONES ===");
    println!("P0 Energy: {:?}", state.core.players[0].energy_zone);
    println!("P1 Energy: {:?}", state.core.players[1].energy_zone);
    
    println!("\n=== LIVE ZONES ===");
    println!("P0 Live: {:?}", state.core.players[0].live_zone);
    println!("P1 Live: {:?}", state.core.players[1].live_zone);
    
    // Count card types in hands
    let p0_live_in_hand = state.core.players[0].hand.iter().filter(|&&cid| cid >= 4000 && cid < 5000).count();
    let p1_live_in_hand = state.core.players[0].hand.iter().filter(|&&cid| cid >= 4000 && cid < 5000).count();
    let p0_member_in_hand = state.core.players[0].hand.iter().filter(|&&cid| cid >= 1000 && cid < 4000).count();
    let p1_member_in_hand = state.core.players[0].hand.iter().filter(|&&cid| cid >= 1000 && cid < 4000).count();
    
    println!("\n=== CARD TYPE ANALYSIS ===");
    println!("P0 Hand: {} live cards, {} member cards", p0_live_in_hand, p0_member_in_hand);
    println!("P1 Hand: {} live cards, {} member cards", p1_live_in_hand, p1_member_in_hand);
    
    // Skip to LiveSet phase for testing
    println!("\n=== SKIPPING TO LIVESET ===");
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    
    println!("Phase: {:?}", state.phase);
    println!("Current Player: {}", state.current_player);
    
    // Test legal actions in LiveSet
    let legal_actions = state.get_legal_actions(&db);
    let legal_count = legal_actions.iter().filter(|&&x| x).count();
    println!("Legal actions in LiveSet: {}", legal_count);
    
    let mut legal_list = Vec::new();
    for (i, &is_legal) in legal_actions.iter().enumerate().take(50) {
        if is_legal {
            legal_list.push(i);
        }
    }
    println!("Legal action indices (first 50): {:?}", legal_list);
    
    // Try playing a live card if available
    if legal_list.len() > 1 {
        let first_action = legal_list[1]; // Skip pass (0)
        println!("Trying action: {}", first_action);
        
        let result = state.step(&db, first_action as i32);
        println!("Result: {:?}", result);
        
        println!("After action:");
        println!("P0 Hand: {:?}", state.core.players[0].hand);
        println!("P0 Live: {:?}", state.core.players[0].live_zone);
    } else {
        println!("No actions available except pass");
    }
}
