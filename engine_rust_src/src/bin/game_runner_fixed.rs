/// game_runner_fixed.rs — Fixed Game Runner with Proper Phase Handling
///
/// Run with: cargo run --bin game_runner_fixed --release
///
/// This version properly handles all game phases and runs until score reaches 3

use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use rand::seq::IndexedRandom;

const NUM_GAMES: usize = 5;
const VERBOSE: bool = true;
const STEP_LIMIT: usize = 10000;
const TURN_LIMIT: u16 = 100;

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
struct GameStats {
    game_num: usize,
    total_steps: usize,
    final_turn: u16,
    winner: i32,
    p0_score: u32,
    p1_score: u32,
    time_ms: f32,
}

fn run_game(
    game_idx: usize,
    member_cards: &[i32],
    live_cards: &[i32],
    energy_ids: &[i32],
    db: &CardDatabase,
    rng: &mut impl rand::RngCore,
) -> GameStats {
    let game_start = Instant::now();
    
    let mut state = GameState::default();
    state.initialize_game(
        member_cards.to_vec(),
        member_cards.to_vec(),
        energy_ids.to_vec(),
        energy_ids.to_vec(),
        live_cards.to_vec(),
        live_cards.to_vec(),
    );

    state.ui.silent = true;

    println!("\n╔════════════════════════════════════════════╗");
    println!("║  GAME {} (Official Rules)        ║", game_idx + 1);
    println!("╚════════════════════════════════════════════╝");

    let mut current_step = 0;
    let mut last_turn_phase = (0u16, Phase::Setup);

    while !state.is_terminal() && current_step < STEP_LIMIT && state.turn <= TURN_LIMIT {
        current_step += 1;

        // Print turn/phase status
        if (state.turn, state.phase.clone()) != last_turn_phase {
            last_turn_phase = (state.turn, state.phase.clone());
            if VERBOSE {
                println!("[Turn {} | {:?}] P0: {} | P1: {}", 
                    state.turn, state.phase, state.players[0].score, state.players[1].score);
            }
        }

        // Handle Main phase with AI
        if state.phase == Phase::Main {
            let legal = state.get_legal_action_ids(db);
            if legal.is_empty() {
                let _ = state.step(db, ACTION_BASE_PASS);
            } else {
                // Use TurnSequencer to get best move
                let (_evals, best_seq, _nodes, _breakdown) = TurnSequencer::plan_full_turn(&state, db);
                let action = if best_seq.is_empty() {
                    ACTION_BASE_PASS as i32
                } else {
                    best_seq[0]
                };
                
                if state.step(db, action).is_err() {
                    let _ = state.step(db, ACTION_BASE_PASS);
                }
            }
        } 
        // Handle LiveSet phase with AI
        else if state.phase == Phase::LiveSet {
            let legal = state.get_legal_action_ids(db);
            if legal.is_empty() {
                let _ = state.step(db, ACTION_BASE_PASS);
            } else {
                let (best_seq, _nodes, _val) = TurnSequencer::find_best_liveset_selection(&state, db);
                let action = if best_seq.is_empty() {
                    ACTION_BASE_PASS as i32
                } else {
                    best_seq[0]
                };
                let _ = state.step(db, action);
            }
        }
        // Handle random/auto phases
        else if matches!(state.phase, Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response) {
            let legal = state.get_legal_action_ids(db);
            if !legal.is_empty() {
                if let Some(&action) = legal.choose(rng) {
                    let _ = state.step(db, action as i32);
                } else {
                    let _ = state.step(db, ACTION_BASE_PASS);
                }
            } else {
                let _ = state.step(db, ACTION_BASE_PASS);
            }
        }
        // Auto-step other phases
        else {
            state.auto_step(db);
        }

        // Early termination if someone reaches 3
        if state.players[0].score >= 3 || state.players[1].score >= 3 {
            break;
        }
    }

    let winner = state.get_winner();
    let time_ms = game_start.elapsed().as_secs_f32() * 1000.0;

    if VERBOSE {
        println!("\n  ════════════════════════════════════════════");
        println!("  Final: Winner=P{} | Turns={} | Steps={}", winner, state.turn, current_step);
        println!("  Score: P0={} P1={} | Time: {:.2}ms",
            state.players[0].score, state.players[1].score, time_ms);
        println!("  ════════════════════════════════════════════");
    }

    GameStats {
        game_num: game_idx + 1,
        total_steps: current_step,
        final_turn: state.turn,
        winner,
        p0_score: state.players[0].score,
        p1_score: state.players[1].score,
        time_ms,
    }
}

fn main() {
    println!("╔════════════════════════════════════════════╗");
    println!("║  FIXED GAME RUNNER                         ║");
    println!("║  Running until score >= 3                 ║");
    println!("╚════════════════════════════════════════════╝\n");

    let db = load_vanilla_db();
    let (member_cards, live_cards) = fallback_deck(&db);
    let energy_ids: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    let mut rng = rand::rng();

    let mut games = Vec::new();
    for i in 0..NUM_GAMES {
        let stats = run_game(i, &member_cards, &live_cards, &energy_ids, &db, &mut rng);
        games.push(stats);
    }

    // Summary
    println!("\n╔════════════════════════════════════════════╗");
    println!("║              BATCH SUMMARY                 ║");
    println!("╚════════════════════════════════════════════╝\n");

    let total_time: f32 = games.iter().map(|g| g.time_ms).sum();
    let avg_time = total_time / games.len() as f32;
    
    for g in &games {
        println!("Game {}: {} turns, {} steps, P0={} P1={}, {:.2}ms",
            g.game_num, g.final_turn, g.total_steps, g.p0_score, g.p1_score, g.time_ms);
    }
    
    println!("\nOverall: {} games, {:.2}ms avg/game", games.len(), avg_time);
    println!("✓ Games completed successfully!\n");
}
