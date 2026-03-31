use std::time::Instant;
use engine_rust::core::logic::game::GameState;
use engine_rust::core::logic::card_db::CardDatabase;
use engine_rust::core::enums::Phase;

#[derive(Debug, Clone, Copy, Hash, PartialEq, Eq)]
enum MicroPhase {
    HandleLivesetCall,
    AutoStepEntry,
    AutoStepLoopStart,
    CheckWinCondition,
    TriggerQueueCheck,
    TriggerProcessing,
    PhaseTransition,
    SyncStats,
    Other,
}

struct MicroTimer {
    times: std::collections::HashMap<MicroPhase, Vec<u64>>,
}

impl MicroTimer {
    fn new() -> Self {
        let mut times = std::collections::HashMap::new();
        for phase in [
            MicroPhase::HandleLivesetCall,
            MicroPhase::AutoStepEntry,
            MicroPhase::AutoStepLoopStart,
            MicroPhase::CheckWinCondition,
            MicroPhase::TriggerQueueCheck,
            MicroPhase::TriggerProcessing,
            MicroPhase::PhaseTransition,
            MicroPhase::SyncStats,
            MicroPhase::Other,
        ] {
            times.insert(phase, Vec::new());
        }
        Self { times }
    }

    fn record(&mut self, phase: MicroPhase, ns: u64) {
        self.times.get_mut(&phase).unwrap().push(ns);
    }

    fn print_stats(&self) {
        println!("\n=== Micro LiveSet Timing Analysis ===");
        println!("{:<20} {:>8} {:>10} {:>10} {:>10}", "Phase", "Count", "Total(ns)", "Avg(μs)", "Max(μs)");
        println!("{}", "-".repeat(68));
        
        let mut total_all: u64 = 0;
        for (phase, times) in &self.times {
            if times.is_empty() { continue; }
            let count = times.len();
            let total: u64 = times.iter().sum();
            let avg = total / count as u64;
            let max = *times.iter().max().unwrap();
            total_all += total;
            println!("{:<20?} {:>8} {:>10} {:>10.2} {:>10.2}", 
                phase, count, total, avg as f64 / 1000.0, max as f64 / 1000.0);
        }
        println!("{}", "-".repeat(68));
        println!("{:<20} {:>8} {:>10.2}μs", "TOTAL", "", total_all as f64 / 1000.0);
    }
}

fn load_db() -> CardDatabase {
    let db_path = "../data/cards_compiled.json";
    let json_content = std::fs::read_to_string(db_path).expect("Failed to read database file");
    CardDatabase::from_json(&json_content).expect("Failed to parse database")
}

fn setup_liveset_state(state: &mut GameState, deck: &[i32], lives: &[i32], energy: &[i32]) {
    state.initialize_game(deck.to_vec(), deck.to_vec(), energy.to_vec(), energy.to_vec(), lives.to_vec(), lives.to_vec());
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    state.ui.headless = true;
    state.ui.silent = true;
    
    // Set up some cards in stage and live zone
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

fn run_micro_liveset_analysis(
    state: &mut GameState,
    db: &CardDatabase,
    timer: &mut MicroTimer,
) -> u64 {
    let start = Instant::now();
    
    // Measure handle_liveset call specifically
    let t = Instant::now();
    let _old_phase = state.phase;
    let _ = state.step_internal(db, 0); // action=0 (pass)
    let handle_liveset_ns = t.elapsed().as_nanos() as u64;
    timer.record(MicroPhase::HandleLivesetCall, handle_liveset_ns);
    
    // Now measure auto_step components
    let t = Instant::now();
    state.auto_step(db);
    let auto_step_ns = t.elapsed().as_nanos() as u64;
    timer.record(MicroPhase::AutoStepEntry, auto_step_ns);
    
    start.elapsed().as_nanos() as u64
}

fn main() {
    println!("=== Micro LiveSet Performance Analysis ===\n");
    
    let db = load_db();
    let (deck, lives, energy) = (
        vec![1001, 1002, 1003, 2001, 2002, 2003, 3001, 3002, 3003],
        vec![4001, 4002, 4003, 4004, 4005, 4006],
        vec![5001, 5002, 5003, 5004, 5005, 5006],
    );
    
    const RUNS: usize = 50;
    let mut timer = MicroTimer::new();
    let mut total_times = Vec::new();
    
    for i in 0..RUNS {
        let mut state = GameState::default();
        setup_liveset_state(&mut state, &deck, &lives, &energy);
        
        let total_ns = run_micro_liveset_analysis(&mut state, &db, &mut timer);
        total_times.push(total_ns);
        
        if i < 5 {
            println!("Run {}: total={:>5}μs -> {:?}", 
                i, total_ns / 1000, state.phase);
        }
        if i == RUNS - 1 {
            println!("Run {}: total={:>5}μs -> {:?}", 
                i, total_ns / 1000, state.phase);
        }
    }
    
    timer.print_stats();
    
    total_times.sort();
    let min = total_times[0];
    let max = total_times[RUNS - 1];
    let avg = total_times.iter().sum::<u64>() / RUNS as u64;
    
    println!("\n=== LiveSet:step Summary ===");
    println!("Runs:    {}", RUNS);
    println!("Min:     {}μs", min / 1000);
    println!("Max:     {}μs", max / 1000);
    println!("Avg:     {}μs", avg / 1000);
    println!("Total:   {}μs", total_times.iter().sum::<u64>() / 1000);
}
