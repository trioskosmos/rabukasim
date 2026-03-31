//! Ultra-Granular Diagnostic Benchmark - Tracks cards/opcodes causing slowdowns

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
    PerfP1Calc,
    PerfP2Calc,
    LiveResultFinalize,
}

struct DiagnosticTimer {
    times: HashMap<Metric, Vec<u64>>,
    // Track which cards are on stage during slow calls
    slow_p1_cards: Vec<(u64, [i32; 3])>, // (time_ns, stage_cards)
    slow_p2_cards: Vec<(u64, [i32; 3])>,
    // Track live zone cards during slow calls
    slow_p1_lives: Vec<(u64, [i32; 3])>,
    slow_p2_lives: Vec<(u64, [i32; 3])>,
    // Yell cards during slow calls
    slow_p1_yells: Vec<(u64, Vec<i32>)>,
    slow_p2_yells: Vec<(u64, Vec<i32>)>,
}

impl DiagnosticTimer {
    fn new() -> Self {
        let mut times = HashMap::new();
        for m in [Metric::PerfP1Calc, Metric::PerfP2Calc, Metric::LiveResultFinalize] {
            times.insert(m, Vec::new());
        }
        Self {
            times,
            slow_p1_cards: Vec::new(),
            slow_p2_cards: Vec::new(),
            slow_p1_lives: Vec::new(),
            slow_p2_lives: Vec::new(),
            slow_p1_yells: Vec::new(),
            slow_p2_yells: Vec::new(),
        }
    }

    fn record_perf(&mut self, is_p1: bool, ns: u64, stage: [i32; 3], lives: [i32; 3], yells: Vec<i32>) {
        let metric = if is_p1 { Metric::PerfP1Calc } else { Metric::PerfP2Calc };
        self.times.get_mut(&metric).unwrap().push(ns);
        
        // Only record board state for slow calls (>100μs)
        if ns > 100_000 {
            if is_p1 {
                self.slow_p1_cards.push((ns, stage));
                self.slow_p1_lives.push((ns, lives));
                self.slow_p1_yells.push((ns, yells));
            } else {
                self.slow_p2_cards.push((ns, stage));
                self.slow_p2_lives.push((ns, lives));
                self.slow_p2_yells.push((ns, yells));
            }
        }
    }

    fn print(&self, db: &CardDatabase) {
        println!("\n=== Diagnostic Timing ===");
        println!("{:<20} {:>6} {:>10} {:>10} {:>10}", "Metric", "N", "Avg(μs)", "Max(μs)", "Total(μs)");
        println!("{}", "-".repeat(65));
        
        for (metric, times) in &self.times {
            if times.is_empty() { continue; }
            let sum: u64 = times.iter().sum();
            let avg = sum / times.len() as u64;
            let max = *times.iter().max().unwrap();
            println!("{:<20?} {:>6} {:>10.2} {:>10.2} {:>10.2}", 
                metric, times.len(), avg as f64 / 1000.0, max as f64 / 1000.0, sum as f64 / 1000.0);
        }
        
        // Print slowest board states
        self.print_slow_states("P1 Performance", &self.slow_p1_cards, &self.slow_p1_lives, &self.slow_p1_yells, db);
        self.print_slow_states("P2 Performance", &self.slow_p2_cards, &self.slow_p2_lives, &self.slow_p2_yells, db);
    }
    
