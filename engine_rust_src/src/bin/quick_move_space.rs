use std::fs;
use std::time::Instant;
use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::enums::Phase;
use engine_rust::core::ACTION_BASE_PASS;
use rand::seq::IndexedRandom;
use rand::SeedableRng;
use rand::prelude::StdRng;

fn main() {
    println!("[init] Loading database...");
    let start_init = Instant::now();
    let db = load_vanilla_db();
    println!("[init] ✓ DB loaded in {:.2}s", start_init.elapsed().as_secs_f32());
    
    println!("[init] Creating game state...");
    let (deck, lives, energy) = build_decks(&db);
    let mut state = GameState::default();
    state.initialize_game(deck.clone(), deck.clone(), energy.clone(), energy.clone(), lives.clone(), lives.clone());
    println!("[init] ✓ Game state created");
    println!("[init] Current phase: {:?}", state.phase);
    
    // Don't wait for Main phase - sample from current state
    println!("\n=== MEASURING MOVE SPACE (100 random walks) ===\n");
    
    let start = Instant::now();
    let mut last_log = Instant::now();
    let mut depth_counts = std::collections::BTreeMap::new();
    let mut rng = StdRng::seed_from_u64(42);
    
    for sample_idx in 0..100 {
        let mut test_state = state.clone();
        let mut depth = 0;
        
        // Just count steps until we can't proceed
        for _ in 0..25 {
            let legal = test_state.get_legal_action_ids(&db);
            if legal.is_empty() {
                break;
            }
            
            if let Some(&action) = legal.choose(&mut rng) {
                if test_state.step(&db, action).is_err() {
                    break;
                }
                depth += 1;
            } else {
                break;
            }
        }
        
        *depth_counts.entry(depth).or_insert(0) += 1;
        
        // Log progress every second
        if last_log.elapsed().as_secs_f32() >= 1.0 {
            let elapsed = start.elapsed().as_secs_f32();
            let rate = (sample_idx + 1) as f32 / elapsed;
            println!("[{:.0}s] Sample {}/100 | {:.1} states/s", elapsed, sample_idx + 1, rate);
            last_log = Instant::now();
        }
    }
    
    println!("\n[done] {:.2}s total\n", start.elapsed().as_secs_f32());
    println!("=== RESULTS ===\n");
    
    for (depth, count) in &depth_counts {
        println!("Depth {}: {} walks", depth, count);
    }
    
    if let Some(max_depth) = depth_counts.keys().max() {
        println!("\nMax sequence length: {}", max_depth);
    }
}

fn build_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    while deck.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            deck.push(id);
        } else { break; }
    }
    
    let mut lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    while lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            lives.push(id);
        } else { break; }
    }
    
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    
    (deck, lives, energy)
}

fn load_vanilla_db() -> CardDatabase {
    for path in &["data/cards_vanilla.json", "../data/cards_vanilla.json", "../../data/cards_vanilla.json"] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = true;
            return db;
        }
    }
    panic!("cards_vanilla.json not found");
}
