use std::fs;
use std::time::Instant;
use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::enums::Phase;
use engine_rust::core::ACTION_BASE_PASS;
use rand::seq::IndexedRandom;
use rand::SeedableRng;
use rand::prelude::StdRng;

fn main() {
    let db = load_vanilla_db();
    let mut state = GameState::default();
    
    // Build decks from actual cards
    let (dummy_deck, dummy_lives, dummy_energy) = build_decks(&db);
    state.initialize_game(
        dummy_deck.clone(),
        dummy_deck.clone(),
        dummy_energy.clone(),
        dummy_energy.clone(),
        dummy_lives.clone(),
        dummy_lives.clone(),
    );
    
    // Step to Main phase
    println!("[init] Stepping to Main phase...");
    let step_start = Instant::now();
    while state.phase != Phase::Main {
        let legal = state.get_legal_action_ids(&db);
        if !legal.is_empty() {
            if state.step(&db, legal[0]).is_err() {
                break;
            }
        } else {
            break;
        }
    }
    println!("[init] ✓ Reached Main phase in {:.2}s\n", step_start.elapsed().as_secs_f32());
    
    println!("=== MOVE SPACE DISTRIBUTION ===\n");
    
    // Run random walks with progress logging
    let num_samples = 100;
    let mut depth_counts = std::collections::BTreeMap::new();
    let mut rng = StdRng::seed_from_u64(42);
    
    let start = Instant::now();
    let mut last_progress = Instant::now();
    let mut last_count = 0;
    
    for sample_idx in 0..num_samples {
        let mut test_state = state.clone();
        let mut depth = 0;
        
        loop {
            // Get legal non-Pass actions
            let legal = test_state.get_legal_action_ids(&db);
            let main_actions: Vec<i32> = legal.iter()
                .filter(|&&a| a != ACTION_BASE_PASS)
                .copied()
                .collect();
            
            if main_actions.is_empty() || test_state.phase != Phase::Main {
                break;
            }
            
            // Pick random action
            if let Some(&action) = main_actions.choose(&mut rng) {
                if test_state.step(&db, action).is_err() {
                    break;
                }
                depth += 1;
                if depth > 20 {
                    break;
                }
            } else {
                break;
            }
        }
        
        *depth_counts.entry(depth).or_insert(0) += 1;
        
        // Progress log every second
        if last_progress.elapsed().as_secs_f32() >= 1.0 {
            let total_elapsed = start.elapsed().as_secs_f32();
            let current_count = sample_idx + 1;
            let rate = current_count as f32 / total_elapsed;
            let elapsed_secs = total_elapsed as u32;
            let stalled = current_count == last_count;
            println!(
                "[{:2}s] Progress: {}/{} samples | {:.1} states/s",
                elapsed_secs, current_count, num_samples, rate
            );
            last_progress = Instant::now();
            last_count = current_count;
            
            // Timeout check
            if elapsed_secs > 10 && stalled {
                println!("[TIMEOUT] No progress for 10+ seconds, terminating...\n");
                println!("Partial results ({}/{} samples completed):", current_count, num_samples);
                break;
            }
        }
    }
    
    let total_time = start.elapsed().as_secs_f32();
    println!("\n[done] Completed in {:.2}s\n", total_time);
    
    println!("Random walk results:\n");
    for (depth, count) in &depth_counts {
        let pct = (*count as f32 / depth_counts.values().sum::<usize>() as f32) * 100.0;
        println!("Depth {}: {} sequences ({:.1}%)", depth, count, pct);
    }
    
    // Estimate branching if we have enough data
    if depth_counts.len() >= 2 {
        let depths: Vec<usize> = depth_counts.keys().copied().collect();
        if depths[0] + 1 == depths[1] {
            let branching = depth_counts[&depths[1]] as f32 / depth_counts[&depths[0]] as f32;
            println!("\nEstimated branching factor: {:.2}x", branching);
            
            // Extrapolate
            println!("\nExtrapolated sequence counts:");
            for d in 1..=10 {
                let est = (branching.powi(d as i32)) as usize;
                println!("  Depth {}: ~{} sequences", d, est);
            }
        }
    }
}

fn build_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut dummy_deck = Vec::new();
    let mut dummy_lives = Vec::new();
    
    for &id in db.members.keys() {
        dummy_deck.push(id);
        if dummy_deck.len() >= 48 {
            break;
        }
    }
    while dummy_deck.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            dummy_deck.push(id);
        } else {
            break;
        }
    }
    
    for &id in db.lives.keys() {
        dummy_lives.push(id);
        if dummy_lives.len() >= 12 {
            break;
        }
    }
    while dummy_lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            dummy_lives.push(id);
        } else {
            break;
        }
    }
    
    let dummy_energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    
    (dummy_deck, dummy_lives, dummy_energy)
}

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
        let json = fs::read_to_string(path).expect("Failed to read DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
        db.is_vanilla = true;
        return db;
    }
    panic!("cards_vanilla.json not found");
}
