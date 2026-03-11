/// test_turn_runner.rs — Diagnostic Solitaire Game Runner for Training
///
/// Run with: cargo run --bin test_turn_runner [--release]
///
/// Purpose: Fast, diagnostics-focused game runner for the no-abilities variant.
/// Output: Per-turn and per-action diagnostics including:
/// - Number of nodes explored (exhaustive search)
/// - Time to run (microseconds)
/// - Score breakdown (board_score + live_ev)
/// - Performance metrics
///
/// ─── TUNABLE PARAMETERS ──────────────────────────────────────────────────────
const NUM_GAMES: usize = 5;
const VERBOSE: bool = true;
const TURN_LIMIT: u16 = 6;  // Quick games for diagnostics
const ACTIONS_PER_TURN_LIMIT: usize = 50;  // Max play actions per turn
/// ─────────────────────────────────────────────────────────────────────────────

use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::{TurnSequencer, CONFIG};
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS, ACTION_BASE_LIVESET};
use rand::seq::IndexedRandom;

// ─────────────────────────────────────────────────────────────────────────────
// Diagnostics Tracking
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Default)]
struct ActionDiagnostic {
    action_id: i32,
    action_label: String,
    board_score: f32,
    live_ev: f32,
    total_score: f32,
    nodes_explored: usize,
    time_us: u128,
}

#[derive(Debug, Clone, Default)]
struct TurnDiagnostic {
    turn_number: u16,
    phase_name: String,
    actions: Vec<ActionDiagnostic>,
    final_board_score: f32,
    final_live_ev: f32,
    final_total_score: f32,
    total_nodes: usize,
    total_time_us: u128,
}

#[derive(Debug, Clone, Default)]
struct GameDiagnostic {
    game_number: usize,
    turns: Vec<TurnDiagnostic>,
    winner: i32,
    final_scores: (u32, u32),
    total_time_ms: f32,
}

// ─────────────────────────────────────────────────────────────────────────────
// Database Loading
// ─────────────────────────────────────────────────────────────────────────────

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
        println!("[DB_LOAD] Loading vanilla DB from: {:?}", abs);
        let json = fs::read_to_string(path).expect("Failed to read vanilla DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse vanilla DB");
        db.is_vanilla = true;
        return db;
    }

    panic!("Could not find cards_vanilla.json");
}

fn load_deck_combined(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let content = fs::read_to_string(path).expect("Failed to read deck file");
    let mut members = Vec::new();
    let mut lives = Vec::new();

    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        let card_no = parts[0];
        let count: usize = if parts.len() >= 3 && parts[1] == "x" {
            parts[2].parse().unwrap_or(1)
        } else {
            1
        };

        if let Some(id) = db.id_by_no(card_no) {
            for _ in 0..count {
                if db.lives.contains_key(&id) {
                    lives.push(id);
                } else {
                    members.push(id);
                }
            }
        }
    }

    while members.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            members.push(id);
        } else {
            break;
        }
    }
    while lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            lives.push(id);
        } else {
            break;
        }
    }

    members.truncate(48);
    lives.truncate(12);

    (members, lives)
}

