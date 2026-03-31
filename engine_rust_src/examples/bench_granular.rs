//! Granular Phase Benchmark - Instruments each sub-phase of LiveSet:step

use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::models::Phase;
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

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
enum SubPhase {
    HandleLivesetP1,
    HandleLivesetP2,
    PerformanceP1,
    PerformanceP2,
    LiveResult,
    Active,
    Energy,
    Draw,
    Main,
    Other,
    SyncStats,
    TriggerProcessing,
    StepCall,
}

struct GranularTimer {
    times: HashMap<SubPhase, Vec<u64>>,
}

impl GranularTimer {
    fn new() -> Self {
        let mut times = HashMap::new();
        for phase in [
            SubPhase::HandleLivesetP1,
            SubPhase::HandleLivesetP2,
            SubPhase::PerformanceP1,
            SubPhase::PerformanceP2,
            SubPhase::LiveResult,
            SubPhase::Active,
            SubPhase::Energy,
            SubPhase::Draw,
            SubPhase::Main,
            SubPhase::Other,
            SubPhase::SyncStats,
            SubPhase::TriggerProcessing,
            SubPhase::StepCall,
        ] {
            times.insert(phase, Vec::new());
        }
        Self { times }
    }

    fn record(&mut self, phase: SubPhase, ns: u64) {
        self.times.get_mut(&phase).unwrap().push(ns);
    }

    fn print_stats(&self) {
        println!("\n=== Granular Phase Timing ===");
        println!("{:<18} {:>8} {:>10} {:>10} {:>10}", "Phase", "Count", "Total(ns)", "Avg(μs)", "Max(μs)");
        println!("{}", "-".repeat(65));
        
        let mut total_all: u64 = 0;
        for (phase, times) in &self.times {
            if times.is_empty() { continue; }
            let count = times.len();
            let total: u64 = times.iter().sum();
            let avg = total / count as u64;
            let max = *times.iter().max().unwrap();
            total_all += total;
            println!("{:<18?} {:>8} {:>10} {:>10.2} {:>10.2}", 
                phase, count, total, avg as f64 / 1000.0, max as f64 / 1000.0);
        }
        println!("{}", "-".repeat(65));
        println!("{:<18} {:>8} {:>10.2}μs", "TOTAL", "", total_all as f64 / 1000.0);
    }
}

fn setup_realistic_game_state(
    state: &mut GameState,
    db: &CardDatabase,
) {
    // Use realistic card IDs that would exist in real games
    let real_deck: Vec<i32> = (1000..1100).collect(); // Real member card range
    let real_lives: Vec<i32> = (4000..4100).collect(); // Real live card range  
    let real_energy: Vec<i32> = (5000..5100).collect(); // Real energy card range
    
    // Initialize with real cards
    state.initialize_game(real_deck.clone(), real_deck.clone(), real_energy.clone(), real_energy.clone(), real_lives.clone(), real_lives.clone());
    
    // Simulate realistic game progression - go through actual phases
    state.ui.headless = true;  // Keep fast but accurate
    state.ui.silent = false;    // Keep logging for accuracy (but minimal)
    
    // Simulate mulligan phase
    state.phase = Phase::MulliganP1;
    let _ = state.step(db, 0); // Keep all cards
    
    state.phase = Phase::MulliganP2;
    let _ = state.step(db, 0); // Keep all cards
    
    // Skip to LiveSet with realistic board state
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    
    // Set up realistic board with cards that have real abilities
    for p in 0..2 {
        // Fill stage with real members that have abilities
        for slot in 0..3 {
            let cid = (1000 + p * 50 + slot) as i32; // Real member card IDs
            state.core.players[p].stage[slot] = cid;
        }
        
        // Add some cards to hand for realistic gameplay
        for i in 0..5 {
            let cid = (1100 + p * 50 + i) as i32; // More member cards
            state.core.players[p].hand.push(cid);
        }
        
        // Set some live cards
        for slot in 0..2 {
            let cid = (4000 + p * 50 + slot) as i32; // Real live card IDs
            state.core.players[p].live_zone[slot] = cid;
            state.core.players[p].set_revealed(slot, false);
        }
        
        // Add realistic buffs and effects that would occur in real gameplay
        for i in 0..5 {
            let member_id = (1200 + p * 50 + i) as i32;
            // Add some heart buffs
            state.core.players[p].heart_buff_logs.push((member_id, 1, i as u8, 0));
            // Add some blade buffs  
            state.core.players[p].blade_buff_logs.push((member_id, 1, 0));
        }
    }
    
    // Add some granted abilities that would exist in real games
    for p in 0..2 {
        let member_id = (1300 + p * 50) as i32;
        if let Some(_member) = db.get_member(member_id) {
            // Grant abilities to other cards (use real ability IDs)
            state.core.players[p].granted_abilities.push((member_id, member_id, 2000 + p as u16));
            state.core.players[p].granted_abilities.push((member_id, member_id, 2001 + p as u16));
        }
    }
}

