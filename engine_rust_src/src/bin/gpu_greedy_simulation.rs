use std::sync::Arc;
use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_state::GpuGameState;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::test_helpers::load_real_db;
use pollster::block_on;

fn parse_deck(path: &str, db: &CardDatabase) -> Vec<i32> {
    let content = std::fs::read_to_string(path).expect("Failed to read deck file");
    let mut ids = Vec::new();
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') { continue; }
        let parts: Vec<&str> = line.split('x').map(|s| s.trim()).collect();
        let no = parts[0];
        let count = if parts.len() > 1 { parts[1].parse::<usize>().unwrap_or(1) } else { 1 };
        if let Some(&id) = db.card_no_to_id.get(no) {
            for _ in 0..count { ids.push(id); }
        }
    }
    ids
}

async fn real_main() {
    println!("=== GPU Greedy Simulation Runner ===");
    let db = load_real_db();
    let (stats, bytecode) = db.convert_to_gpu();
    let manager = Arc::new(GpuManager::new(&stats, &bytecode, wgpu::Backends::all()).expect("Failed to init GPU"));

    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() { "ai/decks/muse_cup.txt" } else { "../ai/decks/muse_cup.txt" };
    let p0_deck = parse_deck(deck_path, &db);
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    let mut initial_state = GameState::default();
    initial_state.initialize_game(p0_deck.clone(), p0_deck.clone(), energy_ids.clone(), energy_ids.clone(), Vec::new(), Vec::new());
    
    println!("Running 100 GPU Rollouts...");

    let batch_size = 100;
    let mut gpu_batch = vec![GpuGameState::default(); batch_size];
    let gpu_initial = initial_state.to_gpu(&db);

    for i in 0..batch_size {
        gpu_batch[i] = gpu_initial.clone();
        gpu_batch[i].rng_state_lo = i as u32; 
        gpu_batch[i].rng_state_hi = 0xABCDEF01;
        gpu_batch[i].is_debug = 1; 
    }

    let mut results = vec![GpuGameState::default(); batch_size];
    manager.run_simulations_into(&gpu_batch, &mut results);

    let mut p0_wins = 0;
    let mut p1_wins = 0;
    let mut turn_counts = std::collections::HashMap::new();
    let mut step_counts = std::collections::HashMap::new();
    let mut min_steps = u32::MAX;
    let mut max_steps = 0;

    for r in &results {
        if r.player0.lives_cleared_count >= 3 { p0_wins += 1; }
        else if r.player1.lives_cleared_count >= 3 { p1_wins += 1; }
        
        *turn_counts.entry(r.turn).or_insert(0) += 1;
        let steps = r._pad_game[0];
        *step_counts.entry(steps).or_insert(0) += 1;
        min_steps = min_steps.min(steps);
        max_steps = max_steps.max(steps);
    }

    println!("\n--- Empirical Results (10k Parallel Games) ---");
    println!("P0 Win Rate: {:.2}%", (p0_wins as f32 / batch_size as f32) * 100.0);
    println!("P1 Win Rate: {:.2}%", (p1_wins as f32 / batch_size as f32) * 100.0);
    println!("Draw Rate:   {:.2}%", ((batch_size - p0_wins - p1_wins) as f32 / batch_size as f32) * 100.0);

    println!("\n--- Turn Count Distribution ---");
    let mut sorted_turns: Vec<_> = turn_counts.iter().collect();
    sorted_turns.sort_by_key(|a| a.0);
    for (turn, count) in sorted_turns {
        println!("Turn {:2}: {:5} games ({:>5.2}%)", turn, count, (*count as f32 / batch_size as f32) * 100.0);
    }

    println!("\n--- Step Count (Rollout Density) ---");
    println!("Min Steps: {}", min_steps);
    println!("Max Steps: {}", max_steps);
    println!("Avg Steps: {:.1}", results.iter().map(|r| r._pad_game[0] as f32).sum::<f32>() / batch_size as f32);
    
    println!("\n--- Sample Game Insights (Top 3) ---");
    for i in 0..3.min(batch_size) {
        let r = &results[i];
        println!("Game {}: Turns: {}, Steps: {}, Winner: {}, P0 Clear: {}, P1 Clear: {}", 
            i, r.turn, r._pad_game[0], r.winner, r.player0.lives_cleared_count, r.player1.lives_cleared_count);
        println!("  P0 Telemetry: {} Performances, {} Needed Hearts, {} Total Yells", 
            r._pad_game[1], r._pad_game[2], r._pad_game[3]);
        println!("  P0 Board Blades: {}, Avg Hearts: {:?}", r.player0.board_blades, r.player0.avg_hearts);
    }
}

fn main() {
    let builder = std::thread::Builder::new()
        .name("gpu-sim-main".into())
        .stack_size(32 * 1024 * 1024);
    let handler = builder.spawn(|| {
        block_on(real_main());
    }).expect("Failed to spawn main thread");
    handler.join().expect("Main thread panicked");
}
