use std::sync::Arc;
use engine_rust::core::logic::{GameState, CardDatabase, Phase};
use engine_rust::core::mcts::{MCTS, SearchHorizon};
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::core::heuristics::OriginalHeuristic;

fn main() {
    println!("=== MCTS Tournament: CPU vs GPU (100ms limit) ===");

    // 1. Setup Database & Manager
    let json_path = if std::path::Path::new("data/cards_compiled.json").exists() {
        "data/cards_compiled.json"
    } else {
        "../data/cards_compiled.json"
    };
    println!("Loading database from: {}", json_path);
    let json_str = std::fs::read_to_string(json_path).expect("Failed to read cards JSON");
    let db = CardDatabase::from_json(&json_str).expect("Failed to parse JSON");
    let (stats, bytecode) = db.convert_to_gpu();

    println!("GpuGameState size: {} (expected 1608)", std::mem::size_of::<engine_rust::core::gpu_state::GpuGameState>());
    let gpu_manager = Arc::new(GpuManager::new(&stats, &bytecode, wgpu::Backends::VULKAN).expect("Failed to init GPU"));
    let heuristic = OriginalHeuristic::default();

    let mut gpu_wins = 0;
    let mut cpu_wins = 0;
    let mut draws = 0;
    let mut total_turns = 0;
    let mut total_gpu_sims: i64 = 0;
    let mut total_cpu_sims: i64 = 0;

    let num_games = 10;
    let timeout_sec = 0.1; // 0.1 seconds per move

    for game_id in 1..=num_games {
        println!("  Starting Game {}/{}...", game_id, num_games);
        // Setup Initial Game State
        let mut state = GameState::default();
        let mut all_members: Vec<i32> = db.members.keys().map(|&k| k as i32).collect();
        let mut all_lives: Vec<i32> = db.lives.keys().map(|&k| k as i32).collect();

        // SHUFFLE to avoid "dead" decks from first 50 cards
        use rand::seq::SliceRandom;
        let mut rng = rand::rng();
        all_members.shuffle(&mut rng);
        all_lives.shuffle(&mut rng);

        let mut p0_main: Vec<i32> = all_members.iter().take(20).cloned().collect();
        p0_main.extend(all_lives.iter().take(10).cloned());
        let mut p1_main: Vec<i32> = all_members.iter().skip(20).take(20).cloned().collect();
        p1_main.extend(all_lives.iter().skip(10).take(10).cloned());

        state.initialize_game(
            p0_main,
            p1_main,
            all_members.iter().take(6).cloned().collect(),
            all_members.iter().skip(20).take(6).cloned().collect(),
            Vec::new(), Vec::new(),
        );
        state.turn = 1;
        state.phase = Phase::Main;
        state.ui.silent = true;

        // GPU plays as Player 0 in even games, Player 1 in odd games
        let gpu_player_idx = (game_id % 2) as u8;

        let mut move_count = 0;
        while !state.is_terminal() && move_count < 1000 {
            let active_player = state.current_player;
            let is_gpu_turn = active_player == gpu_player_idx;

            if is_gpu_turn {
                let _gpu_state = state.to_gpu(&db);
                let gpu_mcts = MCTS::with_gpu(gpu_manager.clone(), 128);
                let suggestions = gpu_mcts.search_parallel(
                    &state, &db, 0, timeout_sec, SearchHorizon::GameEnd(), &heuristic, false
                );
                let visits: u32 = suggestions.iter().map(|s| s.2).sum();
                total_gpu_sims += visits as i64;
                let action = suggestions.first().map(|s| s.0).unwrap_or(0);
                let _ = state.step(&db, action);
            } else {
                let cpu_mcts = MCTS::new();
                let suggestions = cpu_mcts.search_parallel(
                    &state, &db, 0, timeout_sec, SearchHorizon::GameEnd(), &heuristic, false
                );
                let sims: u32 = suggestions.iter().map(|s| s.2).sum();
                total_cpu_sims += sims as i64;
                let action = suggestions.first().map(|s| s.0).unwrap_or(0);
                let _ = state.step(&db, action);
            }
            move_count += 1;
        }

        total_turns += state.turn;

        if state.is_terminal() {
            let winner = state.get_winner();
            if winner == gpu_player_idx as i32 {
                gpu_wins += 1;
            } else if winner == (1 - gpu_player_idx as i32) {
                cpu_wins += 1;
            } else {
                draws += 1;
            }
            println!("Game {} Result: Winner={} (GPUPidx={}) | Total Score: GPU={} CPU={} Draws={}",
                game_id, winner, gpu_player_idx, gpu_wins, cpu_wins, draws);
        } else {
            draws += 1;
        }
    }

    println!("\n=== Tournament Final Results ===");
    println!("GPU Wins: {}", gpu_wins);
    println!("CPU Wins: {}", cpu_wins);
    println!("Draws   : {}", draws);
    println!("Average Turns: {:.1}", total_turns as f32 / num_games as f32);
    println!("--------------------------------");
    println!("TOTAL CAPACITY DELTA (100ms actions):");
    println!("Total CPU Simulations : {}", total_cpu_sims);
    println!("Total GPU Simulations : {}", total_gpu_sims);
    println!("GPU ADVANTAGE         : {:.1}x", total_gpu_sims as f64 / total_cpu_sims.max(1) as f64);
}
