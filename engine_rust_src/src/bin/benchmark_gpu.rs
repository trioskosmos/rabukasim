use std::time::Instant;
use engine_rust::core::logic::{GameState, CardDatabase};
// use engine_rust::core::enums::Phase;
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_conversions::GpuConverter;
// use rand::prelude::*;
// use rand::rngs::SmallRng;

fn run_benchmark() {
    println!("Initializing GPU Benchmark...");
    println!("GpuGameState size: {} bytes", std::mem::size_of::<engine_rust::core::gpu_state::GpuGameState>());

    // 1. Setup real database for GPU
    let json_path = "../data/cards_compiled.json";
    let json_str = std::fs::read_to_string(json_path).expect("Failed to read cards JSON");
    let db = CardDatabase::from_json(&json_str).expect("Failed to parse JSON");
    println!("Database loaded. Members: {}", db.members.len());

    let (stats, bytecode) = db.convert_to_gpu();

    let mut state = GameState::default();
    // Initialize a realistic state
    let all_members: Vec<i32> = db.members.keys().map(|&k| k as i32).collect();
    let all_lives: Vec<i32> = db.lives.keys().map(|&k| k as i32).collect();

    let mut p0_main: Vec<i32> = all_members.iter().take(48).cloned().collect();
    p0_main.extend(all_lives.iter().take(12).cloned());
    let mut p1_main: Vec<i32> = all_members.iter().skip(48).take(48).cloned().collect();
    p1_main.extend(all_lives.iter().skip(12).take(12).cloned());

    state.initialize_game(
        p0_main,
        p1_main,
        vec![], vec![],
        Vec::new(), Vec::new(),
    );
    state.turn = 10;
    state.phase = engine_rust::core::logic::Phase::Main;
    let state_gpu = state.to_gpu(&db);

    // 2. CPU Benchmark (Latency/Serial)
    let _iterations = 1000;
    /*
    println!("Benchmarking CPU: {} random rollouts (depth 100)...", iterations);
    let start_cpu = Instant::now();
    let mut rng = rand::rngs::SmallRng::from_os_rng();
    for _ in 0..iterations {
        let mut sim_state = state.clone();
        for _ in 0..100 {
            let mut legal = smallvec::SmallVec::<[i32; 32]>::new();
            sim_state.generate_legal_actions(&db, sim_state.current_player as usize, &mut legal);
            if legal.is_empty() { break; }
            use rand::seq::IndexedRandom;
            let action = *legal.choose(&mut rng).unwrap();
            let _ = sim_state.step(&db, action);
        }
        std::hint::black_box(&sim_state);
    }
    let duration_cpu = start_cpu.elapsed();
    println!("CPU Total: {:.4} ms", duration_cpu.as_secs_f64() * 1000.0);
    println!("CPU Latency: {:.4} ms per rollout", duration_cpu.as_secs_f64() * 1000.0 / iterations as f64);
    */
    let _cpu_throughput = 10000.0; // dummy

    for backend in [wgpu::Backends::VULKAN] {
        println!("\n=== TESTING BACKEND: {:?} ===", backend);

        let manager = match GpuManager::new(&stats, &bytecode, backend) {
            Some(m) => m,
            None => {
                println!("Backend {:?} not supported. Skipping.", backend);
                continue;
            }
        };

        for &gpu_batch_size in &[100, 500, 1_000, 2_500, 5_000, 10_000] {
            println!("\nTesting Batch Size: {}", gpu_batch_size);
            let mut batch = Vec::with_capacity(gpu_batch_size);
            for _ in 0..gpu_batch_size {
                batch.push(state_gpu.clone());
            }

            let mut results = vec![state_gpu.clone(); gpu_batch_size];
            let start_gpu = Instant::now();
            manager.run_simulations_chunked(&batch, &mut results, 100_000);
            let duration_gpu = start_gpu.elapsed();

            println!("  Time: {:.4} ms", duration_gpu.as_secs_f64() * 1000.0);
            let gpu_throughput = gpu_batch_size as f64 / duration_gpu.as_secs_f64();
            println!("  Throughput: {:.0} sims/sec", gpu_throughput);
        }

        // --- 10 x 10k Batch Test ---
        let batch_size = 10_000;
        let num_batches = 10;
        println!("\n=== Testing Sequential Batching ({} batches of {}) ===", num_batches, batch_size);
        let mut total_latency_ms = 0.0;
        let mut overall_start = Instant::now();

        for i in 0..num_batches {
            let mut batch = Vec::with_capacity(batch_size);
            for _ in 0..batch_size {
                batch.push(state_gpu.clone());
            }
            let mut results = vec![state_gpu.clone(); batch_size];
            let start_batch = Instant::now();
            manager.run_simulations_chunked(&batch, &mut results, 100_000);
            total_latency_ms += start_batch.elapsed().as_secs_f64() * 1000.0;
        }
        let overall_duration = overall_start.elapsed();
        let total_sims = batch_size * num_batches;

        println!("  Sum of Individual Latencies: {:.4} ms", total_latency_ms);
        println!("  Overall Wall-clock Time: {:.4} ms", overall_duration.as_secs_f64() * 1000.0);
        println!("  Avg Time per 10k batch:  {:.4} ms", total_latency_ms / (num_batches as f64));
        println!("  Overall Throughput: {:.0} sims/sec", total_sims as f64 / overall_duration.as_secs_f64());
    }
}

fn main() {
    let builder = std::thread::Builder::new()
        .name("benchmark_gpu_thread".into())
        .stack_size(8 * 1024 * 1024); // 8MB stack size to prevent Naga stack overflow
    let handler = builder.spawn(|| {
        run_benchmark();
    }).unwrap();
    handler.join().unwrap();
}
