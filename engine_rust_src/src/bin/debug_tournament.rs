// use std::time::Duration;
use std::sync::Arc;
use engine_rust::core::logic::{GameState, CardDatabase, Phase};
use engine_rust::core::mcts::{MCTS, SearchHorizon};
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::core::heuristics::OriginalHeuristic;

fn main() {
    println!("=== MCTS Debug Tournament: CPU vs GPU (Verbose) ===");

    let json_path = if std::path::Path::new("data/cards_compiled.json").exists() {
        "data/cards_compiled.json"
    } else {
        "../data/cards_compiled.json"
    };
    println!("Loading database from: {}", json_path);
    let json_str = std::fs::read_to_string(json_path).expect("Failed to read cards JSON");
    let db = CardDatabase::from_json(&json_str).expect("Failed to parse JSON");
    let (stats, bytecode) = db.convert_to_gpu();

    let gpu_manager = Arc::new(GpuManager::new(&stats, &bytecode, wgpu::Backends::VULKAN).expect("Failed to init GPU"));
    let heuristic = OriginalHeuristic::default();

    let mut state = GameState::default();
    let mut all_members: Vec<i32> = db.members.keys().map(|&k| k as i32).collect();
    let mut all_lives: Vec<i32> = db.lives.keys().map(|&k| k as i32).collect();

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
    state.ui.silent = false; // ENABLE VERBOSE LOGGING
    let _gpu_state = state.to_gpu(&db);
    let timeout_sec = 0.1; // 100ms per move
    let gpu_player_idx = 1;

    let mut move_count = 0;
    while !state.is_terminal() && move_count < 1000 {
        let active_player = state.current_player;
        let is_gpu_turn = active_player == gpu_player_idx;

        println!("\n--- Move {} | Turn {} | Player {} ---", move_count, state.turn, active_player);

        if is_gpu_turn {
            let gpu_mcts = MCTS::with_gpu(gpu_manager.clone(), 512);
            let suggestions = gpu_mcts.search_parallel(
                &state, &db, 0, timeout_sec, SearchHorizon::GameEnd(), &heuristic, false
            );
            println!("GPU MCTS Suggestions: {:?}", suggestions.get(..3).unwrap_or(&suggestions));
            let action = suggestions.first().map(|s| s.0).unwrap_or(0);
            let _ = state.step(&db, action);
        } else {
            let cpu_mcts = MCTS::new();
            let suggestions = cpu_mcts.search_parallel(
                &state, &db, 0, timeout_sec, SearchHorizon::GameEnd(), &heuristic, false
            );
            println!("CPU MCTS Suggestions: {:?}", suggestions.get(..3).unwrap_or(&suggestions));
            let action = suggestions.first().map(|s| s.0).unwrap_or(0);
            let _ = state.step(&db, action);
        }
        move_count += 1;
    }

    println!("\n=== Final State ===");
    println!("Winner: {}", state.get_winner());
    println!("Scores: P0={} P1={}", state.core.players[0].score, state.core.players[1].score);
    println!("Turns: {}, Moves: {}", state.turn, move_count);
}
