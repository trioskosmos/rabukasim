use engine_rust::core::enums::*;
use engine_rust::core::logic::*;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::test_helpers::*;
use std::time::Instant;

#[test]
fn benchmark_sequencer_speed() {
    // Initialize DB
    let db = load_real_db();
    
    // Initialize State
    let mut state = GameState::default();
    state.players[0].player_id = 0;
    state.players[1].player_id = 1;
    state.phase = Phase::Main;
    state.current_player = 0;
    state.turn = 5;

    // Branching-heavy hand
    let mut hand = Vec::new();
    for i in 0..10 {
        hand.push(9 + i); 
    }
    state.set_hand(0, &hand);
    
    // Lives
    state.set_live(0, 0, 53301);
    state.set_live(0, 1, 57397);
    state.set_live(0, 2, 53468);
    
    // Abundant energy
    for _ in 0..20 {
        state.players[0].push_energy_card(9, false);
    }

    println!("Starting 100-iteration benchmark...");
    
    std::env::set_var("TURNSEQ_VANILLA_EXACT_THRESHOLD", "10000000");
    std::env::set_var("TURNSEQ_EXACT_THRESHOLD", "10000000");
    std::env::set_var("TURNSEQ_PROGRESS", "0");

    let iterations = 100;
    let mut total_evals = 0;
    let start = Instant::now();
    for _ in 0..iterations {
        let (_seq, _val, _breakdown, evals) = TurnSequencer::plan_full_turn(&state, &db);
        total_evals += evals;
    }
    let duration = start.elapsed();

    println!("Benchmark finished.");
    println!("Total iterations: {}", iterations);
    println!("Total evaluations: {}", total_evals);
    println!("Total duration: {:?}", duration);
    println!("Avg duration per search: {:?}", duration / iterations as u32);
    if duration.as_secs_f64() > 0.0 {
        println!("Nodes/sec: {:.2}", total_evals as f64 / duration.as_secs_f64());
    }
    
    assert!(total_evals > 0);
}
