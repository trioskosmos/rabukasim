//! Debug Game Log - Shows exactly what actions are being taken

use std::time::Instant;
use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};

fn load_db() -> CardDatabase {
    let candidates = [
        "data/cards_compiled.json",
        "../data/cards_compiled.json",
        "../../data/cards_compiled.json",
    ];

    for path in &candidates {
        if !std::path::Path::new(path).exists() {
            continue;
        }
        let json = std::fs::read_to_string(path).expect("Failed to read DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
        db.is_vanilla = false;
        return db;
    }
    panic!("cards_compiled.json not found");
}

fn load_deck(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let content = std::fs::read_to_string(path).expect("Failed to read deck");
    let mut members = Vec::new();
    let mut lives = Vec::new();

    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.is_empty() {
            continue;
        }

        let card_no = parts[0];
        let count: usize = if parts.len() >= 3 && parts[1] == "x" {
            parts[2].parse().unwrap_or(1)
        } else {
            1
        };

        if let Some(id) = db.id_by_no(card_no) {
            for _ in 0..count {
                if db.lives.contains_key(&id) {
                    lives.push(id);
                } else {
                    members.push(id);
                }
            }
        }
    }

    while members.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            members.push(id);
        } else {
            break;
        }
    }
    while lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            lives.push(id);
        } else {
            break;
        }
    }

    members.truncate(48);
    lives.truncate(12);

    (members, lives)
}

fn resolve_deck_path(spec: &str) -> String {
    let direct = std::path::Path::new(spec);
    if direct.exists() {
        return spec.to_string();
    }

    for base in [std::path::Path::new("ai/decks"), std::path::Path::new("../ai/decks")] {
        let candidate = base.join(format!("{}.txt", spec));
        if candidate.exists() {
            return candidate.to_string_lossy().into_owned();
        }
    }

    spec.to_string()
}

fn format_action(action: i32) -> String {
    if action == ACTION_BASE_PASS {
        return "PASS".to_string();
    }
    if (400..=459).contains(&action) {
        return format!("LIVESET(hand={})", action - 400);
    }
    if (1..=180).contains(&action) {
        let hand_idx = (action - 1) / 3;
        let slot_idx = (action - 1) % 3;
        let areas = ["Left", "Center", "Right"];
        return format!("PLAY(hand={}, area={})", hand_idx, areas[slot_idx as usize]);
    }
    format!("ACTION({})", action)
}

fn log_game_state(state: &GameState, db: &CardDatabase, step: usize) {
    println!("\n=== STEP {} ===", step);
    println!("Phase: {:?}", state.phase);
    println!("Current Player: {}", state.current_player);
    println!("Turn: {}", state.turn);
    
    for p in 0..2 {
        let hand = &state.core.players[p].hand;
        let live_zone = &state.core.players[p].live_zone;
        let stage = &state.core.players[p].stage;
        
        // Count card types
        let live_in_hand = hand.iter().filter(|&&cid| db.get_live(cid).is_some()).count();
        let member_in_hand = hand.iter().filter(|&&cid| db.get_member(cid).is_some()).count();
        
        println!("P{} Hand: {} cards ({} live, {} member) {:?}", 
            p, hand.len(), live_in_hand, member_in_hand, hand);
        println!("P{} Live: {:?}", p, live_zone);
        println!("P{} Stage: {:?}", p, stage);
    }
}

fn run_debug_game(state: &mut GameState, db: &CardDatabase, max_steps: usize) {
    let mut step_count = 0;
    
    println!("=== DEBUG GAME START ===");
    log_game_state(state, db, 0);
    
    while !state.is_terminal() && step_count < max_steps {
        step_count += 1;
        
        let phase_before = state.phase;
        let player_before = state.current_player;
        
        // Get legal actions
        let legal = state.get_legal_action_ids(db);
        println!("\n--- LEGAL ACTIONS ({} available) ---", legal.len());
        for (i, &action) in legal.iter().enumerate() {
            println!("  {}: {}", i, format_action(action));
        }
        
        // Choose first legal action (deterministic for debugging)
        let chosen_action = if legal.is_empty() {
            ACTION_BASE_PASS
        } else {
            legal[0] // Always pick first for consistency
        };
        
        println!("CHOSEN: {}", format_action(chosen_action));
        
        // Execute action
        let t = Instant::now();
        let result = state.step(db, chosen_action);
        let elapsed = t.elapsed().as_micros();
        
        println!("RESULT: {:?} (took {}μs)", result, elapsed);
        
        // Show what changed
        if phase_before != state.phase {
            println!("PHASE CHANGE: {:?} -> {:?}", phase_before, state.phase);
        }
        if player_before != state.current_player {
            println!("PLAYER CHANGE: {} -> {}", player_before, state.current_player);
        }
        
        // Log state after key phases
        if matches!(phase_before, Phase::LiveSet) || matches!(phase_before, Phase::Main) {
            log_game_state(state, db, step_count);
        }
        
        // Break if we get stuck
        if elapsed > 1000 {
            println!("SLOW OPERATION DETECTED: {}μs - breaking", elapsed);
            break;
        }
    }
    
    println!("\n=== GAME END ===");
    println!("Final Phase: {:?}", state.phase);
    println!("Total Steps: {}", step_count);
    log_game_state(state, db, step_count);
}

fn main() {
    println!("=== DEBUG GAME LOG ===\n");
    
    let db = load_db();
    let deck_path = resolve_deck_path("muse_cup");
    let p0_deck = load_deck(&deck_path, &db);
    let p1_deck = load_deck(&deck_path, &db);
    
    println!("Loaded deck: {}", deck_path);
    println!("P0: {} members + {} lives", p0_deck.0.len(), p0_deck.1.len());
    println!("P1: {} members + {} lives", p1_deck.0.len(), p1_deck.1.len());
    
    // Debug: Show some card IDs
    if !p0_deck.0.is_empty() {
        println!("P0 member samples: {:?}", &p0_deck.0[..5.min(p0_deck.0.len())]);
    }
    if !p0_deck.1.is_empty() {
        println!("P0 live samples: {:?}", &p0_deck.1[..5.min(p0_deck.1.len())]);
    }
    
    // Run 3 debug games
    for game_id in 0..3 {
        println!("\n{}", "=".repeat(60));
        println!("GAME {}", game_id + 1);
        println!("{}", "=".repeat(60));
        
        let mut state = GameState::default();
        let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

        state.initialize_game(
            p0_deck.0.clone(),
            p1_deck.0.clone(),
            energy.clone(),
            energy.clone(),
            p0_deck.1.clone(),
            p1_deck.1.clone(),
        );
        
        state.ui.silent = true;
        
        run_debug_game(&mut state, &db, 20); // Max 20 steps
    }
}
