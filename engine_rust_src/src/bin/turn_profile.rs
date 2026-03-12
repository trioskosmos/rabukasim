use std::fs;
use std::time::Instant;

use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{GameState, CardDatabase, ACTION_BASE_PASS};
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
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

fn count_legal_actions_recursive(state: &GameState, db: &CardDatabase, depth: usize, max_depth: usize) -> usize {
    if state.phase != Phase::Main || depth >= max_depth {
        return 1;
    }
    let legal = state.get_legal_action_ids(db);
    let mut total = 0;
    for &action in &legal {
        if action != ACTION_BASE_PASS {
            let mut next = state.clone();
            if next.step(db, action).is_ok() {
                total += count_legal_actions_recursive(&next, db, depth + 1, max_depth);
            }
        }
    }
    let mut pass_state = state.clone();
    if pass_state.step(db, ACTION_BASE_PASS).is_ok() {
        total += 1;
    }
    total
}

fn main() {
    let db = load_vanilla_db();
    let mut members = Vec::new();
    let mut lives = Vec::new();
    for (&id, _) in db.members.iter().take(48) {
        members.push(id);
    }
    for (&id, _) in db.lives.iter().take(12) {
        lives.push(id);
    }

    let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();

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

    let mut rng = StdRng::seed_from_u64(100);
    
    // Advance to first Main phase
    while state.phase != Phase::Main && !state.is_terminal() {
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice => {
                let legal = state.get_legal_action_ids(&db);
                if let Some(&action) = legal.choose(&mut rng) {
                    let _ = state.step(&db, action);
                }
            }
            _ => state.auto_step(&db),
        }
    }

    println!("=== TURN-BY-TURN PROFILING ===\n");
    println!("TURN | DEPTH | BRANCHES | PLAN_TIME | EVALS | AVG_EV_TIME | TOTAL_TIME | %DEPTH");
    println!("-----|-------|----------|-----------|-------|-------------|------------|------");

    let mut total_main_time = 0.0;
    let mut main_turns = 0;

    while !state.is_terminal() && main_turns < 20 {
        main_turns += 1;

        if state.phase == Phase::Main {
            let depth = 10;
            let branches_start = Instant::now();
            let branches = count_legal_actions_recursive(&state, &db, 0, depth);
            let branches_time = branches_start.elapsed();
            
            let plan_start = Instant::now();
            let (_, _, _, evals) = TurnSequencer::plan_full_turn(&state, &db);
            let plan_time = plan_start.elapsed();
            
            let avg_time_per_eval = if evals > 0 {
                (plan_time.as_secs_f32() * 1000.0) / evals as f32
            } else {
                0.0
            };
            
            let percent_of_depth = (branches as f32).log2();
            
            println!("{:4} | {:5} | {:8} | {:9.2}ms | {:5} | {:11.3}ms | {:10.2}ms | {:.1}%",
                main_turns,
                depth,
                branches,
                branches_time.as_secs_f32() * 1000.0,
                evals,
                avg_time_per_eval,
                plan_time.as_secs_f32() * 1000.0,
                percent_of_depth * 10.0
            );
            
            total_main_time += plan_time.as_secs_f32();
            
            // Execute the turn to advance state
            let (seq, _, _, _) = TurnSequencer::plan_full_turn(&state, &db);
            for &action in &seq {
                if state.phase != Phase::Main {
                    break;
                }
                if state.step(&db, action).is_err() {
                    break;
                }
            }
            if state.phase == Phase::Main {
                let _ = state.step(&db, ACTION_BASE_PASS);
            }
        }
        
        // Handle other phases
        while state.phase != Phase::Main && !state.is_terminal() && state.phase != Phase::Terminal {
            match state.phase {
                Phase::LiveSet => {
                    let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
                    for &action in &seq {
                        let _ = state.step(&db, action);
                    }
                    let _ = state.step(&db, ACTION_BASE_PASS);
                }
                Phase::Active | Phase::Draw | Phase::Energy | Phase::PerformanceP1 | Phase::PerformanceP2 => {
                    state.auto_step(&db);
                }
                Phase::LiveResult => {
                    let legal = state.get_legal_action_ids(&db);
                    if let Some(&action) = legal.choose(&mut rng) {
                        let _ = state.step(&db, action);
                    } else {
                        let _ = state.step(&db, ACTION_BASE_PASS);
                    }
                }
                Phase::Terminal => break,
                _ => state.auto_step(&db),
            }
        }
    }

    let total_time = game_start.elapsed();
    println!("\n[GAME SUMMARY]");
    println!("Total game time: {:.2}ms", total_time.as_secs_f32() * 1000.0);
    println!("Main planning time: {:.2}ms ({} turns)", total_main_time * 1000.0, main_turns);
    println!("Avg per main turn: {:.2}ms", (total_main_time * 1000.0) / main_turns as f32);
    println!("Overhead: {:.2}ms", (total_time.as_secs_f32() - total_main_time) * 1000.0);
}