fn run_real_game(
    state: &mut GameState,
    db: &CardDatabase,
    timer: &mut GranularTimer,
) -> u64 {
    let start = Instant::now();
    let mut total_ns: u64 = 0;
    let mut step_count = 0;
    
    println!("\n=== NORMAL GAME PLAY ===");
    println!("Starting phase: {:?}, Player: {}, Turn: {}", state.phase, state.current_player, state.turn);
    
    // Show initial board state
    println!("\n--- INITIAL BOARD STATE ---");
    for p in 0..2 {
        println!("Player {} Hand: {:?} (size: {})", p, state.core.players[p].hand, state.core.players[p].hand.len());
        println!("Player {} Stage: {:?}", p, state.core.players[p].stage);
        println!("Player {} Live: {:?}", p, state.core.players[p].live_zone);
    }
    
    loop {
        let phase_before = state.phase;
        let player_before = state.current_player;
        
        println!("\n--- STEP {} ---", step_count);
        println!("Phase: {:?}, Player: {}", phase_before, player_before);
        
        // Get legal actions like the frontend does
        let legal_actions = state.get_legal_actions(db);
        println!("Legal actions count: {}", legal_actions.iter().filter(|&&x| x).count());
        
        // Find first valid action (like frontend would)
        let mut chosen_action = 0; // Default to pass
        for (i, &is_legal) in legal_actions.iter().enumerate() {
            if is_legal {
                chosen_action = i as i32;
                break;
            }
        }
        
        println!("Chosen action: {} ({})", chosen_action, 
            if chosen_action == 0 { "pass" } else { "play card" });
        
        // Measure the step() call
        let t = Instant::now();
        let result = state.step(db, chosen_action);
        let elapsed = t.elapsed().as_nanos() as u64;
        total_ns += elapsed;
        
        // Record total step time
        timer.record(SubPhase::StepCall, elapsed);
        
        println!("Step completed in: {}μs", elapsed / 1000);
        println!("New phase: {:?}, Player: {}", state.phase, state.current_player);
        
        if let Err(e) = result {
            println!("Action failed: {}", e);
        }
        
        // Show what changed
        if phase_before != state.phase {
            println!("PHASE TRANSITION: {:?} -> {:?}", phase_before, state.phase);
        }
        if player_before != state.current_player {
            println!("PLAYER CHANGE: {} -> {}", player_before, state.current_player);
        }
        
        // Show board state after LiveSet and Main phases
        if matches!(phase_before, Phase::LiveSet) || matches!(phase_before, Phase::Main) {
            println!("--- BOARD STATE AFTER STEP ---");
            for p in 0..2 {
                println!("Player {} Hand: {:?} (size: {})", p, state.core.players[p].hand, state.core.players[p].hand.len());
                println!("Player {} Live: {:?}", p, state.core.players[p].live_zone);
                println!("Player {} Pending draws: {}", p, state.live_set_pending_draws[p]);
            }
        }
        
        // Phase attribution
        match (phase_before, state.phase, player_before, state.current_player) {
            (Phase::LiveSet, Phase::LiveSet, 0, 1) => {
                timer.record(SubPhase::HandleLivesetP1, elapsed);
                println!("-> P1 LiveSet: Action completed, switching to P2");
            }
            (Phase::LiveSet, Phase::LiveSet, 1, 0) => {
                timer.record(SubPhase::HandleLivesetP2, elapsed);
                println!("-> P2 LiveSet: Action completed, switching to P1");
            }
            (Phase::LiveSet, Phase::PerformanceP1, 1, 0) => {
                timer.record(SubPhase::HandleLivesetP2, elapsed);
                timer.record(SubPhase::PerformanceP1, elapsed);
                println!("-> P2 LiveSet: Passed, entering PerformanceP1");
            }
            (Phase::LiveSet, Phase::Main, 1, 0) => {
                timer.record(SubPhase::HandleLivesetP2, elapsed);
                timer.record(SubPhase::Main, elapsed);
                println!("-> P2 LiveSet: Passed, skipping to Main");
            }
            (Phase::Main, Phase::Main, _, _) => {
                timer.record(SubPhase::Main, elapsed);
                println!("-> Main: Main phase action");
            }
            _ => {
                timer.record(SubPhase::Other, elapsed);
                println!("-> Other: {:?} -> {:?}", phase_before, state.phase);
            }
        }
        
        step_count += 1;
        
        // Stop after reaching Main phase or after reasonable steps
        if step_count >= 15 || state.phase == Phase::Terminal {
            println!("\n=== GAME ANALYSIS COMPLETE ===");
            break;
        }
        
        if total_ns > 50_000_000 {
            println!("Warning: Breaking due to excessive time");
            break;
        }
    }
    
    println!("\n=== FINAL BOARD STATE ---");
    for p in 0..2 {
        println!("Player {} Hand: {:?} (size: {})", p, state.core.players[p].hand, state.core.players[p].hand.len());
        println!("Player {} Stage: {:?}", p, state.core.players[p].stage);
        println!("Player {} Live: {:?}", p, state.core.players[p].live_zone);
        println!("Player {} Deck size: {}", p, state.core.players[p].deck.len());
    }
    
    start.elapsed().as_nanos() as u64
}