    fn print_slow_states(&self, label: &str, cards: &[(u64, [i32; 3])], lives: &[(u64, [i32; 3])], yells: &[(u64, Vec<i32>)], db: &CardDatabase) {
        if cards.is_empty() { return; }
        
        println!("\n=== Slowest {} Calls (showing board state) ===", label);
        println!("{:<10} {:<30} {:<30} {:<30}", "Time(μs)", "Stage Cards", "Live Cards", "Yell Cards");
        println!("{}", "-".repeat(100));
        
        // Get indices of slowest calls
        let mut indexed: Vec<(usize, u64)> = cards.iter().enumerate().map(|(i, (t, _))| (i, *t)).collect();
        indexed.sort_by(|a, b| b.1.cmp(&a.1)); // Descending
        
        for (idx, time_ns) in indexed.iter().take(10) {
            let stage = &cards[*idx].1;
            let live = &lives[*idx].1;
            let yell = &yells[*idx].1;
            
            let stage_names: Vec<String> = stage.iter().map(|&cid| {
                if cid < 0 { "Empty".to_string() }
                else { db.get_member(cid).map(|m| m.name.clone()).unwrap_or_else(|| format!("Card{}", cid)) }
            }).collect();
            
            let live_names: Vec<String> = live.iter().map(|&cid| {
                if cid < 0 { "Empty".to_string() }
                else { db.get_live(cid).map(|l| l.name.clone()).unwrap_or_else(|| format!("Live{}", cid)) }
            }).collect();
            
            let yell_names: Vec<String> = yell.iter().map(|&cid| {
                db.get_member(cid).map(|m| m.name.clone()).unwrap_or_else(|| format!("Yell{}", cid))
            }).collect();
            
            println!("{:<10} {:<30} {:<30} {:<30}", 
                time_ns / 1000,
                stage_names.join(", "),
                live_names.join(", "),
                if yell_names.is_empty() { "None".to_string() } else { yell_names.join(", ") }
            );
        }
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

fn run_diagnostic(state: &mut GameState, db: &CardDatabase, timer: &mut DiagnosticTimer) {
    // === P1 PASS ===
    let _ = state.step_internal(db, 0);
    
    // === auto_step ===
    diagnostic_auto_step(state, db, timer);
    
    // === P2 PASS (only if still in LiveSet) ===
    if state.phase == Phase::LiveSet && state.current_player == 1 {
        let _ = state.step_internal(db, 0);
        diagnostic_auto_step(state, db, timer);
    }
}

fn diagnostic_auto_step(state: &mut GameState, db: &CardDatabase, timer: &mut DiagnosticTimer) {
    let mut loop_count = 0;
    loop {
        state.check_win_condition();
        
        if state.phase == Phase::Terminal || state.phase == Phase::Response {
            break;
        }
        if !state.interaction_stack.is_empty() {
            break;
        }
        
        if !state.core.trigger_queue.is_empty() {
            state.process_trigger_queue(db);
            if state.phase == Phase::Response {
                break;
            }
            continue;
        }
        
        let old_phase = state.phase;
        let p_idx = state.current_player as usize;
        
        match state.phase {
            Phase::PerformanceP1 | Phase::PerformanceP2 => {
                let is_p1 = state.phase == Phase::PerformanceP1;
                
                // Capture board state BEFORE the call
                let stage = state.players[p_idx].stage;
                let lives = state.players[p_idx].live_zone;
                let yells = state.players[p_idx].yell_cards.clone();
                
                let t = Instant::now();
                state.do_performance_phase(db);
                let elapsed = t.elapsed().as_nanos() as u64;
                
                timer.record_perf(is_p1, elapsed, stage, lives, yells.to_vec());
            }
            Phase::LiveResult => {
                let t = Instant::now();
                if !state.live_result_selection_pending {
                    let _ = state.handle_liveresult(db, 0);
                }
                let elapsed = t.elapsed().as_nanos() as u64;
                timer.times.get_mut(&Metric::LiveResultFinalize).unwrap().push(elapsed);
            }
            Phase::Active => {
                state.do_active_phase(db);
            }
            Phase::Energy => {
                state.do_energy_phase();
            }
            Phase::Draw => {
                state.do_draw_phase(db);
            }
            _ => break,
        }
        
        if state.phase == old_phase && state.core.trigger_queue.is_empty() {
            break;
        }
        loop_count += 1;
        if loop_count > 40 { break; }
    }
}

fn main() {
    println!("=== Diagnostic Performance Analysis ===\n");
    
    let db = load_db();
    let (deck, lives, energy) = build_decks(&db);
    
    const RUNS: usize = 100;
    let mut timer = DiagnosticTimer::new();
    
    for i in 0..RUNS {
        let mut state = GameState::default();
        setup(&mut state, &deck, &lives, &energy);
        run_diagnostic(&mut state, &db, &mut timer);
        
        if i < 3 || (i < 20 && i % 5 == 0) || i == RUNS - 1 {
            println!("Run {} complete", i);
        }
    }
    
    timer.print(&db);
}
