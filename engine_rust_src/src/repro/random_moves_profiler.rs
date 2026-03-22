use engine_rust::core::enums::*;
use engine_rust::core::logic::*;
use engine_rust::test_helpers::*;
use std::time::{Instant, Duration};
use rand::prelude::*;
use rand::rngs::SmallRng;
use rand::SeedableRng;

#[test]
fn benchmark_random_moves() {
    // 1. Initialize DB
    let db = load_real_db();
    
    // 2. Setup Measurement
    let mut total_steps = 0;
    let mut total_action_gen_time = Duration::ZERO;
    let mut total_execution_time = Duration::ZERO;
    let mut total_auto_step_time = Duration::ZERO;
    
    let target_steps = 50000;
    let mut rng = SmallRng::from_os_rng();
    
    println!("Starting Random Moves Profiler (Target: {} steps)...", target_steps);
    
    let start_overall = Instant::now();
    
    while total_steps < target_steps {
        // Initialize State for a new game session if terminal or just starting
        let mut state = GameState::default();
        state.ui.silent = true;
        state.debug.debug_mode = false;
        
        // Randomize player decks if possible (or just use default)
        // Here we just use the default setup for simplicity
        
        while state.phase != Phase::Terminal && total_steps < target_steps {
            let p_idx = state.current_player as usize;
            
            // Measure Action Generation
            let t_gen_start = Instant::now();
            let mut actions: Vec<i32> = Vec::new();
            state.generate_legal_actions(db, p_idx, &mut actions);
            total_action_gen_time += t_gen_start.elapsed();
            
            if actions.is_empty() {
                // If no actions and not terminal, we might be stuck or need a dummy step
                // But usually this shouldn't happen with correct engine logic
                break;
            }
            
            // Pick a random action
            let action = actions[rng.random_range(0..actions.len())];
            
            // Measure Execution
            let t_exec_start = Instant::now();
            // We use step_internal + auto_step to profile them separately if we want,
            // but state.step() does both. Let's profile state.step() first.
            let _ = state.step(db, action);
            total_execution_time += t_exec_start.elapsed();
            
            total_steps += 1;
            
            if total_steps % 5000 == 0 {
                let elapsed = start_overall.elapsed().as_secs_f64();
                println!("Progress: {}/{} steps ({:.1} SPS)", 
                    total_steps, target_steps, total_steps as f64 / elapsed);
            }
        }
    }
    
    let overall_duration = start_overall.elapsed();
    let overall_secs = overall_duration.as_secs_f64();
    let sps = total_steps as f64 / overall_secs;
    
    println!("\n=== Profiling Results ===");
    println!("Total Steps:      {}", total_steps);
    println!("Total Time:       {:.3}s", overall_secs);
    println!("Steps Per Second: {:.1}", sps);
    println!("--------------------------");
    println!("Action Generation: {:.3}s ({:>5.1}%)", 
        total_action_gen_time.as_secs_f64(), 
        (total_action_gen_time.as_secs_f64() / overall_secs) * 100.0);
    println!("Step Execution:   {:.3}s ({:>5.1}%)", 
        total_execution_time.as_secs_f64(), 
        (total_execution_time.as_secs_f64() / overall_secs) * 100.0);
    
    let other_time = overall_secs - total_action_gen_time.as_secs_f64() - total_execution_time.as_secs_f64();
    println!("Other Overlay:    {:.3}s ({:>5.1}%)", 
        other_time, (other_time / overall_secs) * 100.0);
    
    assert!(total_steps >= target_steps);
}
