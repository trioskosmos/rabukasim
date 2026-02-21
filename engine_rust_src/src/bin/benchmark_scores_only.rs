use std::time::Instant;
use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_conversions::GpuConverter;

fn run_benchmark() {
    println!("=== GPU Score-Only Readback Benchmark ===");

    // 1. Setup Data
    let json_path = "../data/cards_compiled.json";
    let json_str = std::fs::read_to_string(json_path).expect("Failed to read cards JSON");
    let db = CardDatabase::from_json(&json_str).expect("Failed to parse JSON");
    let (stats, bytecode) = db.convert_to_gpu();

    let mut state = GameState::default();
    let all_members: Vec<i32> = db.members.keys().map(|&k| k as i32).collect();
    let all_lives: Vec<i32> = db.lives.keys().map(|&k| k as i32).collect();

    let mut p0_main: Vec<i32> = all_members.iter().take(48).cloned().collect();
    p0_main.extend(all_lives.iter().take(12).cloned());
    let mut p1_main: Vec<i32> = all_members.iter().skip(48).take(48).cloned().collect();
    p1_main.extend(all_lives.iter().skip(12).take(12).cloned());

    state.initialize_game(p0_main, p1_main, vec![], vec![], Vec::new(), Vec::new());
    state.turn = 10;
    state.phase = engine_rust::core::logic::Phase::Main;
    let state_gpu = state.to_gpu(&db);

    let manager = GpuManager::new(&stats, &bytecode, wgpu::Backends::VULKAN).expect("Failed to init GPU");

    let batch_size = 100_000;
    println!("\nBatch Size: {}", batch_size);

    let mut batch = vec![state_gpu.clone(); batch_size];
    
    // Test 1: Full State Readback
    {
        let mut results = vec![state_gpu.clone(); batch_size];
        let start = Instant::now();
        manager.run_simulations_into(&batch, &mut results);
        let duration = start.elapsed();
        println!("Full State Readback:");
        println!("  Time: {:.2} ms", duration.as_secs_f64() * 1000.0);
        println!("  Throughput: {:.0} sims/sec", batch_size as f64 / duration.as_secs_f64());
    }

    // Test 2: Score-Only Readback
    {
        let mut scores = vec![0.0f32; batch_size];
        let start = Instant::now();
        manager.run_simulations_scores(&batch, &mut scores);
        let duration = start.elapsed();
        println!("\nScore-Only Readback:");
        println!("  Time: {:.2} ms", duration.as_secs_f64() * 1000.0);
        println!("  Throughput: {:.0} sims/sec", batch_size as f64 / duration.as_secs_f64());
        
        if batch_size > 0 {
            println!("  Sample Score[0]: {:.4}", scores[0]);
        }
    }
}

fn main() {
    let builder = std::thread::Builder::new()
        .name("benchmark_scores_thread".into())
        .stack_size(16 * 1024 * 1024);
    let handler = builder.spawn(|| {
        run_benchmark();
    }).unwrap();
    handler.join().unwrap();
}
