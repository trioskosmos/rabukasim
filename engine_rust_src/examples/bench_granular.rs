//! Granular Phase Benchmark - Instruments each sub-phase of LiveSet:step

use engine_rust::core::logic::{CardDatabase, GameState, MainPhaseController, TurnPhaseController};
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

fn setup_liveset_state(
    state: &mut GameState,
    deck: &[i32],
    lives: &[i32],
    energy: &[i32],
) {
    state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    
    for p in 0..2 {
        for slot in 0..3 {
            if let Some(&cid) = deck.get(slot + p * 3) {
                state.core.players[p].stage[slot] = cid;
            }
        }
        for slot in 0..2 {
            if let Some(&cid) = lives.get(slot + p * 3) {
                state.core.players[p].live_zone[slot] = cid;
                state.core.players[p].set_revealed(slot, false);
            }
        }
    }
}

fn run_full_liveset_transition(
    state: &mut GameState,
    db: &CardDatabase,
    timer: &mut GranularTimer,
) -> u64 {
    let start = Instant::now();
    let mut total_ns: u64 = 0;
    
    loop {
        let phase_before = state.phase;
        let player_before = state.current_player;
        
        let t = Instant::now();
        let _ = state.step(db, 0);
        let elapsed = t.elapsed().as_nanos() as u64;
        total_ns += elapsed;
        
        match (phase_before, state.phase, player_before, state.current_player) {
            (Phase::LiveSet, _, 0, 1) => {
                timer.record(SubPhase::HandleLivesetP1, elapsed);
            }
            (Phase::LiveSet, _, 1, 0) | (Phase::LiveSet, Phase::PerformanceP1, 1, 0) => {
                timer.record(SubPhase::HandleLivesetP2, elapsed);
            }
            (Phase::PerformanceP1, _, _, _) => {
                timer.record(SubPhase::PerformanceP1, elapsed);
            }
            (Phase::PerformanceP2, _, _, _) => {
                timer.record(SubPhase::PerformanceP2, elapsed);
            }
            (Phase::LiveResult, _, _, _) => {
                timer.record(SubPhase::LiveResult, elapsed);
            }
            (Phase::Active, _, _, _) => {
                timer.record(SubPhase::Active, elapsed);
            }
            (Phase::Energy, _, _, _) => {
                timer.record(SubPhase::Energy, elapsed);
            }
            (Phase::Draw, _, _, _) => {
                timer.record(SubPhase::Draw, elapsed);
            }
            (Phase::Main, _, _, _) => {
                timer.record(SubPhase::Main, elapsed);
            }
            _ => {
                timer.record(SubPhase::Other, elapsed);
            }
        }
        
        if state.phase == Phase::Main || state.phase == Phase::Terminal {
            break;
        }
        
        if total_ns > 10_000_000 {
            println!("Warning: Breaking due to excessive time");
            break;
        }
    }
    
    start.elapsed().as_nanos() as u64
}

fn main() {
    println!("=== Granular LiveSet Transition Benchmark ===\n");
    
    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);
    
    const RUNS: usize = 100;
    let mut timer = GranularTimer::new();
    let mut total_times = Vec::new();
    
    for i in 0..RUNS {
        let mut state = GameState::default();
        setup_liveset_state(&mut state, &deck, &lives, &energy);
        
        let total_ns = run_full_liveset_transition(&mut state, &db, &mut timer);
        total_times.push(total_ns);
        
        if i < 5 || i == RUNS - 1 {
            let phase_str = match state.phase {
                Phase::Main => "Main",
                Phase::Terminal => "Terminal",
                _ => "Other",
            };
            println!("Run {:>3}: total={:>6}μs -> {}", i, total_ns / 1000, phase_str);
        }
    }
    
    timer.print_stats();
    
    if !total_times.is_empty() {
        let total_sum: u64 = total_times.iter().sum();
        let avg = total_sum / total_times.len() as u64;
        let max = *total_times.iter().max().unwrap();
        let min = *total_times.iter().min().unwrap();
        println!("\n=== LiveSet:step Summary ===");
        println!("Runs:    {}", total_times.len());
        println!("Min:     {}μs", min / 1000);
        println!("Max:     {}μs", max / 1000);
        println!("Avg:     {}μs", avg / 1000);
        println!("Total:   {}μs", total_sum / 1000);
    }
}
