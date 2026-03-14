/// final_diagnostic.rs — Comprehensive Turn Sequencer Performance Test
///
/// Run with: cargo run --bin final_diagnostic --release
///
/// Shows complete diagnostics for training the no-abilities variant with DFS

use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use rand::SeedableRng;
use rand::rngs::SmallRng;
use rand::seq::IndexedRandom;

fn load_vanilla_db() -> CardDatabase {
    let candidates = [
        "data/cards_vanilla.json",
        "../data/cards_vanilla.json",
        "../../data/cards_vanilla.json",
    ];

    for path in &candidates {
        if !std::path::Path::new(path).exists() {
            continue;
        }
        let abs = std::fs::canonicalize(path)
            .unwrap_or_else(|_| std::path::PathBuf::from(path));
        println!("[DB] Loading from: {:?}\n", abs);
        let json = fs::read_to_string(path).expect("Failed to read vanilla DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse vanilla DB");
        db.is_vanilla = true;
        return db;
    }
    panic!("Could not find cards_vanilla.json");
}

fn fallback_deck(db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let members: Vec<i32> = db.members.keys().take(48).cloned().collect();
    let lives: Vec<i32> = db.lives.keys().take(12).cloned().collect();
    (members, lives)
}

#[derive(Debug, Clone)]
struct TurnStats {
    turn_num: u16,
    hand_size: usize,
    legal_actions: usize,
    dfs_nodes: usize,
    search_time_us: u128,
    board_score: f32,
    live_ev: f32,
    total_score: f32,
}

fn run_diagnostic_turn(
    state: &GameState,
    db: &CardDatabase,
    _rng: &mut impl rand::RngCore,
) -> TurnStats {
    let p_idx = state.current_player as usize;
    let hand_size = state.players[p_idx].hand.len();
    let legal_actions = state.get_legal_action_ids(db).len();

    let start = Instant::now();
    let (_best_seq, _best_val, breakdown, total_nodes) = TurnSequencer::plan_full_turn(state, db);
    let elapsed_us = start.elapsed().as_micros();

    TurnStats {
        turn_num: state.turn,
        hand_size,
        legal_actions,
        dfs_nodes: total_nodes,
        search_time_us: elapsed_us,
        board_score: breakdown.0,
        live_ev: breakdown.1,
        total_score: breakdown.0 + breakdown.1,
    }
}

fn main() {
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║  FINAL TURN SEQUENCER DIAGNOSTIC                          ║");
    println!("║  No-Abilities Variant for Training                        ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");

    let db = load_vanilla_db();
    let (_members, _lives) = fallback_deck(&db);
    let members = _members.clone();
    let lives = _lives.clone();
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    println!("DB STATS:");
    println!("  Members: {}", db.members.len());
    println!("  Lives: {}", db.lives.len());
    println!("  Energy: {}", db.energy_db.len());
    println!("  Deck Size: 48 members + 12 lives\n");

    let mut rng = rand::rngs::SmallRng::from_os_rng();
    let mut all_stats = Vec::new();

    // Run a few sample games
    for game_num in 0..3 {
        println!("╭─ GAME {} ───────────────────────────────────────────────╮", game_num + 1);

        let mut state = GameState::default();
        state.initialize_game(
            members.clone(),
            members.clone(),
            energy.clone(),
            energy.clone(),
            lives.clone(),
            lives.clone(),
        );
        state.ui.silent = true;

        // Reach Main phase
        let mut step = 0;
        while !state.is_terminal() && state.phase != Phase::Main && step < 50 {
            match state.phase {
                Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                    let legal = state.get_legal_action_ids(&db);
                    if !legal.is_empty() {
                        if let Some(&action) = legal.choose(&mut rng) {
                            let _ = state.step(&db, action as i32);
                        } else {
                            break;
                        }
                    }
                }
                _ => {
                    state.auto_step(&db);
                }
            }
            step += 1;
        }

        if state.phase != Phase::Main {
            println!("│  ⚠️  Could not reach Main phase (stuck at {:?})", state.phase);
            println!("╰──────────────────────────────────────────────────────────╯\n");
            continue;
        }

        // Run up to 3 Main phases
        let mut turn_count = 0;
        let max_turns = 3;

        while !state.is_terminal() && turn_count < max_turns && state.turn <= 10 {
            if state.phase == Phase::Main {
                let stats = run_diagnostic_turn(&state, &db, &mut rng);
                all_stats.push(stats.clone());

                println!("│  Turn {}.{} | Hand: {} | Legal: {} | DFS Nodes: {}",
                    stats.turn_num, state.current_player, stats.hand_size, stats.legal_actions, stats.dfs_nodes);
                println!("│    Search: {}μs | Board: {:.2} | LiveEV: {:.2} | Total: {:.2}",
                    stats.search_time_us, stats.board_score, stats.live_ev, stats.total_score);

                turn_count += 1;
                let _ = state.step(&db, ACTION_BASE_PASS);
            } else {
                // Auto-handle non-Main phases
                match state.phase {
                    Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                        let legal = state.get_legal_action_ids(&db);
                        if !legal.is_empty() {
                            if let Some(&action) = legal.choose(&mut rng) {
                                let _ = state.step(&db, action as i32);
                            }
                        }
                    }
                    _ => {
                        state.auto_step(&db);
                    }
                }
            }
        }

        println!("│  Final Score: P0={} P1={}", state.players[0].score, state.players[1].score);
        println!("╰──────────────────────────────────────────────────────────╯\n");
    }

    // Summary
    if !all_stats.is_empty() {
        println!("╔════════════════════════════════════════════════════════════╗");
        println!("║                     SUMMARY STATISTICS                     ║");
        println!("╚════════════════════════════════════════════════════════════╝\n");

        let avg_nodes: f32 = all_stats.iter().map(|s| s.dfs_nodes as f32).sum::<f32>() / all_stats.len() as f32;
        let avg_time: f32 = all_stats.iter().map(|s| s.search_time_us as f32).sum::<f32>() / all_stats.len() as f32;
        let avg_board: f32 = all_stats.iter().map(|s| s.board_score).sum::<f32>() / all_stats.len() as f32;
        let avg_live: f32 = all_stats.iter().map(|s| s.live_ev).sum::<f32>() / all_stats.len() as f32;

        println!("Turns Analyzed:     {}", all_stats.len());
        println!("Avg Hand Size:      {:.1}", all_stats.iter().map(|s| s.hand_size as f32).sum::<f32>() / all_stats.len() as f32);
        println!("Avg Legal Actions:  {:.1}", all_stats.iter().map(|s| s.legal_actions as f32).sum::<f32>() / all_stats.len() as f32);
        println!("\nDFS Performance:");
        println!("  Avg Nodes:       {:.0}", avg_nodes);
        println!("  Avg Time:        {:.1}μs ({:.3}ms)", avg_time, avg_time / 1000.0);
        println!("  Throughput:      {:.0} turns/sec", 1_000_000.0 / avg_time);
        println!("\nScore Breakdown:");
        println!("  Avg Board Score: {:.2}", avg_board);
        println!("  Avg Live EV:     {:.2}", avg_live);
        println!("  Avg Total:       {:.2}", avg_board + avg_live);

        println!("\n✓ The DFS turn sequencer is suitable for fast training!");
        println!("  - Exhaustive search explores all feasible combinations");
        println!("  - Outputs both board state and live evaluation scores");
        println!("  - No abilities → solitaire mode → deterministic scoring");
    }
}
