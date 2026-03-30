//! Quick Granular Benchmark - Runs a few games and prints timing breakdown
//! 
//! Usage: cargo run --example quick_bench

use engine_rust::core::models::Phase;
use engine_rust::core::logic::{CardDatabase, GameState};
use rand::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::time::Instant;

fn load_full_db() -> CardDatabase {
    for path in &["data/cards.json", "../data/cards.json", "../../data/cards.json"] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = false;
            return db;
        }
    }
    panic!("DB not found");
}

fn build_real_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    while deck.len() < 48 { 
        if let Some(&id) = db.members.keys().next() { deck.push(id); } else { break; } 
    }
    let mut lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    while lives.len() < 12 { 
        if let Some(&id) = db.lives.keys().next() { lives.push(id); } else { break; } 
    }
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    (deck, lives, energy)
}

#[derive(Debug, Default)]
struct TimingStats {
    count: u64,
    total_ns: u64,
    min_ns: u64,
    max_ns: u64,
}

impl TimingStats {
    fn record(&mut self, duration_ns: u64) {
        self.count += 1;
        self.total_ns += duration_ns;
        if self.min_ns == 0 || duration_ns < self.min_ns { self.min_ns = duration_ns; }
        if duration_ns > self.max_ns { self.max_ns = duration_ns; }
    }
    fn avg_ns(&self) -> u64 {
        if self.count == 0 { 0 } else { self.total_ns / self.count }
    }
}

fn run_granular_benchmark(db: &CardDatabase, deck: &[i32], lives: &[i32], energy: &[i32], num_games: usize) -> HashMap<String, TimingStats> {
    let mut stats: HashMap<String, TimingStats> = HashMap::new();
    let mut rng = StdRng::seed_from_u64(42);

    for game_idx in 0..num_games {
        let mut state = GameState::default();
        state.initialize_game(
            deck.to_vec(), deck.to_vec(),
            energy.to_vec(), energy.to_vec(),
            lives.to_vec(), lives.to_vec()
        );
        state.ui.silent = true;
        state.phase = Phase::MulliganP1;
        state.current_player = 0;
        state.first_player = 0;

        let game_start = Instant::now();
        let mut steps = 0;

        while state.phase != Phase::Terminal && steps < 50000 {
            steps += 1;
            let phase = state.phase;

            if state.phase.is_interactive() {
                // Time get_legal_action_ids
                let t1 = Instant::now();
                let actions = state.get_legal_action_ids(db);
                let ns = t1.elapsed().as_nanos() as u64;
                stats.entry(format!("{:?}:get_actions", phase)).or_default().record(ns);

                if !actions.is_empty() {
                    let action = if actions.len() == 1 { actions[0] } else { actions[rng.random_range(0..actions.len())] };
                    
                    // Time step_internal
                    let t2 = Instant::now();
                    let _ = state.step_internal(db, action);
                    let ns = t2.elapsed().as_nanos() as u64;
                    stats.entry(format!("{:?}:step_internal", phase)).or_default().record(ns);
                    
                    // Time auto_step
                    let t3 = Instant::now();
                    state.auto_step(db);
                    let ns = t3.elapsed().as_nanos() as u64;
                    stats.entry(format!("{:?}:auto_step", phase)).or_default().record(ns);
                    
                    // Time sync_all_stats
                    let t4 = Instant::now();
                    state.sync_all_stats(db);
                    let ns = t4.elapsed().as_nanos() as u64;
                    stats.entry(format!("{:?}:sync_stats", phase)).or_default().record(ns);
                }
            } else {
                // Non-interactive phases
                let t = Instant::now();
                match state.phase {
                    Phase::PerformanceP1 | Phase::PerformanceP2 => {
                        let t_perf = Instant::now();
                        state.do_performance_phase(db);
                        let ns = t_perf.elapsed().as_nanos() as u64;
                        stats.entry("Performance:do_performance".to_string()).or_default().record(ns);
                    }
                    _ => { state.auto_step(db); }
                }
                let ns = t.elapsed().as_nanos() as u64;
                stats.entry(format!("{:?}:auto", phase)).or_default().record(ns);
            }
        }

        let game_ns = game_start.elapsed().as_nanos() as u64;
        stats.entry("game_total".to_string()).or_default().record(game_ns);
        println!("Game {} completed in {:.2}ms ({} steps)", game_idx + 1, game_ns as f64 / 1_000_000.0, steps);
    }

    stats
}

fn main() {
    println!("=== Quick Granular Benchmark ===");
    println!("Loading database...");
    
    let db = load_full_db();
    let (deck, lives, energy) = build_real_decks(&db);
    
    println!("Running 3 games with granular timing...\n");
    let stats = run_granular_benchmark(&db, &deck, &lives, &energy, 3);
    
    println!("\n=== GRANULAR TIMING RESULTS ===");
    println!("{:<35} | {:>8} | {:>10} | {:>10} | {:>10}", 
             "Operation", "Count", "Avg (µs)", "Min (µs)", "Max (µs)");
    println!("{}", "-".repeat(90));
    
    let mut sorted: Vec<_> = stats.iter().collect();
    sorted.sort_by(|a, b| b.1.avg_ns().cmp(&a.1.avg_ns()));
    
    for (op, s) in sorted {
        let avg_us = s.avg_ns() as f64 / 1000.0;
        let min_us = s.min_ns as f64 / 1000.0;
        let max_us = s.max_ns as f64 / 1000.0;
        println!("{:<35} | {:>8} | {:>10.2} | {:>10.2} | {:>10.2}", 
                 op, s.count, avg_us, min_us, max_us);
    }
    
    println!("\n=== ANALYSIS ===");
    if let Some(game_stat) = stats.get("game_total") {
        let avg_game_ms = game_stat.avg_ns() as f64 / 1_000_000.0;
        println!("Average game duration: {:.2}ms", avg_game_ms);
    }
    
    // Find the slowest operation
    if let Some((slowest_op, slowest_stat)) = sorted.first() {
        let max_ms = slowest_stat.max_ns as f64 / 1_000_000.0;
        println!("Slowest operation: {} (max: {:.2}ms)", slowest_op, max_ms);
    }
}
