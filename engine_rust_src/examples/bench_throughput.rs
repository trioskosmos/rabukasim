//! Raw throughput benchmark - headless, silent, maximum speed

use engine_rust::core::logic::{CardDatabase, GameState, Phase};
use rand::prelude::*;
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

fn run_headless_game(db: &CardDatabase, deck: &[i32], lives: &[i32], energy: &[i32], seed: u64) -> (u32, u64) {
    let mut state = GameState::default();
    state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
    state.phase = Phase::MulliganP1;
    state.current_player = 0;
    state.first_player = 0;
    
    // HEADLESS MODE - disable all UI/logging
    state.ui.silent = true;
    state.debug.debug_mode = false;
    
    let mut rng = StdRng::seed_from_u64(seed);
    let mut total_steps = 0u32;
    
    let start = Instant::now();
    
    while !state.is_terminal() && total_steps < 1000 {
        match state.phase {
            Phase::Main | Phase::LiveSet | Phase::MulliganP1 | Phase::MulliganP2 | Phase::Response => {
                let legal = state.get_legal_action_ids(db);
                if legal.is_empty() { 
                    let _ = state.step(db, 0);
                } else {
                    let action = *legal.choose(&mut rng).unwrap_or(&0);
                    let _ = state.step(db, action);
                }
            }
            _ => {
                state.auto_step(db);
            }
        }
        total_steps += 1;
    }
    
    let elapsed_ns = start.elapsed().as_nanos() as u64;
    (total_steps, elapsed_ns)
}

fn main() {
    println!("=== Raw Throughput Benchmark (Headless/Silent) ===\n");
    
    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);
    
    // Warmup
    println!("Warming up...");
    for _ in 0..5 {
        let _ = run_headless_game(&db, &deck, &lives, &energy, 42);
    }
    
    // Benchmark: run many games
    const GAMES: usize = 1000;
    let mut total_steps = 0u64;
    let mut total_ns = 0u64;
    let mut min_ns = u64::MAX;
    let mut max_ns = 0u64;
    
    println!("Running {} games...", GAMES);
    let bench_start = Instant::now();
    
    for i in 0..GAMES {
        let seed = i as u64;
        let (steps, ns) = run_headless_game(&db, &deck, &lives, &energy, seed);
        total_steps += steps as u64;
        total_ns += ns;
        min_ns = min_ns.min(ns);
        max_ns = max_ns.max(ns);
        
        if i > 0 && i % 200 == 0 {
            println!("  Completed {} games...", i);
        }
    }
    
    let bench_ns = bench_start.elapsed().as_nanos() as u64;
    
    // Stats
    let avg_ns_per_game = total_ns / GAMES as u64;
    let avg_steps_per_game = total_steps / GAMES as u64;
    let ns_per_step = total_ns / total_steps;
    
    let games_per_sec = 1_000_000_000.0 / avg_ns_per_game as f64;
    let steps_per_sec = 1_000_000_000.0 / ns_per_step as f64;
    
    println!("\n=== Results ===");
    println!("Games:        {}", GAMES);
    println!("Total steps:  {}", total_steps);
    println!("Avg steps/game: {}", avg_steps_per_game);
    println!("\nTime per game: {}μs (min: {}μs, max: {}μs)", 
        avg_ns_per_game / 1000, min_ns / 1000, max_ns / 1000);
    println!("Time per step: {}ns", ns_per_step);
    println!("\nThroughput:");
    println!("  Games/sec:  {:.0}", games_per_sec);
    println!("  Steps/sec:  {:.0}", steps_per_sec);
    println!("\nTotal benchmark time: {}ms", bench_ns / 1_000_000);
}
