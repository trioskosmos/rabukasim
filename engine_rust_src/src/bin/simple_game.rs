/// simple_game.rs — Simple Game Runner Using TurnSequencer
///
/// Run with: cargo run --bin simple_game --release
///
/// Loads deck from ai/decks/, runs game until someone reaches score 3

use std::fs;
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
    println!("║  Simple Game Runner - TurnSequencer  ║");
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
    let mut last_phase = state.phase;

    while !state.is_terminal() && game_start.elapsed().as_secs() < 300 && steps < 50000 {
        steps += 1;

        // Track all phase transitions
        if state.phase != last_phase {
            println!("[{}] Phase: {:?} (P{})", steps, state.phase, state.current_player);
            last_phase = state.phase;
        }

        // Handle each phase type appropriately
        match state.phase {
            Phase::Main => {
                println!("[Turn {}] Main | Score: P0={} P1={}", 
                    state.turn, state.players[0].score, state.players[1].score);

                let start = Instant::now();
                let (_evals, best_seq, nodes, breakdown) = TurnSequencer::plan_full_turn(&state, &db);
                let elapsed = start.elapsed().as_micros();

                println!("  DFS: {} nodes, {}μs | Board: {:.2} | Live: {:.2}",
                    nodes, elapsed, breakdown.0, breakdown.1);

                // Execute sequence
                for &action in &best_seq {
                    if state.step(&db, action).is_err() {
                        break;
                    }
                    if state.phase != Phase::Main {
                        break;
                    }
                }
                // Pass to end Main
                let _ = state.step(&db, ACTION_BASE_PASS);
            },
            Phase::LiveSet => {
                let (seq, _nodes, _val) = TurnSequencer::find_best_liveset_selection(&state, &db);
                
                if !seq.is_empty() {
                    println!("  [LiveSet] {} actions", seq.len());
                    for &action in &seq {
                        if state.step(&db, action).is_err() {
                            break;
                        }
                    }
                }
                
                // Pass to end LiveSet
                let _ = state.step(&db, ACTION_BASE_PASS);
            },
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | 
            Phase::TurnChoice | Phase::Response => {
                // Random action for non-deterministic phases
                let legal = state.get_legal_action_ids(&db);
                if !legal.is_empty() {
                    if let Some(&action) = legal.choose(&mut rng) {
                        let _ = state.step(&db, action as i32);
                    }
                } else {
                    let _ = state.step(&db, ACTION_BASE_PASS);
                }
            },
            _ => {
                // All other phases: auto-advance
                state.auto_step(&db);
            }
        }

        // Termination check with score debug
        if state.is_terminal() {
            println!("[TERMINAL] Game ended at turn {}, score P0={}, P1={}", 
                state.turn, state.players[0].score, state.players[1].score);
            break;
        }

        if steps % 100 == 0 {
            println!("  [{}] Still running... Score: P0={} P1={}", 
                steps, state.players[0].score, state.players[1].score);
        }
    }

    let elapsed = game_start.elapsed().as_secs_f32();
    let winner = state.get_winner();

    println!("\n╔═══════════════════════════════════════╗");
    println!("║  Game Complete                      ║");
    println!("╚═══════════════════════════════════════╝");
    println!("Steps: {} | Time: {:.2}s", steps, elapsed);
    println!("Final Score: P0={} P1={} | Winner: P{}", 
        state.players[0].score, state.players[1].score, winner);
}
