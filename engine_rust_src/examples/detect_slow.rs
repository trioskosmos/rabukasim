//! Standalone slow action detector - runs quickly without benchmark overhead

use engine_rust::core::logic::{CardDatabase, GameState, Phase};
use rand::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::time::Instant;

fn load_full_db() -> CardDatabase {
    // Use cards_compiled.json with vanilla mode (abilities disabled)
    for path in &[
        "data/cards_compiled.json",
        "../data/cards_compiled.json", 
        "../../data/cards_compiled.json",
    ] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = true;  // Disable abilities - no infinite trigger loops
            eprintln!("Loaded DB from: {} ({} members, {} lives) [vanilla mode]", 
                path, db.members.len(), db.lives.len());
            return db;
        }
    }
    panic!("DB not found - looked for cards_compiled.json");
}

fn build_real_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    while deck.len() < 48 { if let Some(&id) = db.members.keys().next() { deck.push(id); } else { break; } }
    let mut lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    while lives.len() < 12 { if let Some(&id) = db.lives.keys().next() { lives.push(id); } else { break; } }
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    (deck, lives, energy)
}

#[derive(Debug, Default)]
struct TimingStats { count: u64, total_ns: u64, min_ns: u64, max_ns: u64, slow_count: u64 }

impl TimingStats {
    fn record(&mut self, ns: u64, threshold: u64) {
        self.count += 1; self.total_ns += ns;
        if self.min_ns == 0 || ns < self.min_ns { self.min_ns = ns; }
        if ns > self.max_ns { self.max_ns = ns; }
        if ns > threshold { self.slow_count += 1; }
    }
    fn avg_ns(&self) -> u64 { if self.count == 0 { 0 } else { self.total_ns / self.count } }
}

fn run_game(
    db: &CardDatabase, deck: &[i32], lives: &[i32], energy: &[i32],
    threshold_ns: u64, rng: &mut StdRng,
    stats: &mut HashMap<String, TimingStats>,
    verbose: bool
) -> (i32, u32) {
    let mut state = GameState::default();
    
    // Use initialize_game like simple_game.rs does
    state.initialize_game(
        deck.to_vec(),
        deck.to_vec(),
        energy.to_vec(),
        energy.to_vec(),
        lives.to_vec(),
        lives.to_vec(),
    );
    
    // Skip to Main phase like simple_game does
    state.phase = Phase::MulliganP1;
    state.current_player = 0;
    state.first_player = 0;
    
    // Advance through RPS/Mulligan to first Main phase
    while state.phase != Phase::Main && !state.is_terminal() {
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                let legal = state.get_legal_action_ids(db);
                if !legal.is_empty() {
                    let &action = legal.choose(rng).unwrap_or(&0);
                    let _ = state.step(db, action);
                } else {
                    let _ = state.step(db, 0);
                }
            }
            _ => state.auto_step(db),
        }
    }

    let mut auto_steps = 0;
    let max_steps = 1000; // 1000 steps should be plenty for vanilla games
    let mut step_log: Vec<(String, u64, u64)> = Vec::new();
    
    // Main game loop - like simple_game.rs
    while !state.is_terminal() && auto_steps < max_steps {
        auto_steps += 1;
        let phase = state.phase;
        
        if verbose && auto_steps <= 30 {
            println!("  Step {}: {:?} (Player {})", auto_steps, phase, state.current_player);
        }
        
        match phase {
            Phase::Main => {
                // Play multiple cards in one turn, then pass
                let mut turn_actions = 0;
                loop {
                    let legal = state.get_legal_action_ids(db);
                    if legal.is_empty() { break; }
                    
                    // Prefer non-pass actions for first few plays
                    let action = if turn_actions < 3 {
                        let non_pass: Vec<_> = legal.iter().filter(|&&a| a != 0).collect();
                        if !non_pass.is_empty() {
                            **non_pass.choose(rng).unwrap()
                        } else { 0 }
                    } else { 0 }; // Pass after 3 attempts
                    
                    // Log board state before step for analysis
                    let p0_stage = state.players[0].stage.iter().filter(|&&c| c >= 0).count();
                    let p1_stage = state.players[1].stage.iter().filter(|&&c| c >= 0).count();
                    let p0_lives = state.players[0].live_zone.iter().filter(|&&c| c >= 0).count();
                    let p1_lives = state.players[1].live_zone.iter().filter(|&&c| c >= 0).count();
                    
                    let t = Instant::now();
                    let _ = state.step(db, action);
                    let step_ns = t.elapsed().as_nanos() as u64;
                    stats.entry(format!("{:?}:step", phase)).or_default().record(step_ns, threshold_ns);
                    
                    // Log ALL steps to see the transition chain
                    if verbose {
                        println!("  {:?}[P{}]: action={} time={}μs | Stage:{}-{} Lives:{}-{}",
                            phase, state.current_player, action, step_ns/1000, p0_stage, p1_stage, p0_lives, p1_lives);
                    }
                    if step_ns > threshold_ns {
                        step_log.push((format!("{:?}:step[S{}-L{}-{}]", phase, p0_stage+p1_stage, p0_lives+p1_lives, step_ns/1000), step_ns, legal.len() as u64));
                    }
                    
                    turn_actions += 1;
                    auto_steps += 1;
                    if action == 0 || auto_steps >= max_steps { break; }
                }
                auto_steps -= 1; // Compensate for outer loop increment
            }
            Phase::LiveSet => {
                // Set multiple lives in one turn, then pass
                let mut turn_actions = 0;
                loop {
                    let legal = state.get_legal_action_ids(db);
                    if legal.is_empty() { break; }
                    
                    // Prefer non-pass actions
                    let action = if turn_actions < 3 {
                        let non_pass: Vec<_> = legal.iter().filter(|&&a| a != 0).collect();
                        if !non_pass.is_empty() {
                            **non_pass.choose(rng).unwrap()
                        } else { 0 }
                    } else { 0 }; // Pass
                    
                    let t = Instant::now();
                    let _ = state.step(db, action);
                    let step_ns = t.elapsed().as_nanos() as u64;
                    stats.entry(format!("{:?}:step", phase)).or_default().record(step_ns, threshold_ns);
                    
                    turn_actions += 1;
                    auto_steps += 1;
                    if action == 0 || auto_steps >= max_steps { break; }
                }
                auto_steps -= 1; // Compensate for outer loop increment
            }
            Phase::Active | Phase::Draw | Phase::Energy | Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::LiveResult => {
                let t = Instant::now();
                state.auto_step(db);
                let auto_ns = t.elapsed().as_nanos() as u64;
                // Track each auto phase separately
                stats.entry(format!("{:?}", phase)).or_default().record(auto_ns, threshold_ns);
            }
            _ => {
                let legal = state.get_legal_action_ids(db);
                let action = if !legal.is_empty() {
                    *legal.choose(rng).unwrap_or(&0)
                } else {
                    0
                };
                let _ = state.step(db, action);
            }
        }
    }
    
    if verbose {
        println!("  Total steps: {}", auto_steps);
        println!("  Final phase: {:?}", state.phase);
        if !step_log.is_empty() {
            println!("  Slow steps (>{}μs):", threshold_ns / 1000);
            for (op, ns, actions) in step_log.iter().take(10) {
                println!("    {}: {} μs ({} actions)", op, ns / 1000, actions);
            }
        }
    }
    
    (state.get_winner(), auto_steps)
}

