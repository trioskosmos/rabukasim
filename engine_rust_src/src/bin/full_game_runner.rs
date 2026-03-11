/// full_game_runner.rs — Complete Game Runner for Training
///
/// Run with: cargo run --bin full_game_runner --release
///
/// Plays complete games until one player reaches score 3

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
        let abs = std::fs::canonicalize(path)
            .unwrap_or_else(|_| std::path::PathBuf::from(path));
        println!("[DB] {} loaded\n", abs.display());
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

fn advance_to_phase(
    state: &mut GameState,
    db: &CardDatabase,
    target_phase: Phase,
    rng: &mut impl rand::RngCore,
    max_steps: usize,
) -> bool {
    let mut steps = 0;
    while state.phase != target_phase && !state.is_terminal() && steps < max_steps {
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                let legal = state.get_legal_action_ids(db);
                if !legal.is_empty() {
                    if let Some(&action) = legal.choose(rng) {
                        let _ = state.step(db, action as i32);
                    } else {
                        return false;
                    }
                } else {
                    return false;
                }
            }
            _ => {
                state.auto_step(db);
            }
        }
        steps += 1;
    }
    state.phase == target_phase && !state.is_terminal()
}

fn main() {
    println!("╔════════════════════════════════════════════════════════════╗");
    println!("║         FULL GAME RUNNER - No Abilities Variant           ║");
    println!("║            Play until P0 or P1 reaches score 3            ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");

    let db = load_vanilla_db();
    let (_members, _lives) = fallback_deck(&db);
    let members = _members;
    let lives = _lives;
    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    let mut rng = rand::rng();
    let game_start = Instant::now();

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

    println!("Initializing game...\n");

    // Reach first Main
    if !advance_to_phase(&mut state, &db, Phase::Main, &mut rng, 50) {
        println!("ERROR: Could not reach Main phase");
        return;
    }

    println!("Game initialized. Playing...\n");

    let max_turns = 50;
    let mut turn = 0;

    while !state.is_terminal() && state.players[0].score < 3 && state.players[1].score < 3  && turn < max_turns {
        println!("┌─ Turn {} (P{}) Score: P0={} P1={}", 
            state.turn, state.current_player, state.players[0].score, state.players[1].score);

        if state.phase != Phase::Main {
            if !advance_to_phase(&mut state, &db, Phase::Main, &mut rng, 50) {
                println!("└─ Failed to reach Main phase");
                break;
            }
        }

        // ─ MAIN PHASE ─
        let (_evals, best_seq, nodes, (board_score, live_ev)) = TurnSequencer::plan_full_turn(&state, &db);
        println!("│  Main Phase: {} legal actions, {} DFS nodes", 
            state.get_legal_action_ids(&db).len(), nodes);
        println!("│    Best Score: Board={:.2} + Live={:.2} = {:.2}", 
            board_score, live_ev, board_score + live_ev);

        // Execute best sequence
        for &action in &best_seq {
            if state.step(&db, action).is_err() {
                break;
            }
            if state.phase != Phase::Main {
                break;
            }
        }

        // End Main phase
        let _ = state.step(&db, ACTION_BASE_PASS);

        // ─ LIVESET PHASE (if applicable) ─
        if state.phase == Phase::LiveSet {
            let (liveset_seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
            println!("│  LiveSet Phase: {} cards to place", liveset_seq.len());
            for &action in &liveset_seq {
                let _ = state.step(&db, action);
            }
            let _ = state.step(&db, ACTION_BASE_PASS);
        }

        // ─ AUTO-ADVANCE to next Main/Terminal ─
        while !state.is_terminal() && state.phase != Phase::Main {
            match state.phase {
                Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                    let legal = state.get_legal_action_ids(&db);
                    if !legal.is_empty() {
                        if let Some(&action) = legal.choose(&mut rng) {
                            let _ = state.step(&db, action as i32);
                        } else {
                            break;
                        }
                    } else {
                        break;
                    }
                }
                _ => {
                    state.auto_step(&db);
                }
            }
        }

        println!("│  End-of-turn Score: P0={} P1={}", 
            state.players[0].score, state.players[1].score);
        println!("└─ Turn {} Complete\n", state.turn);

        turn += 1;
    }

    let total_time = game_start.elapsed().as_secs_f32();

    println!("\n╔════════════════════════════════════════════════════════════╗");
    println!("║                      GAME COMPLETE                        ║");
    println!("╚════════════════════════════════════════════════════════════╝\n");

    let winner = if state.players[0].score >= 3 {
        0
    } else if state.players[1].score >= 3 {
        1
    } else {
        -1
    };

    println!("Result:");
    println!("  Winner: P{}", winner);
    println!("  Final Score: P0={} P1={}", state.players[0].score, state.players[1].score);
    println!("  Turns Played: {}", state.turn);
    println!("  Time: {:.3}s\n", total_time);

    if winner >= 0 {
        println!("✓ Game successfully completed!");
    } else {
        println!("⚠ Game reached turn limit without winner");
    }
}
