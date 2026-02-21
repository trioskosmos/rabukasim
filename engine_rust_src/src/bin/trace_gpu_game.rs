
use std::sync::Arc;
use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::core::mcts::{MCTS, SearchHorizon};
use engine_rust::core::gpu_conversions::GpuConverter;
use engine_rust::core::gpu_manager::GpuManager;
use engine_rust::core::heuristics::OriginalHeuristic;
use rand::seq::SliceRandom;

fn run_trace() {
    println!("=== GPU MCTS Single Game Trace (Rule-Accurate Edition) ===");

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

    let gpu_manager = Arc::new(GpuManager::new(&stats, &bytecode, wgpu::Backends::VULKAN).expect("Failed to init GPU"));
    let heuristic = OriginalHeuristic::default();

    // 2. Setup Initial Game State
    let mut state = GameState::default();

    // Sort members into playable (low cost) vs complex
    let mut members: Vec<i32> = db.members.keys().map(|&k| k as i32).collect();
    let mut lives: Vec<i32> = db.lives.keys().map(|&k| k as i32).collect();

    let mut rng = rand::rng(); 
    members.shuffle(&mut rng);
    lives.shuffle(&mut rng);

    // --- DECK DATA (REALISTIC COMPETITIVE) ---
    // Extracting realistic IDs for testing speed and synergy
    let p0_m: Vec<i32> = vec![
        245, 245, 245, 245, 245, 245, 245, 245, // ID 245 (8)
        227, 227, 227, 227, 227, 227, 227, 227, // ID 227 (8)
        370, 370, 370, 370, 370, 370, 370, 370, // ID 370 (8)
        376, 376, 376, 376, 376, 376, 376, 376, // ID 376 (8)
        24831, 24831, 24831, 24831, 24831, 24831, 24831, 24831 // ID 24831 (8)
    ]; // Total = 40 (8x5)
    let p1_m = p0_m.clone();

    let p0_e: Vec<i32> = vec![20000; 12];
    let p1_e: Vec<i32> = vec![20000; 12];

    let p0_l: Vec<i32> = vec![
        258, 258, 258, // ID 258 (3)
        261, 261, 261, // ID 261 (3)
        294, 294, 294, // ID 294 (3)
        384, 384, 384  // ID 384 (3)
    ]; // Total = 12 (3x4)
    let p1_l = p0_l.clone();

    let mut p0_main = p0_m;
    p0_main.extend(p0_l);
    let mut p1_main = p1_m;
    p1_main.extend(p1_l);

    state.initialize_game(p0_main, p1_main, p0_e, p1_e, Vec::new(), Vec::new());

    // Auto-advance setup phases for trace focus (Rule 6.2)
    let _ = state.step(&db, 10000); // P0 RPS: Rock
    let _ = state.step(&db, 11001); // P1 RPS: Paper (P1 wins first player)
    let _ = state.step(&db, 0);     // P1 Mulligan: Pass
    let _ = state.step(&db, 0);     // P0 Mulligan: Pass

    state.ui.silent = false;

    println!("Game Initialized Rule-Accurately (RPS/Mulligan skipped). Starting Turn 1 Phase LiveSet.");
    println!("Player 0 (GPU MCTS) vs Player 1 (CPU MCTS)");

    let mut move_count = 0;
    while !state.is_terminal() && move_count < 200 {
        let active_player = state.current_player;
        let is_gpu = active_player == 0;

        println!("\n--- MOVE {} (Player {}, Turn {}, Phase {:?}) ---", move_count, active_player, state.turn, state.phase);
        println!("Scores: P0={} P1={}", state.core.players[0].score, state.core.players[1].score);

        for p in 0..2 {
            let player = &state.core.players[p];
            print!("P{} Hand ({}): [", p, player.hand.len());
            for (i, &cid) in player.hand.iter().take(5).enumerate() {
                if i > 0 { print!(", "); }
                if let Some(m) = db.get_member(cid) {
                     print!("M{} (C{})", cid, m.cost);
                } else if let Some(l) = db.get_live(cid) {
                     print!("L{} (S{})", cid, l.score);
                }
            }
            if player.hand.len() > 5 { print!(", ..."); }
            println!("]");

            print!("P{} Stage: [", p);
            for (i, &cid) in player.stage.iter().enumerate() {
                if i > 0 { print!(", "); }
                if cid >= 0 {
                    if let Some(m) = db.get_member(cid as i32) {
                        let sanitized_name: String = m.name.chars().filter(|c| c.is_ascii()).collect();
                        print!("{}(ID{})", sanitized_name, cid);
                    } else { print!("ID{}", cid); }
                } else { print!("EMPTY"); }
            }
            println!("]");

            print!("P{} Lives: [", p);
            for (i, &cid) in player.live_zone.iter().enumerate() {
                if i > 0 { print!(", "); }
                if cid >= 0 {
                    if let Some(l) = db.get_live(cid as i32) {
                        let sanitized_name: String = l.name.chars().filter(|c| c.is_ascii()).collect();
                        print!("{}(ID{}) (S{})", sanitized_name, cid, l.score);
                    } else { print!("ID{}", cid); }
                } else { print!("EMPTY"); }
            }
            println!("]");
        }

        let timeout_sec = 0.1;

        let suggestions = if is_gpu {
            let gpu_mcts = MCTS::with_gpu(gpu_manager.clone(), 512);
            let _initial_state = state.to_gpu(&db);
            gpu_mcts.search_parallel(&state, &db, 0, timeout_sec, SearchHorizon::Limited(32), &heuristic, false)
        } else {
            let cpu_mcts = MCTS::new();
            cpu_mcts.search_parallel(&state, &db, 0, timeout_sec, SearchHorizon::Limited(32), &heuristic, false)
        };

        if !suggestions.is_empty() {
            println!("  Suggestions (Top 3):");
            for (i, res) in suggestions.iter().take(3).enumerate() {
                println!("    {}. Action {}, Reward {:.3}, Visits {}", i+1, res.0, res.1, res.2);
            }
        }

        let best = suggestions.first().cloned().unwrap_or((0, 0.5, 0));
        let action = best.0;

        if action == 0 {
             println!("  [ACTION] Pass/Wait chosen with Reward {:.3}", best.1);
        } else {
             println!("  [ACTION] Played ID {} chosen with Reward {:.3}", action, best.1);
        }

        let step_res = state.step(&db, action);
        for log in state.ui.rule_log.drain(..) {
            let sanitized: String = log.chars().filter(|c| c.is_ascii()).collect();
            println!("  [LOG] {}", sanitized);
        }
        if let Err(e) = step_res {
             println!("  [ERROR] Step failed: {:?}", e);
             break;
        }

        move_count += 1;
    }

    println!("\n=== GAME OVER ===");
    println!("Final Turn: {}, Final Move Count: {}", state.turn, move_count);
    println!("Final Scores: P0={} P1={}", state.core.players[0].score, state.core.players[1].score);
    println!("Winner: {:?}", state.get_winner());
}

fn main() {
    let builder = std::thread::Builder::new()
        .name("trace_gpu_thread".into())
        .stack_size(8 * 1024 * 1024); // 8MB stack size to prevent Naga stack overflow
    let handler = builder.spawn(|| {
        run_trace();
    }).unwrap();
    handler.join().unwrap();
}
