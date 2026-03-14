use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use rand::seq::IndexedRandom;
use rand::SeedableRng;
use rand::prelude::StdRng;
use smallvec::SmallVec;

fn count_exact_main_sequences(state: &GameState, db: &CardDatabase, max_depth: usize) -> usize {
    fn recurse(state: &GameState, db: &CardDatabase, depth: usize, max_depth: usize) -> usize {
        if state.phase != Phase::Main {
            return 1;
        }
        if depth >= max_depth {
            return 1;
        }

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        let mut total = 0usize;
        let mut saw_non_pass = false;
        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            saw_non_pass = true;
            let mut next_state = state.clone();
            if next_state.step(db, action).is_ok() {
                total += recurse(&next_state, db, depth + 1, max_depth);
            }
        }

        let mut pass_state = state.clone();
        if pass_state.step(db, ACTION_BASE_PASS).is_ok() {
            total += 1;
        } else if !saw_non_pass {
            total += 1;
        }

        total
    }

    recurse(state, db, 0, max_depth)
}

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

    println!("\n[QUICK DIAGNOSTIC] Advance to first Main phase...");
    let setup_start = Instant::now();
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
    println!("[SETUP] took {:.3}s\n", setup_start.elapsed().as_secs_f64());

    // Now analyze the first Main turn
    let search_depth = engine_rust::core::logic::turn_sequencer::get_config().read().unwrap().search.max_dfs_depth;
    println!("[TURN 1 ANALYSIS]");
    println!("  Player: P{}", state.current_player);
    println!("  Phase: {:?}", state.phase);

    // STEP 1: Count sequences
    let count_start = Instant::now();
    let exact_sequences = count_exact_main_sequences(&state, &db, search_depth);
    let count_time = count_start.elapsed();
    println!("  1. COUNT SEQUENCES: {} sequences in {:.3}s", exact_sequences, count_time.as_secs_f64());

    // Save state for next step
    // STEP 2: Execute one random move
    println!("\n  2. EXECUTE RANDOM MOVE:");
    let main_start = Instant::now();
    let mut move_num = 0usize;
    while state.phase == Phase::Main {
        let legal = state.get_legal_action_ids(&db);
        if legal.is_empty() {
            let _ = state.step(&db, ACTION_BASE_PASS);
            move_num += 1;
            println!("     Move {}: [PASS]", move_num);
            break;
        }

        let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
        
        let move_start = Instant::now();
        if state.step(&db, action).is_err() {
            break;
        }
        let move_time = move_start.elapsed();
        
        move_num += 1;
        let action_str = if action == ACTION_BASE_PASS {
            "[PASS]".to_string()
        } else {
            format!("[ACTION {}]", action)
        };
        println!("     Move {}: {} in {:.3}s", move_num, action_str, move_time.as_secs_f64());
        
        if action == ACTION_BASE_PASS {
            break;
        }
    }
    let main_time = main_start.elapsed();
    println!("  Main phase total: {:.3}s ({} moves)", main_time.as_secs_f64(), move_num);

    // STEP 3: Rest of turn (LiveSet, auto_step, etc.)
    println!("\n  3. LIVESETS & AUTO-STEP:");
    let rest_start = Instant::now();
    while !state.is_terminal() {
        if state.phase == Phase::Main {
            break; // Next turn
        }
        
        let phase = state.phase.clone();
        let phase_start = Instant::now();
        let legal = state.get_legal_action_ids(&db);
        if state.phase == Phase::LiveSet && !legal.is_empty() {
            let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
            let _ = state.step(&db, action);
        } else {
            state.auto_step(&db);
        }
        let phase_time = phase_start.elapsed();
        
        if phase_time.as_millis() > 0 {
            println!("     Phase {:?}: {:.3}s", phase, phase_time.as_secs_f64());
        }
    }
    let rest_time = rest_start.elapsed();
    println!("  Total non-Main phases: {:.3}s", rest_time.as_secs_f64());

    let turn_total = count_time + main_time + rest_time;
    println!("\n[BREAKDOWN]");
    println!("  Sequence count: {:.3}s ({:.1}%)", count_time.as_secs_f64(), 
             count_time.as_secs_f64() / turn_total.as_secs_f64() * 100.0);
    println!("  Main phase moves: {:.3}s ({:.1}%)", main_time.as_secs_f64(),
             main_time.as_secs_f64() / turn_total.as_secs_f64() * 100.0);
    println!("  LiveSet/auto-step: {:.3}s ({:.1}%)", rest_time.as_secs_f64(),
             rest_time.as_secs_f64() / turn_total.as_secs_f64() * 100.0);
    println!("  TOTAL TURN: {:.3}s", turn_total.as_secs_f64());
    
    println!("\n[CONCLUSION]");
    if count_time.as_secs_f64() > 0.1 {
        println!("  ⚠ Sequence counting is slow ({:.3}s)", count_time.as_secs_f64());
    } else {
        println!("  ✓ Sequence counting is fast ({:.3}s)", count_time.as_secs_f64());
    }
    if main_time.as_secs_f64() > 0.1 {
        println!("  ⚠ Main phase execution is slow ({:.3}s)", main_time.as_secs_f64());
    } else {
        println!("  ✓ Main phase execution is fast ({:.3}s)", main_time.as_secs_f64());
    }
    if rest_time.as_secs_f64() > 0.1 {
        println!("  ⚠ LiveSet/auto-step is slow ({:.3}s)", rest_time.as_secs_f64());
    } else {
        println!("  ✓ LiveSet/auto-step is fast ({:.3}s)", rest_time.as_secs_f64());
    }
}
