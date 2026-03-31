//! Ultra-Granular Phase Benchmark - Instruments inside auto_step

use engine_rust::core::logic::{CardDatabase, GameState, MainPhaseController, Phase};
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
enum Metric {
    // LiveSet
    LiveSetPass,
    // Performance phases (inside auto_step)
    PerfP1Reveal,
    PerfP1Yell,
    PerfP1Calc,
    PerfP2Reveal,
    PerfP2Yell,
    PerfP2Calc,
    // LiveResult
    LiveResultScore,
    LiveResultTriggers,
    LiveResultFinalize,
    // Turn setup
    ActiveUntap,
    ActiveTriggers,
    EnergyDraw,
    DrawCard,
    DrawTriggers,
    // Sync
    SyncStats,
    // Overhead
    TriggerQueue,
    CheckWin,
    Other,
}

struct Timer {
    times: HashMap<Metric, Vec<u64>>,
}

impl Timer {
    fn new() -> Self {
        let mut times = HashMap::new();
        for m in [
            Metric::LiveSetPass,
            Metric::PerfP1Reveal, Metric::PerfP1Yell, Metric::PerfP1Calc,
            Metric::PerfP2Reveal, Metric::PerfP2Yell, Metric::PerfP2Calc,
            Metric::LiveResultScore, Metric::LiveResultTriggers, Metric::LiveResultFinalize,
            Metric::ActiveUntap, Metric::ActiveTriggers,
            Metric::EnergyDraw,
            Metric::DrawCard, Metric::DrawTriggers,
            Metric::SyncStats,
            Metric::TriggerQueue, Metric::CheckWin, Metric::Other,
        ] {
            times.insert(m, Vec::new());
        }
        Self { times }
    }

    fn record(&mut self, m: Metric, ns: u64) {
        self.times.get_mut(&m).unwrap().push(ns);
    }

    fn print(&self) {
        println!("\n=== Ultra-Granular Timing ===");
        println!("{:<20} {:>6} {:>10} {:>10} {:>10}", "Metric", "N", "Avg(μs)", "Max(μs)", "Total(μs)");
        println!("{}", "-".repeat(65));
        
        let mut total = 0u64;
        let items: Vec<_> = self.times.iter()
            .filter(|(_, v)| !v.is_empty())
            .map(|(k, v)| {
                let sum: u64 = v.iter().sum();
                (k, v.len(), sum / v.len() as u64, *v.iter().max().unwrap(), sum)
            })
            .collect();
        
        for (k, n, avg, max, sum) in items {
            total += sum;
            println!("{:<20?} {:>6} {:>10.2} {:>10.2} {:>10.2}", 
                k, n, avg as f64 / 1000.0, max as f64 / 1000.0, sum as f64 / 1000.0);
        }
        println!("{}", "-".repeat(65));
        println!("{:<20} {:>6} {:>10.2}μs", "TOTAL", "", total as f64 / 1000.0);
    }
}

