/// simple_game_v2.rs — Game Runner (Based on full_game_sim.rs)
///
/// Run with: cargo run --bin simple_game_v2 --release
///
/// Uses TurnSequencer for AI decisions, auto_step for phase transitions.
/// Completes games until someone reaches score 3.

use std::fs::{ self, OpenOptions };
use std::io::Write;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
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
        println!("[DB] Loading: {}", path);
        let json = fs::read_to_string(path).expect("Failed to read DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
        db.is_vanilla = true;
        return db;
    }
    panic!("cards_vanilla.json not found");
}

fn load_deck(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    println!("[DECK] Loading: {}", path);
    let content = fs::read_to_string(path).expect("Failed to read deck");
    let mut members = Vec::new();
    let mut lives = Vec::new();

    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.is_empty() {
            continue;
        }
        
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

    println!("[DECK] Members: {} | Lives: {}", members.len(), lives.len());
    (members, lives)
}

fn main() {
    println!("\n╔═══════════════════════════════════════╗");
    println!("║     Simple Game Runner (v2)         ║");
    println!("╚═══════════════════════════════════════╝\n");

    let db = load_vanilla_db();
    let (members, lives) = load_deck("../ai/decks/liella_cup.txt", &db);
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

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

    println!("[GAME] Starting game...\n");
    let game_start = Instant::now();
    let mut rng = rand::rng();
    let mut steps = 0;
    let mut last_state = (0u16, Phase::Setup);

    // Open output file for UTF-8 logging
    let mut output_file = OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(true)
        .open("game_output.txt")
        .expect("Failed to create output file");

    let _ = writeln!(output_file, "╔═══════════════════════════════════════╗");
    let _ = writeln!(output_file, "║  Game Output (UTF-8 Encoded)        ║");
    let _ = writeln!(output_file, "╚═══════════════════════════════════════╝\n");

    const STEP_LIMIT: usize = 50000;
    const TURN_LIMIT: u16 = 100;

    while !state.is_terminal() && game_start.elapsed().as_secs() < 300 && steps < STEP_LIMIT && state.turn <= TURN_LIMIT {
        // First: auto-step through non-interactive phases
        state.auto_step(&db);

        if state.is_terminal() {
            break;
        }

        // Track turn/phase changes
        if (state.turn, state.phase) != last_state {
            last_state = (state.turn, state.phase);
            if state.phase == Phase::Main || state.phase == Phase::LiveSet {
                let msg = format!("[Turn {}] P{} @ {:?} | Score: P0={} P1={}",
                    state.turn, state.current_player, state.phase,
                    state.players[0].score, state.players[1].score);
                println!("{}", msg);
                let _ = writeln!(output_file, "{}", msg);
            }
        }

        // Get legal actions for current phase
        let legal = state.get_legal_action_ids(&db);
        if legal.is_empty() {
            steps += 1;
            continue;
        }

        // Decide action based on phase
        let action = match state.phase {
            Phase::Main => {
                let (_evals, best_seq, _nodes, _breakdown) = TurnSequencer::plan_full_turn(&state, &db);
                if best_seq.is_empty() {
                    ACTION_BASE_PASS
                } else {
                    best_seq[0]
                }
            },
            Phase::LiveSet => {
                let (seq, _nodes, _val) = TurnSequencer::find_best_liveset_selection(&state, &db);
                if seq.is_empty() {
                    ACTION_BASE_PASS
                } else {
                    seq[0]
                }
            },
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                // Random action for interactive non-AI phases
                if let Some(&action_id) = legal.choose(&mut rng) {
                    action_id as i32
                } else {
                    ACTION_BASE_PASS
                }
            },
            _ => {
                // Default: use first legal action (should be rare)
                legal[0] as i32
            }
        };

        // Execute the action
        if state.step(&db, action).is_err() {
            let _ = state.step(&db, ACTION_BASE_PASS);
        }

        steps += 1;

        // Check win condition
        if state.players[0].score >= 3 || state.players[1].score >= 3 {
            break;
        }
    }

    let elapsed = game_start.elapsed().as_secs_f32();
    let winner = state.get_winner();

    println!("\n╔═══════════════════════════════════════╗");
    println!("║         Game Complete               ║");
    println!("╚═══════════════════════════════════════╝");
    println!("Steps: {} | Turns: {} | Time: {:.2}s",  steps, state.turn, elapsed);
    println!("Winner: P{} | Final Score: P0={} P1={}",
        winner, state.players[0].score, state.players[1].score);

    // Write to file
    let _ = writeln!(output_file, "\n╔═══════════════════════════════════════╗");
    let _ = writeln!(output_file, "║         Game Complete               ║");
    let _ = writeln!(output_file, "╚═══════════════════════════════════════╝");
    let _ = writeln!(output_file, "Steps: {} | Turns: {} | Time: {:.2}s",  steps, state.turn, elapsed);
    let _ =  writeln!(output_file, "Winner: P{} | Final Score: P0={} P1={}",
        winner, state.players[0].score, state.players[1].score);
}
