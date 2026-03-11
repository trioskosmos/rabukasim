/// full_game_sim.rs — Official Rule Compliant AI Simulation
///
/// Run with: cargo run --bin full_game_sim [--release]
///
/// ─── TUNABLE PARAMETERS ──────────────────────────────────────────────────────
const NUM_GAMES: usize = 1;
const VERBOSE: bool = true;
const STEP_LIMIT: usize = 500;
const TURN_LIMIT: u16 = 20;
/// ─────────────────────────────────────────────────────────────────────────────

use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::{TurnSequencer, CONFIG};
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use rand::seq::SliceRandom;

// ── DB loading ────────────────────────────────────────────────────────────────

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

// ── Deck loading ──────────────────────────────────────────────────────────────

fn load_deck_combined(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let content = fs::read_to_string(path).expect("Failed to read deck file");
    let mut members = Vec::new();
    let mut lives = Vec::new();

    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') { continue; }
        let parts: Vec<&str> = line.split_whitespace().collect();
        let card_no = parts[0];
        let count: usize = if parts.len() >= 3 && parts[1] == "x" {
            parts[2].parse().unwrap_or(1)
        } else { 1 };

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

    // Official Rules: 48 members + 12 lives = 60 cards
    // If deck is invalid, pad with anything from the DB to avoid Turn 0 termination
    while members.len() < 48 {
        if let Some(&id) = db.members.keys().next() { members.push(id); } else { break; }
    }
    while lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() { lives.push(id); } else { break; }
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

// ── AI decision ───────────────────────────────────────────────────────────────

struct AIDecision {
    action: Option<usize>,
    nodes: usize,
    board_score: f32,
    live_ev: f32,
    duration_us: u128,
}

fn pick_action(state: &GameState, db: &CardDatabase, rng: &mut impl rand::RngCore) -> AIDecision {
    let legal = state.get_legal_action_ids(db);
    if legal.is_empty() {
        return AIDecision { action: None, nodes: 0, board_score: 0.0, live_ev: 0.0, duration_us: 0 };
    }

    let start = Instant::now();
    match state.phase {
        Phase::Main => {
            let (_evals, best_seq, nodes, breakdown) = TurnSequencer::plan_full_turn(state, db);
            let duration = start.elapsed().as_micros();
            let action = if best_seq.is_empty() { Some(ACTION_BASE_PASS as usize) } else { Some(best_seq[0] as usize) };
            AIDecision { action, nodes, board_score: breakdown.0, live_ev: breakdown.1, duration_us: duration }
        }
        Phase::LiveSet => {
            let (seq, _nodes, val_encoded) = TurnSequencer::find_best_liveset_selection(state, db);
            let duration = start.elapsed().as_micros();
            let action = if seq.is_empty() { Some(ACTION_BASE_PASS as usize) } else { Some(seq[0] as usize) };
            let score = val_encoded as f32 / 1000.0;
            AIDecision { action, nodes: _nodes, board_score: 0.0, live_ev: score, duration_us: duration }
        }
        // Randomize RPS, Mulligan, and Choice phases for variability
        Phase::Rps | Phase::Mulligan | Phase::TurnChoice | Phase::Response => {
            let duration = start.elapsed().as_micros();
            let action = Some(*legal.choose(rng).unwrap_or(&legal[0]) as usize);
            AIDecision { action, nodes: 0, board_score: 0.0, live_ev: 0.0, duration_us: duration }
        }
        _ => {
            let duration = start.elapsed().as_micros();
            AIDecision { action: Some(legal[0] as usize), nodes: 0, board_score: 0.0, live_ev: 0.0, duration_us: duration }
        }
    }
}

// ── Single game runner ────────────────────────────────────────────────────────

fn run_game(
    game_idx: usize,
    member_cards: &[i32],
    live_cards: &[i32],
    energy_ids: &[i32],
    db: &CardDatabase,
    rng: &mut impl rand::RngCore,
) {
    let mut state = GameState::default();
    
    // Official Rules: Combined Deck (48+12)
    let p0_deck = member_cards.to_vec();
    let p1_deck = member_cards.to_vec();
    let p0_lives = live_cards.to_vec();
    let p1_lives = live_cards.to_vec();
    
    // Note: initialize_game will combine members+lives into the deck and shuffle.
    // Starting lives zone is empty.
    state.initialize_game(
        p0_deck, p1_deck, 
        energy_ids.to_vec(), energy_ids.to_vec(), 
        p0_lives, p1_lives
    );

    println!("[INIT] Phase: {:?}, P0 Hand: {}, P0 Deck: {}, P0 Lives: {}", 
        state.phase, state.players[0].hand.len(), state.players[0].deck.len(), state.players[0].success_lives.len());

    state.ui.silent = true;

    println!("\n══════════════════════════════════════════════");
    println!("  GAME {} (Official Rules: Mixed Deck)", game_idx + 1);
    println!("══════════════════════════════════════════════");

    let mut current_step = 0;
    while !state.is_terminal() && current_step < STEP_LIMIT && state.turn <= TURN_LIMIT {
        state.auto_step(db);
        if state.is_terminal() { 
            println!("[TERMINAL] Game ended at turn {} (Steps: {}, Phase: {:?}, P0 Score: {}, P1 Score: {})", 
                state.turn, current_step, state.phase, state.players[0].score, state.players[1].score);
            break; 
        }

        if (state.turn, state.phase) != last_turn_phase {
            last_turn_phase = (state.turn, state.phase);
            println!("\n[Turn {} | P{} | {:?}] Space Score: P0={} P1={}", 
                state.turn, state.current_player, state.phase, state.players[0].score, state.players[1].score);
        }

        let decision = pick_action(&state, db, rng);
        if let Some(action) = decision.action {
            let label = state.get_verbose_action_label(action as i32, db);
            if decision.nodes > 0 || state.phase != Phase::Main {
                println!("  P{} @ {:?} → {} [Nodes: {}, Board: {:.2}, LiveEV: {:.2}, Time: {}us]", 
                    state.current_player, state.phase, label, decision.nodes, decision.board_score, decision.live_ev, decision.duration_us);
            }
            
            if state.step(db, action as i32).is_err() {
                let _ = state.step(db, ACTION_BASE_PASS);
            }
        } else {
            println!("  [WARN] No actions for P{} at {:?}", state.current_player, state.phase);
            let _ = state.step(db, ACTION_BASE_PASS);
        }
        current_step += 1;
    }

    if current_step >= STEP_LIMIT { println!("[TERMINAL] Step limit reached!"); }
    if state.turn > TURN_LIMIT { println!("[TERMINAL] Turn limit reached!"); }

    let winner = state.get_winner();
    println!("\n  ── Game {} finished: Winner=P{} | Turns={}", game_idx + 1, winner, state.turn);
    println!("  Final Score: P0={} P1={}", state.players[0].score, state.players[1].score);
}

fn main() {
    println!("Vanilla AI Simulation Runner (Official Rules Alignment)\n");
    let cfg = CONFIG.clone();
    println!("DFS Max Depth: {}", cfg.search.max_dfs_depth);

    let db = load_vanilla_db();
    let deck_path = "ai/decks/liella_cup.txt";
    let (member_cards, live_cards) = if std::path::Path::new(deck_path).exists() {
        load_deck_combined(deck_path, &db)
    } else {
        fallback_deck(&db)
    };

    // Grab first 12 energy cards for the energy deck
    let energy_ids: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    let mut rng = rand::rng();

    for i in 0..NUM_GAMES {
        run_game(i, &member_cards, &live_cards, &energy_ids, &db, &mut rng);
    }
}