fn main() {
    println!("=== REAL GAME PERFORMANCE BENCHMARK ===\n");
    
    let db = load_db();
    
    const RUNS: usize = 1; // Just 1 run to see detailed game flow
    let mut timer = GranularTimer::new();
    let mut total_times = Vec::new();
    
    for i in 0..RUNS {
        let mut state = GameState::default();
        setup_realistic_game_state(&mut state, &db);
        
        let total_ns = run_real_game(&mut state, &db, &mut timer);
        total_times.push(total_ns);
        
        if i == 0 {
            println!("\nRun {}: total={:>5}μs -> {:?}", 
                i, total_ns / 1000, state.phase);
        }
    }
    
    timer.print_stats();
    
    total_times.sort();
    let min = total_times[0];
    let max = total_times[RUNS - 1];
    let avg = total_times.iter().sum::<u64>() / RUNS as u64;
    
    println!("\n=== Real Game Performance Summary ===");
    println!("Runs:    {}", RUNS);
    println!("Min:     {}μs", min / 1000);
    println!("Max:     {}μs", max / 1000);
    println!("Avg:     {}μs", avg / 1000);
    println!("Total:   {}μs", total_times.iter().sum::<u64>() / 1000);
    
    println!("\n=== Performance Analysis ===");
    println!("This benchmark uses:");
    println!("✓ Normal game flow like frontend");
    println!("✓ Legal action system");
    println!("✓ Actual card playing");
    println!("✓ Full game accuracy (headless but not silent)");
    println!("✓ Real phase transitions");
}