fn fallback_deck(db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let members: Vec<i32> = db.members.keys().take(48).cloned().collect();
    let lives: Vec<i32> = db.lives.keys().take(12).cloned().collect();
    (members, lives)
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Phase Handler (Exhaustive DFS)
// ─────────────────────────────────────────────────────────────────────────────

struct MainPhaseResult {
    best_sequence: Vec<i32>,
    board_score: f32,
    live_ev: f32,
    total_score: f32,
    nodes_explored: usize,
    time_us: u128,
    evaluated_actions: Vec<ActionDiagnostic>,
}

fn handle_main_phase(state: &GameState, db: &CardDatabase) -> MainPhaseResult {
    let start = Instant::now();
    let (evals, best_seq, total_nodes, (board_score, live_ev)) =
        TurnSequencer::plan_full_turn(state, db);

    let total_score = board_score + live_ev;
    let duration = start.elapsed().as_micros();

    // Convert evaluations to action diagnostics
    let mut evaluated_actions = Vec::new();
    for (action_id, total_val, b_score, l_ev) in evals {
        let label = state.get_verbose_action_label(action_id, db);
        evaluated_actions.push(ActionDiagnostic {
            action_id,
            action_label: label,
            board_score: b_score,
            live_ev: l_ev,
            total_score: total_val,
            nodes_explored: 0,
            time_us: 0,
        });
    }

    MainPhaseResult {
        best_sequence: best_seq,
        board_score,
        live_ev,
        total_score,
        nodes_explored: total_nodes,
        time_us: duration,
        evaluated_actions,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// LiveSet Phase Handler
// ─────────────────────────────────────────────────────────────────────────────

struct LiveSetPhaseResult {
    best_sequence: Vec<i32>,
    live_ev: f32,
    nodes_explored: usize,
    time_us: u128,
}

fn handle_liveset_phase(state: &GameState, db: &CardDatabase) -> LiveSetPhaseResult {
    let start = Instant::now();
    let (seq, nodes, val_encoded) = TurnSequencer::find_best_liveset_selection(state, db);
    let duration = start.elapsed().as_micros();
    let live_ev = val_encoded as f32 / 1000.0;

    LiveSetPhaseResult {
        best_sequence: seq,
        live_ev,
        nodes_explored: nodes,
        time_us: duration,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Single Turn Runner (Main → LiveSet)
// ─────────────────────────────────────────────────────────────────────────────

fn run_single_turn(state: &mut GameState, db: &CardDatabase, turn_num: u16) -> TurnDiagnostic {
    let mut turn_diag = TurnDiagnostic {
        turn_number: turn_num,
        phase_name: "Main→LiveSet".to_string(),
        ..Default::default()
    };

    if VERBOSE {
        println!(
            "\n[Turn {}] Starting Main Phase: P0_Score={}, P1_Score={}",
            turn_num, state.players[0].score, state.players[1].score
        );
        println!(
            "  P0 Hand: {}, Deck: {}, Lives: {}",
            state.players[0].hand.len(),
            state.players[0].deck.len(),
            state.players[0].success_lives.len()
        );
    }

    // ─ MAIN PHASE ─
    let main_phase_start = Instant::now();
    let main_result = handle_main_phase(state, db);

    if VERBOSE && !main_result.evaluated_actions.is_empty() {
        println!("  ┌─ Main Phase Evaluations");
        for action_diag in main_result.evaluated_actions.iter().take(5) {
            println!(
                "  │ {:30} Board={:6.2} Live={:6.2} Total={:7.2}",
                action_diag.action_label, action_diag.board_score, action_diag.live_ev, action_diag.total_score
            );
        }
        if main_result.evaluated_actions.len() > 5 {
            println!("  │ ... {} more actions", main_result.evaluated_actions.len() - 5);
        }
        println!(
            "  ├─ Best Sequence: {} actions, Nodes: {}, Time: {}μs",
            main_result.best_sequence.len(), main_result.nodes_explored, main_result.time_us
        );
        println!(
            "  ├─ Best Score: Board={:.2} + Live={:.2} = Total={:.2}",
            main_result.board_score, main_result.live_ev, main_result.total_score
        );
    }

    turn_diag.actions = main_result.evaluated_actions;
    turn_diag.total_nodes += main_result.nodes_explored;
    turn_diag.total_time_us += main_result.time_us as u128;

    // Execute best sequence
    for &action in &main_result.best_sequence {
        if state.step(db, action).is_err() {
            break;
        }
        if state.phase != Phase::Main {
            break;
        }
    }

    // Ensure we transition to EndMain (or LiveSet if applicable)
    let _ = state.step(db, ACTION_BASE_PASS);

    // ─ LIVESET PHASE ─
    if state.phase == Phase::LiveSet {
        let liveset_result = handle_liveset_phase(state, db);

        if VERBOSE {
            println!(
                "  └─ LiveSet Phase: Nodes={}, Live_EV={:.2}, Time={}μs",
                liveset_result.nodes_explored, liveset_result.live_ev, liveset_result.time_us
            );
        }

        // Execute best liveset sequence
        for &action in &liveset_result.best_sequence {
            let _ = state.step(db, action);
        }

        turn_diag.final_live_ev = liveset_result.live_ev;
        turn_diag.total_nodes += liveset_result.nodes_explored;
        turn_diag.total_time_us += liveset_result.time_us as u128;
    }

    // Pass to end turn
    let _ = state.step(db, ACTION_BASE_PASS);

    // Auto-advance phases until next Main or Terminal (with safety limit)
    let mut phase_advance_count = 0;
    const MAX_PHASE_STEPS: usize = 100;
    while !state.is_terminal() && state.phase != Phase::Main && state.turn == turn_num && phase_advance_count < MAX_PHASE_STEPS {
        let phase_before = state.phase.clone();
        state.auto_step(db);
        if state.phase == Phase::Response {
            // Randomize response (e.g., Mulligan, TurnChoice, RPS)
            let legal = state.get_legal_action_ids(db);
            if !legal.is_empty() {
                let action = legal[0];
                let _ = state.step(db, action);
            }
        }
        // Detect if we're stuck in a phase
        if state.phase == phase_before {
            phase_advance_count += 1;
            if phase_advance_count > 10 {
                eprintln!("⚠️  WARNING: Phase stuck at {:?} for {} steps. Breaking.", state.phase, phase_advance_count);
                break;
            }
        } else {
            phase_advance_count = 0;
        }
    }

    turn_diag.final_board_score = main_result.board_score;
    turn_diag.final_total_score = main_result.total_score;
    turn_diag.total_time_us += main_phase_start.elapsed().as_micros();

    if VERBOSE {
        println!(
            "  └─ Turn {} Summary: Nodes={}, Time={:.3}ms, Score={:.2}",
            turn_num,
            turn_diag.total_nodes,
            turn_diag.total_time_us as f64 / 1000.0,
            turn_diag.final_total_score
        );
    }

    turn_diag
}

// ─────────────────────────────────────────────────────────────────────────────
// Full Game Runner
// ─────────────────────────────────────────────────────────────────────────────

fn run_game(
    game_idx: usize,
    member_cards: &[i32],
    live_cards: &[i32],
    energy_ids: &[i32],
    db: &CardDatabase,
) -> GameDiagnostic {
    let game_start = Instant::now();
    let mut game_diag = GameDiagnostic {
        game_number: game_idx + 1,
        ..Default::default()
    };

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

    println!("\n╔════════════════════════════════════════════════════════════╗");
    println!("║  GAME {} ({} Mode)", game_idx + 1, if db.is_vanilla { "Vanilla" } else { "Test" });
    println!("╚════════════════════════════════════════════════════════════╝");

    // Auto-advance to first Main phase (with proper handling of RPS/Mulligan/etc)
    let mut init_step_count = 0;
    const MAX_INIT_STEPS: usize = 50;
    let mut rng = rand::rng();
    
    while !state.is_terminal() && state.phase != Phase::Main && init_step_count < MAX_INIT_STEPS {
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                let legal = state.get_legal_action_ids(db);
                if !legal.is_empty() {
                    if let Some(&action) = legal.choose(&mut rng) {
                        let _ = state.step(db, action as i32);
                    } else {
                        break;
                    }
                } else {
                    break;
                }
            }
            _ => {
                state.auto_step(db);
            }
        }
        init_step_count += 1;
    }
    
    if init_step_count >= MAX_INIT_STEPS {
        eprintln!("⚠️  WARNING: Could not reach first Main phase after {} steps", MAX_INIT_STEPS);
    }

    if state.is_terminal() {
        println!("[TERMINAL] Game ended before first Main phase");
        game_diag.winner = state.get_winner();
        game_diag.final_scores = (state.players[0].score, state.players[1].score);
        game_diag.total_time_ms = game_start.elapsed().as_secs_f32() * 1000.0;
        return game_diag;
    }

    // Run turns (with safety limit)
    let mut step_count = 0;
    const MAX_STEPS_TOTAL: usize = 1000;
    while !state.is_terminal() && state.turn <= TURN_LIMIT && step_count < MAX_STEPS_TOTAL {
        // Ensure current player Main phase
        if state.phase != Phase::Main {
            match state.phase {
                Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                    let legal = state.get_legal_action_ids(db);
                    if !legal.is_empty() {
                        if let Some(&action) = legal.choose(&mut rng) {
                            let _ = state.step(db, action as i32);
                        } else {
                            break;
                        }
                    } else {
                        break;
                    }
                }
                _ => {
                    state.auto_step(db);
                }
            }
            step_count += 1;
            continue;
        }

        let current_turn = state.turn;
        let turn_diag = run_single_turn(&mut state, db, current_turn);
        game_diag.turns.push(turn_diag);
        step_count += 1;
    }
    
    if step_count >= MAX_STEPS_TOTAL {
        eprintln!("⚠️  WARNING: Reached max step limit ({}) - game may have infinite loop", MAX_STEPS_TOTAL);
    }

    game_diag.winner = state.get_winner();
    game_diag.final_scores = (state.players[0].score, state.players[1].score);
    game_diag.total_time_ms = game_start.elapsed().as_secs_f32() * 1000.0;

    println!(
        "\n  ══════════════════════════════════════════════════════════════\n  Final Result: Winner=P{}, Turns={}, Time={:.2}ms\n  Final Score: P0={} P1={}\n  ══════════════════════════════════════════════════════════════",
        game_diag.winner, state.turn, game_diag.total_time_ms, game_diag.final_scores.0, game_diag.final_scores.1
    );

    game_diag
}

// ─────────────────────────────────────────────────────────────────────────────
// Summary & Output
// ─────────────────────────────────────────────────────────────────────────────

fn print_summary(games: &[GameDiagnostic]) {
    println!("\n\n╔════════════════════════════════════════════════════════════╗");
    println!("║                    BATCH SUMMARY                           ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");

    let total_games = games.len();
    let total_nodes: usize = games
        .iter()
        .flat_map(|g| &g.turns)
        .map(|t| t.total_nodes)
        .sum();
    let total_time_ms: f32 = games.iter().map(|g| g.total_time_ms).sum();
    let avg_time_ms = total_time_ms / total_games as f32;
    let avg_nodes_per_turn = if games.iter().map(|g| g.turns.len()).sum::<usize>() > 0 {
        total_nodes as f32 / games.iter().map(|g| g.turns.len()).sum::<usize>() as f32
    } else {
        0.0
    };

    println!("Games Run:           {}", total_games);
    println!("Total Nodes:         {}", total_nodes);
    println!("Total Time:          {:.2}ms", total_time_ms);
    println!("Avg Time Per Game:   {:.2}ms", avg_time_ms);
    println!("Avg Nodes Per Turn:  {:.0}", avg_nodes_per_turn);
    println!("Throughput:          {:.1} games/sec", 1000.0 / avg_time_ms);

    println!("\n┌─ Per-Game Breakdown");
    for game in games {
        println!(
            "│ Game {}: {} turns, {} nodes, {:.2}ms, P0_Score={} P1_Score={}",
            game.game_number,
            game.turns.len(),
            game.turns.iter().map(|t| t.total_nodes).sum::<usize>(),
            game.total_time_ms,
            game.final_scores.0,
            game.final_scores.1
        );
    }
    println!("└─ End Breakdown\n");
}

fn main() {
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║  Test Turn Runner — Diagnostic Solitaire Variant         ║");
    println!("║  No Abilities | Exhaustive DFS | Fast Training Mode      ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");

    let cfg = CONFIG.clone();
    println!(
        "Config: DFS_Depth={}, MC_Trials={}\n",
        cfg.search.max_dfs_depth, cfg.search.mc_trials
    );

    let db = load_vanilla_db();
    let deck_path = "ai/decks/liella_cup.txt";
    let (member_cards, live_cards) = if std::path::Path::new(deck_path).exists() {
        load_deck_combined(deck_path, &db)
    } else {
        fallback_deck(&db)
    };

    let energy_ids: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    let mut all_diagnostics = Vec::new();
    for i in 0..NUM_GAMES {
        let game_diag = run_game(i, &member_cards, &live_cards, &energy_ids, &db);
        all_diagnostics.push(game_diag);
    }

    print_summary(&all_diagnostics);
}
