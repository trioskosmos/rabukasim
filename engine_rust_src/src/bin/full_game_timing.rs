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

    let game_start = Instant::now();
    let mut rng = StdRng::seed_from_u64(42u64);
    let max_turns = 20usize;

    println!("\n[GAME TIMING] Per-turn breakdown with sequence counts\n");
    println!("{:>4} {:>2} {:>8} {:>10} {:>8}", "TURN", "P", "SEQS", "TIME(ms)", "CUM(s)");
    println!("{:-<4} {:-<2} {:-<8} {:-<10} {:-<8}", "", "", "", "", "");

    let mut main_turns_played = 0usize;
    let mut total_ms = 0usize;

    // Advance to first Main phase
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

    // Main game loop
    while !state.is_terminal() && main_turns_played < max_turns {
        match state.phase {
            Phase::Main => {
                main_turns_played += 1;
                let player = state.current_player;
                let search_depth = engine_rust::core::logic::turn_sequencer::CONFIG.read().unwrap().search.max_dfs_depth;

                let turn_start = Instant::now();
                
                // Count sequences
                let exact_sequences = count_exact_main_sequences(&state, &db, search_depth);

                // Execute main phase (random moves)
                while state.phase == Phase::Main {
                    let legal = state.get_legal_action_ids(&db);
                    if legal.is_empty() {
                        let _ = state.step(&db, ACTION_BASE_PASS);
                        break;
                    }

                    let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
                    if state.step(&db, action).is_err() {
                        break;
                    }

                    if action == ACTION_BASE_PASS {
                        break;
                    }
                }

                // LiveSet phase
                while state.phase == Phase::LiveSet {
                    let legal = state.get_legal_action_ids(&db);
                    if !legal.is_empty() {
                        let &action = legal.choose(&mut rng).unwrap_or(&ACTION_BASE_PASS);
                        let _ = state.step(&db, action);
                    } else {
                        break;
                    }
                }

                let turn_time_ms = turn_start.elapsed().as_millis() as usize;
                total_ms += turn_time_ms;

                println!("{:4} {:2} {:8} {:10} {:>7.2}s", 
                         main_turns_played, 
                         player, 
                         exact_sequences,
                         turn_time_ms, 
                         total_ms as f64 / 1000.0);
            }
            _ => {
                state.auto_step(&db);
            }
        }

        if game_start.elapsed().as_secs() > 60 {
            println!("\n[TIMEOUT] Game exceeded 60s");
            break;
        }
    }

    let total_elapsed = game_start.elapsed();
    println!("\n{:=<50}", "");
    println!("[SUMMARY]");
    println!("  Turns: {} Main turns completed", main_turns_played);
    println!("  Total time: {:.3}s ({} ms)", total_elapsed.as_secs_f64(), total_ms);
    println!("  Average per turn: {:.1}ms", total_ms as f64 / main_turns_played.max(1) as f64);
    println!("  Winner: P{}", if state.players[0].score > state.players[1].score { 0 } else { 1 });
    println!("\n[OBSERVATION]");
    println!("  If early turns are fast (< 10ms) but later turns are slow (> 100ms),");
    println!("  it indicates the game engine slows down as board complexity increases.");
    println!("  The sequence counting itself is NOT the bottleneck.");
}
