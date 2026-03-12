/// diagnostic_init.rs — Game Initialization Diagnostic
///
/// Run with: cargo run --bin diagnostic_init [--release]
///
/// Purpose: Diagnose why games are failing to initialize properly

use std::fs;
use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{GameState, CardDatabase};
use rand::seq::IndexedRandom;

fn load_vanilla_db() -> CardDatabase {
    let candidates = [
        "data/cards_vanilla.json",
        "../data/cards_vanilla.json",
        "../../data/cards_vanilla.json",
    ];

    for path in &candidates {
        if !std::path::Path::new(path).exists() {
            continue;
        }
        let abs = std::fs::canonicalize(path)
            .unwrap_or_else(|_| std::path::PathBuf::from(path));
        println!("[DB_LOAD] Loading from: {:?}", abs);
        let json = fs::read_to_string(path).expect("Failed to read vanilla DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse vanilla DB");
        db.is_vanilla = true;
        return db;
    }
    panic!("Could not find cards_vanilla.json");
}

fn main() {
    println!("Game Initialization Diagnostic\n");

    let db = load_vanilla_db();

    println!("DB loaded: {} members, {} lives, {} energy",
        db.members.len(), db.lives.len(), db.energy_db.len());

    // Get sample cards
    let members: Vec<i32> = db.members.keys().take(48).cloned().collect();
    let lives: Vec<i32> = db.lives.keys().take(12).cloned().collect();
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    if members.is_empty() || lives.is_empty() || energy.is_empty() {
        eprintln!("ERROR: Not enough cards loaded!");
        eprintln!("  Members: {}", members.len());
        eprintln!("  Lives: {}", lives.len());
        eprintln!("  Energy: {}", energy.len());
        return;
    }

    println!("\n✓ Sample decks created");
    println!("  Members: {}", members.len());
    println!("  Lives: {}", lives.len());
    println!("  Energy: {}", energy.len());

    // Initialize the game
    let mut state = GameState::default();

    println!("\nBefore initialize_game:");
    println!("  Phase: {:?}", state.phase);
    println!("  Current Player: {}", state.current_player);
    println!("  Turn: {}", state.turn);
    println!("  Terminal: {}", state.is_terminal());

    state.initialize_game(
        members.clone(),
        members.clone(),
        energy.clone(),
        energy.clone(),
        lives.clone(),
        lives.clone(),
    );

    println!("\nAfter initialize_game:");
    println!("  Phase: {:?}", state.phase);
    println!("  Current Player: {}", state.current_player);
    println!("  Turn: {}", state.turn);
    println!("  Terminal: {}", state.is_terminal());
    println!("  P0 Hand: {}", state.players[0].hand.len());
    println!("  P1 Hand: {}", state.players[1].hand.len());
    println!("  P0 Deck: {}", state.players[0].deck.len());
    println!("  P1 Deck: {}", state.players[1].deck.len());
    println!("  P0 Energy: {}", state.players[0].energy_zone.len());
    println!("  P1 Energy: {}", state.players[1].energy_zone.len());

    if state.is_terminal() {
        println!("\n⚠️  Game is immediately terminal after initialize_game!");
        println!("  Winner: P{}", state.get_winner());
        return;
    }

    // Try advancing to Main phase with proper handling
    state.ui.silent = true;
    println!("\nAdvancing to Main phase:");

    let mut count = 0;
    const MAX_STEPS: usize = 100;
    let mut rng = rand::rng();

    while !state.is_terminal() && state.phase != Phase::Main && count < MAX_STEPS {
        let phase_str = format!("{:?}", state.phase);

        // Handle non-auto phases that require player actions
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                // Get legal actions and pick one randomly
                let legal = state.get_legal_action_ids(&db);
                if !legal.is_empty() {
                    if let Some(&action) = legal.choose(&mut rng) {
                        if let Err(e) = state.step(&db, action as i32) {
                            println!("  Step {}: Phase = {:?} → step() error: {:?}", count, state.phase, e);
                        }
                    }
                } else {
                    println!("  Step {}: Phase = {:?} → no legal actions!", count, phase_str);
                    break;
                }
            }
            _ => {
                // Auto-step for other phases
                state.auto_step(&db);
            }
        }

        count += 1;

        if count <= 10 || count % 5 == 0 {
            println!("  Step {}: Phase = {:?}", count, state.phase);
        }
    }

    if count >= MAX_STEPS {
        println!("⚠️  Reached MAX_STEPS limit!");
    } else if state.is_terminal() {
        println!("⚠️  Game became terminal!");
        println!("  Final Phase: {:?}", state.phase);
    } else {
        println!("✓ Reached Main phase after {} steps", count);
        println!("  Phase: {:?}", state.phase);
        println!("  Legal actions: {}", state.get_legal_action_ids(&db).len());
    }

    println!("\nFinal state:");
    println!("  P0 Score: {}", state.players[0].score);
    println!("  P1 Score: {}", state.players[1].score);
    println!("  P0 Success Lives: {}", state.players[0].success_lives.len());
    println!("  P1 Success Lives: {}", state.players[1].success_lives.len());
    println!("  Turn: {}", state.turn);
}
