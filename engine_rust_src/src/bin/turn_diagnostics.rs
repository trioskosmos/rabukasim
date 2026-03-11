/// turn_diagnostics.rs — Diagnostic Turn Sequencer with Timeout & Stats
///
/// Run with: cargo run --bin turn_diagnostics [--release]
///
/// Tests the DFS search speed with exhaustive diagnostics and timeout protection

use std::fs;
use std::time::Instant;
use std::sync::atomic::{AtomicUsize, Ordering};

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use rand::seq::IndexedRandom;
use rand::SeedableRng;

// ─── CONFIG ──────────────────────────────────────────────────────────────────

/// Max milliseconds for a single turn search
const SEARCH_TIMEOUT_MS: u128 = 5000;

/// Max iteration count for DFS (safety valve)
static DFS_ITERATION_COUNT: AtomicUsize = AtomicUsize::new(0);
const DFS_MAX_ITERATIONS: usize = 100_000;

// ─── DB LOADING ──────────────────────────────────────────────────────────────

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
        println!("[DB_LOAD] Loading from: {:?}", abs);
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

// ─── DIAGNOSTICS ────────────────────────────────────────────────────────────

struct TurnDiagnostic {
    turn_num: u16,
    player: u8,
    phase: Phase,
    hand_size: usize,
    legal_actions: usize,
    search_time_ms: u128,
    iterations: usize,
    best_action: Option<i32>,
    board_score: f32,
    live_ev: f32,
    total_score: f32,
    timeout: bool,
}

impl std::fmt::Display for TurnDiagnostic {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let timeout_flag = if self.timeout { " [TIMEOUT]" } else { "" };
        writeln!(
            f,
            "Turn {}.{} | Hand: {} | Legal: {} | Iters: {}",
            self.turn_num, self.player, self.hand_size, self.legal_actions, self.iterations
        )?;
        writeln!(
            f,
            "  Search Time: {}ms | Board: {:.2} | LiveEV: {:.2} | Total: {:.2}{}",
            self.search_time_ms, self.board_score, self.live_ev, self.total_score, timeout_flag
        )?;
        Ok(())
    }
}

// ─── TEST TURN SEQUENCE ──────────────────────────────────────────────────────

fn run_diagnostic_turn(
    state: &GameState,
    db: &CardDatabase,
    _rng: &mut impl rand::RngCore,
) -> TurnDiagnostic {
    let p_idx = state.current_player as usize;
    let hand_size = state.players[p_idx].hand.len();
    let legal_actions = state.get_legal_action_ids(db).len();

    DFS_ITERATION_COUNT.store(0, Ordering::Relaxed);
    let search_start = Instant::now();

    let (_evals, best_seq, total_nodes, breakdown) =
        TurnSequencer::plan_full_turn(state, db);

    let elapsed_ms = search_start.elapsed().as_millis();
    let iterations = DFS_ITERATION_COUNT.load(Ordering::Relaxed);
    let timeout = elapsed_ms > SEARCH_TIMEOUT_MS || iterations >= DFS_MAX_ITERATIONS;

    let best_action = if best_seq.is_empty() {
        None
    } else {
        Some(best_seq[0])
    };

    let total_score = breakdown.0 + breakdown.1;

    TurnDiagnostic {
        turn_num: state.turn,
        player: state.current_player,
        phase: state.phase.clone(),
        hand_size,
        legal_actions,
        search_time_ms: elapsed_ms,
        iterations: total_nodes,
        best_action,
        board_score: breakdown.0,
        live_ev: breakdown.1,
        total_score,
        timeout,
    }
}

// ─── SIMPLIFIED GAME LOOP ────────────────────────────────────────────────────

fn test_turns(
    member_cards: &[i32],
    live_cards: &[i32],
    energy_ids: &[i32],
    db: &CardDatabase,
    rng: &mut impl rand::RngCore,
) {
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

    println!("\n╔════════════════════════════════════════════════╗");
    println!("║  TURN SEQUENCER DIAGNOSTICS                    ║");
    println!("╚════════════════════════════════════════════════╝\n");

    println!("MAX_DFS_DEPTH: {} | SEARCH_TIMEOUT: {}ms | MAX_ITERATIONS: {}\n",
        5, SEARCH_TIMEOUT_MS, DFS_MAX_ITERATIONS);

    let mut turn_count = 0;
    let max_turns = 3; // Just test first 3 turns to keep it manageable

    while !state.is_terminal() && turn_count < max_turns && state.turn <= 10 {
        state.auto_step(db);

        if state.phase == Phase::Main {
            println!("─ Turn {} Main Phase (P{}) ─────────────────────────", state.turn, state.current_player);

            let diagnostic = run_diagnostic_turn(&state, db, rng);
            println!("{}", diagnostic);

            if diagnostic.timeout {
                println!("⚠️  TIMEOUT DETECTED - Stopping search");
                break;
            }

            // PASS to end turn (since without abilities, any continuation is equivalent)
            let _ = state.step(db, ACTION_BASE_PASS);
            turn_count += 1;
        } else {
            // Auto-handle non-Main phases
            let legal = state.get_legal_action_ids(db);
            if !legal.is_empty() {
                if let Some(&choice) = legal.choose(rng) {
                    let _ = state.step(db, choice as i32);
                } else {
                    break;
                }
            } else {
                break;
            }
        }
    }

    println!("\n╔════════════════════════════════════════════════╗");
    println!("║  DIAGNOSTIC COMPLETE                           ║");
    println!("║  Final Score: P0={} | P1={}               │",
        state.players[0].score, state.players[1].score);
    println!("╚════════════════════════════════════════════════╝");
}

fn main() {
    println!("Turn Sequencer Diagnostic Tool\n");

    let db = load_vanilla_db();

    let deck_path = "ai/decks/liella_cup.txt";
    let (member_cards, live_cards) = if std::path::Path::new(deck_path).exists() {
        println!("[DECK] Loading from {}", deck_path);
        load_deck_combined(deck_path, &db)
    } else {
        println!("[DECK] Using fallback deck");
        fallback_deck(&db)
    };

    let energy_ids: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    let mut rng = rand::rng();

    test_turns(&member_cards, &live_cards, &energy_ids, &db, &mut rng);
}