fn setup(state: &mut GameState, deck: &[i32], lives: &[i32], energy: &[i32]) {
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

/// Instrumented version of the LiveSet transition
fn run_instrumented(state: &mut GameState, db: &CardDatabase, timer: &mut Timer) -> u64 {
    let start = Instant::now();
    
    // === P1 PASS ===
    let t = Instant::now();
    let _ = state.step_internal(db, 0);
    timer.record(Metric::LiveSetPass, t.elapsed().as_nanos() as u64);
    
    // === auto_step ===
    instrumented_auto_step(state, db, timer);
    
    // === P2 PASS (only if still in LiveSet) ===
    if state.phase == Phase::LiveSet && state.current_player == 1 {
        let t = Instant::now();
        let _ = state.step_internal(db, 0);
        timer.record(Metric::LiveSetPass, t.elapsed().as_nanos() as u64);
        
        // === auto_step (this is where the heavy work happens) ===
        instrumented_auto_step(state, db, timer);
    }
    
    start.elapsed().as_nanos() as u64
}

fn instrumented_auto_step(state: &mut GameState, db: &CardDatabase, timer: &mut Timer) {
    let mut loop_count = 0;
    loop {
        let t = Instant::now();
        state.check_win_condition();
        timer.record(Metric::CheckWin, t.elapsed().as_nanos() as u64);
        
        if state.phase == Phase::Terminal || state.phase == Phase::Response {
            break;
        }
        if !state.interaction_stack.is_empty() {
            break;
        }
        
        if !state.core.trigger_queue.is_empty() {
            let t = Instant::now();
            state.process_trigger_queue(db);
            timer.record(Metric::TriggerQueue, t.elapsed().as_nanos() as u64);
            if state.phase == Phase::Response {
                break;
            }
            continue;
        }
        
        let old_phase = state.phase;
        match state.phase {
            Phase::PerformanceP1 | Phase::PerformanceP2 => {
                instrumented_performance(state, db, timer, old_phase == Phase::PerformanceP1);
            }
            Phase::LiveResult => {
                instrumented_live_result(state, db, timer);
            }
            Phase::Active => {
                let t = Instant::now();
                state.do_active_phase(db);
                timer.record(Metric::ActiveUntap, t.elapsed().as_nanos() as u64);
            }
            Phase::Energy => {
                let t = Instant::now();
                state.do_energy_phase();
                timer.record(Metric::EnergyDraw, t.elapsed().as_nanos() as u64);
            }
            Phase::Draw => {
                let t = Instant::now();
                state.do_draw_phase(db);
                timer.record(Metric::DrawCard, t.elapsed().as_nanos() as u64);
            }
            _ => break,
        }
        
        if state.phase == old_phase && state.core.trigger_queue.is_empty() {
            if loop_count > 0 {
                let t = Instant::now();
                state.sync_all_stats(db);
                timer.record(Metric::SyncStats, t.elapsed().as_nanos() as u64);
            }
            break;
        }
        loop_count += 1;
        if loop_count > 40 { break; }
    }
}

fn instrumented_performance(state: &mut GameState, db: &CardDatabase, timer: &mut Timer, is_p1: bool) {
    let p_idx = state.current_player as usize;
    
    // Check fast path
    if state.players[p_idx].live_zone.iter().all(|&c| c < 0) {
        let t = Instant::now();
        // Just do phase advance
        state.do_performance_phase(db);
        let metric = if is_p1 { Metric::PerfP1Calc } else { Metric::PerfP2Calc };
        timer.record(metric, t.elapsed().as_nanos() as u64);
        return;
    }
    
    // Reveal phase
    if !state.performance_reveals_done[p_idx] {
        let t = Instant::now();
        // Minimal work for timing
        let metric = if is_p1 { Metric::PerfP1Reveal } else { Metric::PerfP2Reveal };
        timer.record(metric, t.elapsed().as_nanos() as u64);
    }
    
    // Yell phase  
    if !state.performance_yell_done[p_idx] {
        let t = Instant::now();
        let metric = if is_p1 { Metric::PerfP1Yell } else { Metric::PerfP2Yell };
        timer.record(metric, t.elapsed().as_nanos() as u64);
    }
    
    // Full calculation
    let t = Instant::now();
    state.do_performance_phase(db);
    let metric = if is_p1 { Metric::PerfP1Calc } else { Metric::PerfP2Calc };
    timer.record(metric, t.elapsed().as_nanos() as u64);
}

fn instrumented_live_result(state: &mut GameState, db: &CardDatabase, timer: &mut Timer) {
    // Score calculation
    let t = Instant::now();
    timer.record(Metric::LiveResultScore, t.elapsed().as_nanos() as u64);
    
    // Triggers
    if !state.live_result_triggers_done {
        let t = Instant::now();
        timer.record(Metric::LiveResultTriggers, t.elapsed().as_nanos() as u64);
    }
    
    // Finalize
    let t = Instant::now();
    if !state.live_result_selection_pending {
        let _ = state.handle_liveresult(db, 0);
    }
    timer.record(Metric::LiveResultFinalize, t.elapsed().as_nanos() as u64);
}

fn main() {
    println!("=== Ultra-Granular LiveSet Transition ===\n");
    
    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);
    
    const RUNS: usize = 100;
    let mut timer = Timer::new();
    let mut totals = Vec::new();
    
    for i in 0..RUNS {
        let mut state = GameState::default();
        setup(&mut state, &deck, &lives, &energy);
        
        let total = run_instrumented(&mut state, &db, &mut timer);
        totals.push(total);
        
        if i < 3 || (i < 20 && i % 5 == 0) || i == RUNS - 1 {
            println!("Run {:>3}: {:>6}μs", i, total / 1000);
        }
    }
    
    timer.print();
    
    if !totals.is_empty() {
        let sum: u64 = totals.iter().sum();
        let avg = sum / totals.len() as u64;
        let max = *totals.iter().max().unwrap();
        let min = *totals.iter().min().unwrap();
        
        println!("\n=== Summary ===");
        println!("Runs:  {}", totals.len());
        println!("Min:   {}μs", min / 1000);
        println!("Max:   {}μs", max / 1000);  
        println!("Avg:   {}μs", avg / 1000);
    }
}
