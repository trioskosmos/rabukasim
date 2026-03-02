use engine_rust::core::logic::{GameState, ACTION_SPACE};
use engine_rust::test_helpers::load_real_db;
use std::time::{Instant, Duration};

fn main() {
    println!("=== Detailed CPU Profiler (ST) ===");
    let db = load_real_db();
    
    let mut initial_state = GameState::default();
    let p_main = db.members.keys().take(50).cloned().collect::<Vec<i32>>();
    let energy_ids = db.energy_db.keys().take(10).cloned().collect::<Vec<i32>>();
    
    initial_state.initialize_game(
        p_main.clone(), p_main.clone(), 
        energy_ids.clone(), energy_ids.clone(), 
        Vec::new(), Vec::new()
    );
    initial_state.ui.silent = true;
    initial_state.phase = engine_rust::core::logic::Phase::Main;

    let mut clone_time = Duration::ZERO;
    let mut gen_time = Duration::ZERO;
    let mut step_time = Duration::ZERO;
    let mut action_time = Duration::ZERO;
    let mut games = 0;
    let mut steps_total = 0;

    let total_start = Instant::now();
    let bench_duration = Duration::from_secs(10);
    let mut mask = vec![false; ACTION_SPACE];
    let mut rng_state = 12345u64;

    while total_start.elapsed() < bench_duration {
        let t_clone = Instant::now();
        let mut sim = initial_state.clone();
        clone_time += t_clone.elapsed();

        let mut steps = 0;
        while !sim.is_terminal() && steps < 1000 {
            // Action Generation
            let t_gen = Instant::now();
            mask.fill(false);
            sim.get_legal_actions_into(&db, sim.current_player as usize, &mut mask);
            gen_time += t_gen.elapsed();

            // Action Selection
            let t_action = Instant::now();
            let mut valid_actions = smallvec::SmallVec::<[i32; 64]>::new();
            for (i, &b) in mask.iter().enumerate() {
                if b { valid_actions.push(i as i32); }
            }
            if valid_actions.is_empty() { break; }
            
            rng_state ^= rng_state << 13;
            rng_state ^= rng_state >> 17;
            rng_state ^= rng_state << 5;
            let action = valid_actions[(rng_state as usize) % valid_actions.len()];
            action_time += t_action.elapsed();

            // Step
            let t_step = Instant::now();
            let _ = sim.step(&db, action);
            step_time += t_step.elapsed();
            
            steps += 1;
        }
        steps_total += steps;
        games += 1;
    }

    let elapsed = total_start.elapsed().as_secs_f64();
    println!("Elapsed:      {:.2}s", elapsed);
    println!("Games:        {}", games);
    println!("Steps:        {}", steps_total);
    println!("Games/sec:    {:.2}", games as f64 / elapsed);
    println!("Steps/sec:    {:.2}", steps_total as f64 / elapsed);
    println!("\n--- Breakdown ---");
    println!("Clone Time:   {:.4}s ({:.1}%)", clone_time.as_secs_f64(), (clone_time.as_secs_f64() / elapsed) * 100.0);
    println!("Gen Time:     {:.4}s ({:.1}%)", gen_time.as_secs_f64(), (gen_time.as_secs_f64() / elapsed) * 100.0);
    println!("Action Time:  {:.4}s ({:.1}%)", action_time.as_secs_f64(), (action_time.as_secs_f64() / elapsed) * 100.0);
    println!("Step Time:    {:.4}s ({:.1}%)", step_time.as_secs_f64(), (step_time.as_secs_f64() / elapsed) * 100.0);
    println!("Other Time:   {:.4}s", elapsed - (clone_time + gen_time + action_time + step_time).as_secs_f64());
}