fn main() {
    println!("=== Slow Action Detector ===\n");
    
    let db = load_full_db();
    let (deck, lives, energy) = build_real_decks(&db);
    let threshold_ns = 1000; // 1 microsecond
    
    let mut all_stats: HashMap<String, TimingStats> = HashMap::new();
    let mut completed = 0;
    let total_games = 1;  // Just 1 game for detailed analysis
    let overall_start = Instant::now();
    
    println!("\n=== Running {} games ===\n", total_games);
    
    // Run first game with verbose logging - show ALL phases
    println!("--- GAME 1 (verbose logging) ---");
    let mut rng = StdRng::seed_from_u64(42);
    let mut game_stats = HashMap::new();
    let (winner, _steps) = run_game(&db, &deck, &lives, &energy, threshold_ns, &mut rng, &mut game_stats, true);
    println!("  Winner: {} (0=P1, 1=P2, -1=draw/timeout)\n", winner);
    
    // Aggregate first game stats
    for (k, v) in game_stats {
        let e = all_stats.entry(k).or_default();
        e.count += v.count; e.total_ns += v.total_ns;
        if e.min_ns == 0 || v.min_ns < e.min_ns { e.min_ns = v.min_ns; }
        if v.max_ns > e.max_ns { e.max_ns = v.max_ns; }
        e.slow_count += v.slow_count;
    }
    if winner >= 0 { completed += 1; }
    
    // Run remaining games silently
    for i in 1..total_games {
        let mut rng = StdRng::seed_from_u64(42 + i as u64);
        let mut game_stats = HashMap::new();
        let (winner, _) = run_game(&db, &deck, &lives, &energy, threshold_ns, &mut rng, &mut game_stats, false);
        if winner >= 0 { completed += 1; }
        
        for (k, v) in game_stats {
            let e = all_stats.entry(k).or_default();
            e.count += v.count; e.total_ns += v.total_ns;
            if e.min_ns == 0 || v.min_ns < e.min_ns { e.min_ns = v.min_ns; }
            if v.max_ns > e.max_ns { e.max_ns = v.max_ns; }
            e.slow_count += v.slow_count;
        }
        print!(".");
    }
    
    let total_time = overall_start.elapsed();
    println!("\n\n=== Aggregate Results ({} games, {:?}) ===", total_games, total_time);
    println!("Completed: {}/{} ({}%)", completed, total_games, completed * 100 / total_games);
    println!("Time per game: {:?}", total_time / total_games as u32);
    
    let mut sorted: Vec<_> = all_stats.iter().collect();
    sorted.sort_by(|a, b| b.1.max_ns.cmp(&a.1.max_ns));
    
    println!("\n=== TOP 10 SLOWEST OPERATIONS ===");
    println!("{:<35} | {:>8} | {:>8} | {:>8} | {:>6}", "Operation", "Calls", "Avg (μs)", "Max (μs)", "Slow");
    println!("{}", "-".repeat(85));
    for (op, s) in sorted.iter().take(10) {
        println!("{:<35} | {:>8} | {:>8.2} | {:>8.2} | {:>6}", 
            op, s.count, s.avg_ns() as f64 / 1000.0, s.max_ns as f64 / 1000.0, s.slow_count);
    }
    
    // Highlight problem areas
    println!("\n=== PERFORMANCE HOTSPOTS ===");
    for (op, s) in sorted.iter().take(5) {
        if s.max_ns > 100_000 { // > 100μs
            println!("⚠️  {} - MAX: {:.2}ms (avg: {:.2}μs, {} calls)", 
                op, s.max_ns as f64 / 1_000_000.0, s.avg_ns() as f64 / 1000.0, s.count);
        }
    }
}
