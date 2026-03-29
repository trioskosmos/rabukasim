//! Deterministic benchmark - records and replays exact game sequences

use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::models::Phase;
use rand::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::time::Instant;

fn load_db() -> CardDatabase {
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

fn build_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    let lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    (deck, lives, energy)
}

/// Record a game, returning the action sequence and stats
fn record_game(db: &CardDatabase, deck: &[i32], lives: &[i32], energy: &[i32], seed: u64) -> Vec<(Phase, i32, u64)> {
    let mut state = GameState::default();
    state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
    state.phase = Phase::MulliganP1;
    state.current_player = 0;
    state.first_player = 0;
    
    let mut rng = StdRng::seed_from_u64(seed);
    let mut actions = Vec::new();
    let mut steps = 0;
    
    // Advance to Main
    while state.phase != Phase::Main && !state.is_terminal() && steps < 100 {
        steps += 1;
        let legal = state.get_legal_action_ids(db);
        let action = legal.choose(&mut rng).copied().unwrap_or(0);
        let t = Instant::now();
        let _ = state.step(db, action);
        let elapsed = t.elapsed().as_nanos() as u64;
        actions.push((state.phase, action, elapsed));
    }
    
    // Main game loop
    while !state.is_terminal() && steps < 500 {
        let phase = state.phase;
        
        match phase {
            Phase::Main | Phase::LiveSet => {
                // Play up to 3 cards then pass
                for _ in 0..4 {
                    let legal = state.get_legal_action_ids(db);
                    if legal.is_empty() { break; }
                    
                    let non_pass: Vec<_> = legal.iter().filter(|&&a| a != 0).collect();
                    let action = if !non_pass.is_empty() {
                        **non_pass.choose(&mut rng).unwrap()
                    } else { 0 };
                    
                    let t = Instant::now();
                    let _ = state.step(db, action);
                    let elapsed = t.elapsed().as_nanos() as u64;
                    actions.push((phase, action, elapsed));
                    steps += 1;
                    
                    if action == 0 { break; }
                }
            }
            _ => {
                let t = Instant::now();
                state.auto_step(db);
                let elapsed = t.elapsed().as_nanos() as u64;
                actions.push((phase, 0, elapsed));
                steps += 1;
            }
        }
    }
    
    actions
}

/// Replay a recorded action sequence and time it
fn replay_game(db: &CardDatabase, deck: &[i32], lives: &[i32], energy: &[i32], actions: &[(Phase, i32, u64)]) -> (u64, u32, i32) {
    let mut state = GameState::default();
    state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
    state.phase = Phase::MulliganP1;
    state.current_player = 0;
    state.first_player = 0;
    
    let start = Instant::now();
    let mut step_count = 0u32;
    
    for (_expected_phase, action, _original_time) in actions {
        if state.is_terminal() { break; }
        
        // Execute based on current phase
        match state.phase {
            Phase::Main | Phase::LiveSet => {
                let _ = state.step(db, *action);
            }
            _ => {
                state.auto_step(db);
            }
        }
        step_count += 1;
    }
    
    let total_ns = start.elapsed().as_nanos() as u64;
    let winner = state.get_winner();
    (total_ns, step_count, winner)
}

fn main() {
    println!("=== Deterministic Game Benchmark ===\n");
    
    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);
    const SEED: u64 = 42;
    
    // Step 1: Record the game
    println!("Recording game with seed {}...", SEED);
    let recorded = record_game(&db, &deck, &lives, &energy, SEED);
    println!("Recorded {} steps", recorded.len());
    
    // Show action distribution
    let mut by_phase: HashMap<Phase, (usize, u64)> = HashMap::new();
    for (phase, _action, time) in &recorded {
        let entry = by_phase.entry(*phase).or_insert((0, 0));
        entry.0 += 1;
        entry.1 += time;
    }
    
    println!("\nRecorded game breakdown:");
    for (phase, (count, total_ns)) in &by_phase {
        println!("  {:?}: {} steps, avg {}μs", phase, count, total_ns / (*count as u64 * 1000));
    }
    
    // Step 2: Replay multiple times for consistent benchmarking
    println!("\n=== Benchmarking: 10 replays ===");
    let mut times = Vec::new();
    let mut winners = Vec::new();
    
    for i in 0..10 {
        let (total_ns, steps, winner) = replay_game(&db, &deck, &lives, &energy, &recorded);
        let total_us = total_ns;
        times.push(total_us);
        winners.push(winner);
        println!("  Run {}: {} steps in {}ns, winner={}", 
            i + 1, steps, total_us, winner);
    }
    
    // Stats
    let min = *times.iter().min().unwrap();
    let max = *times.iter().max().unwrap();
    let avg = times.iter().sum::<u64>() / times.len() as u64;
    
    println!("\n=== Results ===");
    println!("Min: {}ns, Max: {}ns, Avg: {}ns", min, max, avg);
    if avg > 0 {
        println!("Variance: {:.1}%", ((max - min) as f64 / avg as f64) * 100.0);
    }
    
    // Verify all replays have same winner
    let first_winner = winners[0];
    let all_same = winners.iter().all(|&w| w == first_winner);
    println!("All replays have same winner: {}", all_same);
    
    // Save the recorded game for reuse
    let json = serde_json::to_string(&recorded.iter().map(|(p, a, _)| (*p as i32, *a)).collect::<Vec<_>>()).unwrap();
    let _ = fs::write("target/benchmark_game.json", json);
    println!("\nSaved game sequence to target/benchmark_game.json");
}
