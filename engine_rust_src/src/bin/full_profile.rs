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

fn main() {
    let db = load_vanilla_db();
    println!("=== FULL GAME PROFILING ===\n");

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

    let init_time = game_start.elapsed();
    println!("[INIT] Game initialized in {:.3}ms\n", init_time.as_secs_f32() * 1000.0);

    let mut rng = StdRng::seed_from_u64(100);
    
    // Advance to first Main phase
    println!("[SETUP PHASE]");
    let setup_start = Instant::now();
    let mut setup_turns = 0;
    while state.phase != Phase::Main && !state.is_terminal() {
        match state.phase {
            Phase::Rps | Phase::MulliganP1 | Phase::MulliganP2 | Phase::TurnChoice => {
                let legal = state.get_legal_action_ids(&db);
                if let Some(&action) = legal.choose(&mut rng) {
                    let _ = state.step(&db, action);
                }
            }
            _ => {
                let auto_start = Instant::now();
                state.auto_step(&db);
                let auto_time = auto_start.elapsed();
                if auto_time.as_secs_f32() > 0.001 {
                    println!("  Auto-step took {:.3}ms (phase: {:?})", auto_time.as_secs_f32() * 1000.0, state.phase);
                }
            }
        }
        setup_turns += 1;
        if setup_turns > 100 {
            break;
        }
    }
    println!("  Total setup: {:.3}ms in {} steps\n", setup_start.elapsed().as_secs_f32() * 1000.0, setup_turns);

    let mut total_main_time = 0.0;
    let mut main_turns = 0;

    // Main game loop
    println!("[MAIN TURNS]");
    while !state.is_terminal() && main_turns < 20 {
        let turn_start = Instant::now();
        main_turns += 1;

        match state.phase {
            Phase::Main => {
                let plan_start = Instant::now();
                let (best_seq, _, _, evals) = TurnSequencer::plan_full_turn(&state, &db);
                let plan_time = plan_start.elapsed();
                
                let exec_start = Instant::now();
                for &action in &best_seq {
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
                let exec_time = exec_start.elapsed();
                
                let turn_time = turn_start.elapsed();
                println!("  Turn {:2}: plan={:.2}ms exec={:.2}ms evals={:5} total={:.2}ms", 
                    main_turns, plan_time.as_secs_f32()*1000.0, exec_time.as_secs_f32()*1000.0, 
                    evals, turn_time.as_secs_f32()*1000.0);
                total_main_time += turn_time.as_secs_f32();
            }
            Phase::LiveSet => {
                let ls_start = Instant::now();
                let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
                for &action in &seq {
                    let _ = state.step(&db, action);
                }
                let _ = state.step(&db, ACTION_BASE_PASS);
                let ls_time = ls_start.elapsed();
                println!("  LiveSet: {:.2}ms", ls_time.as_secs_f32()*1000.0);
                total_main_time += ls_time.as_secs_f32();
            }
            Phase::Active | Phase::Draw | Phase::Energy | Phase::PerformanceP1 | Phase::PerformanceP2 => {
                let auto_start = Instant::now();
                state.auto_step(&db);
                let auto_time = auto_start.elapsed();
                if auto_time.as_secs_f32() > 0.001 {
                    println!("  Auto {:?}: {:.2}ms", state.phase, auto_time.as_secs_f32()*1000.0);
                }
            }
            Phase::LiveResult => {
                let manual_start = Instant::now();
                let legal = state.get_legal_action_ids(&db);
                if let Some(&action) = legal.choose(&mut rng) {
                    let _ = state.step(&db, action);
                }
                let manual_time = manual_start.elapsed();
                if manual_time.as_secs_f32() > 0.001 {
                    println!("  LiveResult: {:.2}ms", manual_time.as_secs_f32()*1000.0);
                }
            }
            Phase::Terminal => break,
            _ => {
                state.auto_step(&db);
            }
        }
    }

    let total_time = game_start.elapsed();
    println!("\n[SUMMARY]");
    println!("Total game time: {:.3}ms ({:.2}s)", total_time.as_secs_f32()*1000.0, total_time.as_secs_f32());
    println!("Main turn time: {:.3}ms", total_main_time*1000.0);
    println!("Main turns played: {}", main_turns);
    if main_turns > 0 {
        println!("Avg per main turn: {:.2}ms", (total_main_time*1000.0) / main_turns as f32);
    }
    println!("Other time: {:.2}ms", (total_time.as_secs_f32() - total_main_time)*1000.0);
}
