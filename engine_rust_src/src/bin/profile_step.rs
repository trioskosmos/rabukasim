use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use rand::seq::IndexedRandom;
use rand::SeedableRng;
use rand::prelude::StdRng;

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
        let json = fs::read_to_string(path).expect("Failed to read DB");
        let mut db = CardDatabase::from_json(&json).expect("Failed to parse DB");
        db.is_vanilla = true;
        return db;
    }
    panic!("cards_vanilla.json not found");
}

fn load_deck(path: &str, db: &CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let candidates = [path, &format!("../{}", path), &format!("../../{}", path)];
    
    for candidate in &candidates {
        if let Ok(content) = fs::read_to_string(candidate) {
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

            return (members, lives);
        }
    }
    
    panic!("Could not load deck");
}

fn main() {
    println!("\n[PROFILE] Profiling state.step() calls in random games\n");

    let db = load_vanilla_db();
    let (p0_members, p0_lives) = load_deck("../ai/decks/muse_cup.txt", &db);
    let (p1_members, p1_lives) = load_deck("../ai/decks/muse_cup.txt", &db);

    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

    let mut state = GameState::default();
    state.initialize_game(
        p0_members,
        p1_members,
        energy.clone(),
        energy,
        p0_lives,
        p1_lives,
    );

    let mut rng = StdRng::seed_from_u64(42u64);

    // Suppress debug output
    state.ui.silent = true;

    println!("Advancing to first Main phase...");
    while state.phase != Phase::Main && !state.is_terminal() {
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice | Phase::Response => {
                let legal = state.get_legal_action_ids(&db);
                if !legal.is_empty() {
                    let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
                    let _ = state.step(&db, action);
                } else {
                    let _ = state.step(&db, ACTION_BASE_PASS);
                }
            }
            _ => {
                state.auto_step(&db);
            }
        }
    }

    // Profile Main phase moves
    println!("TURN 1 - First Main phase profiling:\n");
    
    let player = state.current_player;
    println!("Player: P{}", player);

    // Profile each move
    let mut move_count = 0;
    let mut total_moves_time = 0.0;

    while state.phase == Phase::Main {
        let legal = state.get_legal_action_ids(&db);
        if legal.is_empty() {
            let move_start = Instant::now();
            let _ = state.step(&db, ACTION_BASE_PASS);
            let move_time = move_start.elapsed().as_micros() as f64 / 1000.0;
            println!("  Move {}: [PASS] - {:.3}ms", move_count + 1, move_time);
            total_moves_time += move_time;
            move_count += 1;
            break;
        }

        let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
        
        let move_start = Instant::now();
        if state.step(&db, action).is_err() {
            break;
        }
        let move_time = move_start.elapsed().as_micros() as f64 / 1000.0;
        
        move_count += 1;
        println!("  Move {}: action={} - {:.3}ms", move_count, action, move_time);
        total_moves_time += move_time;
        
        if action == ACTION_BASE_PASS {
            break;
        }
    }

    println!("\nTurn 1 Main phase: {} moves in {:.3}ms", move_count, total_moves_time);
    println!("Average per move: {:.3}ms", total_moves_time / move_count as f64);

    // Check if abilities are actually present
    println!("\n[CHECK] Verifying card abilities in vanilla DB:");
    let mut total_abilities = 0usize;
    let mut cards_with_abilities = 0usize;

    for (_, member) in &db.members {
        if !member.abilities.is_empty() {
            total_abilities += member.abilities.len();
            cards_with_abilities += 1;
        }
    }

    for (_, live) in &db.lives {
        if !live.abilities.is_empty() {
            total_abilities += live.abilities.len();
            cards_with_abilities += 1;
        }
    }

    println!("  Total cards: {} members, {} lives", db.members.len(), db.lives.len());
    println!("  Cards with abilities: {}", cards_with_abilities);
    println!("  Total abilities: {}", total_abilities);
    
    if total_abilities == 0 {
        println!("  ✓ Vanilla game has NO abilities (as expected)");
    } else {
        println!("  ⚠ WARNING: Vanilla game has {} abilities!", total_abilities);
    }

    // Now profile a full turn (Main + LiveSet phases)
    println!("\n[FULL TURN] Now playing full turn including LiveSet...\n");

    let turn_start = Instant::now();
    
    // Skip to next Main phase
    while !state.is_terminal() && state.phase != Phase::Main {
        state.auto_step(&db);
    }

    let player2 = state.current_player;
    move_count = 0;
    total_moves_time = 0.0;

    while state.phase == Phase::Main {
        let legal = state.get_legal_action_ids(&db);
        if legal.is_empty() {
            let move_start = Instant::now();
            let _ = state.step(&db, ACTION_BASE_PASS);
            let move_time = move_start.elapsed().as_micros() as f64 / 1000.0;
            total_moves_time += move_time;
            move_count += 1;
            break;
        }

        let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
        
        let move_start = Instant::now();
        if state.step(&db, action).is_err() {
            break;
        }
        let move_time = move_start.elapsed().as_micros() as f64 / 1000.0;
        total_moves_time += move_time;
        move_count += 1;
        
        if action == ACTION_BASE_PASS {
            break;
        }
    }

    // LiveSet phases
    let mut liveset_count = 0usize;
    let liveset_start = Instant::now();
    while state.phase == Phase::LiveSet {
        let legal = state.get_legal_action_ids(&db);
        if !legal.is_empty() {
            let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
            let _ = state.step(&db, action);
            liveset_count += 1;
        } else {
            break;
        }
    }
    let liveset_time = liveset_start.elapsed().as_millis();

    // Auto-step
    let auto_start = Instant::now();
    while !state.is_terminal() && state.phase != Phase::Main {
        state.auto_step(&db);
    }
    let auto_time = auto_start.elapsed().as_millis();

    let turn_total = turn_start.elapsed().as_millis();

    println!("TURN 2 - Full turn breakdown:");
    println!("  Player: P{}", player2);
    println!("  Main phase: {} moves in {:.3}ms", move_count, total_moves_time);
    println!("  LiveSet phase: {} selections in {}ms", liveset_count, liveset_time);
    println!("  Auto-step phases: {}ms", auto_time);
    println!("  TOTAL: {}ms", turn_total);
}
