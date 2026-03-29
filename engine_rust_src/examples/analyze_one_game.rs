//! Analyze one game in detail - board state vs performance

use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::models::Phase;
use rand::prelude::*;
use std::fs;
use std::time::Instant;

fn load_full_db() -> CardDatabase {
    for path in &["data/cards_compiled.json", "../data/cards_compiled.json"] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = true;
            return db;
        }
    }
    panic!("DB not found");
}

fn analyze_game() {
    let db = load_full_db();
    let deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    let lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    
    let mut state = GameState::default();
    state.initialize_game(deck.clone(), deck, energy.clone(), energy, lives.clone(), lives);
    state.phase = Phase::MulliganP1;
    state.current_player = 0;
    state.first_player = 0;
    
    let mut rng = StdRng::seed_from_u64(42);
    
    // Advance to Main
    while state.phase != Phase::Main && !state.is_terminal() {
        let legal = state.get_legal_action_ids(&db);
        let action = legal.choose(&mut rng).copied().unwrap_or(0);
        let _ = state.step(&db, action);
    }
    
    println!("=== Detailed Game Analysis ===\n");
    println!("{:>4} {:>12} {:>6} {:>12} {:>12} {:>12} {:>12} {:>10}", 
        "Turn", "Phase", "Player", "P0 Stage", "P1 Stage", "P0 Lives", "P1 Lives", "Time(μs)");
    println!("{}", "-".repeat(90));
    
    let mut turn_count = 0;
    let start = Instant::now();
    
    while !state.is_terminal() && turn_count < 200 {
        turn_count += 1;
        let phase = state.phase;
        let player = state.current_player;
        
        // Capture board state
        let p0_stage = state.players[0].stage.iter().filter(|&&c| c >= 0).count();
        let p1_stage = state.players[1].stage.iter().filter(|&&c| c >= 0).count();
        let p0_lives = state.players[0].live_zone.iter().filter(|&&c| c >= 0).count();
        let p1_lives = state.players[1].live_zone.iter().filter(|&&c| c >= 0).count();
        
        // Time the step
        let t = Instant::now();
        
        match phase {
            Phase::Main | Phase::LiveSet => {
                // Play up to 3 cards then pass
                for i in 0..4 {
                    let legal = state.get_legal_action_ids(&db);
                    let non_pass: Vec<_> = legal.iter().filter(|&&a| a != 0).collect();
                    let action = if i < 3 && !non_pass.is_empty() {
                        **non_pass.choose(&mut rng).unwrap()
                    } else { 0 };
                    let _ = state.step(&db, action);
                    if action == 0 { break; }
                }
            }
            _ => { state.auto_step(&db); }
        }
        
        let elapsed = t.elapsed().as_micros() as u64;
        
        // Only print interesting turns (slow or high board complexity)
        if elapsed > 50 || p0_stage > 0 || p1_stage > 0 || p0_lives > 0 || p1_lives > 0 {
            println!("{:>4} {:>12?} {:>6} {:>12} {:>12} {:>12} {:>12} {:>10}",
                turn_count, phase, player, p0_stage, p1_stage, p0_lives, p1_lives, elapsed);
        }
    }
    
    let total = start.elapsed();
    println!("\nTotal time: {:?}", total);
    println!("Winner: {:?}", state.get_winner());
    println!("Final score - P0: {} lives, P1: {} lives", 
        state.players[0].success_lives.len(),
        state.players[1].success_lives.len());
}

fn main() {
    analyze_game();
}
