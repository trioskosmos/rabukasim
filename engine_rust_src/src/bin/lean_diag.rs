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

fn main() {
    let db = load_vanilla_db();
    println!("=== LEAN DIAGNOSTICS ===\n");

    // Get some member and life cards
    let mut members = Vec::new();
    let mut lives = Vec::new();
    for (&id, _) in db.members.iter().take(48) {
        members.push(id);
    }
    for (&id, _) in db.lives.iter().take(12) {
        lives.push(id);
    }

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

    // Advance to first Main phase
    let mut rng = StdRng::seed_from_u64(100);
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

    println!("Now in Main phase. Diagnosing turn 1:\n");
    
    let turn_start = Instant::now();
    
    // Get legal actions
    let mut actions = vec![];
    let action_gen_time = Instant::now();
    let legal = state.get_legal_action_ids(&db);
    for &action in &legal {
        if action != ACTION_BASE_PASS {
            actions.push(action);
        }
    }
    println!("[ACTION GENERATION] {} legal actions generated in {:.3}ms", 
        legal.len(), action_gen_time.elapsed().as_secs_f32() * 1000.0);

    // Test: Clone state costs
    let clone_start = Instant::now();
    let _cloned = state.clone();
    let clone_cost = clone_start.elapsed();
    println!("[STATE CLONE] Single clone took {:.3}ms", clone_cost.as_secs_f32() * 1000.0);

    // Test: Step cost
    let mut test_state = state.clone();
    let step_start = Instant::now();
    if actions.len() > 0 {
        let _ = test_state.step(&db, actions[0]);
    }
    let step_cost = step_start.elapsed();
    println!("[STATE STEP] Single step took {:.3}ms\n", step_cost.as_secs_f32() * 1000.0);
    
    // Recursive counting (what simple_game is doing)
    let count_start = Instant::now();
    fn count_recursive(state: &GameState, db: &CardDatabase, depth: usize, max_depth: usize) -> usize {
        if state.phase != Phase::Main || depth >= max_depth {
            return 1;
        }
        let legal = state.get_legal_action_ids(db);
        let mut total = 0;
        for &action in &legal {
                if action != ACTION_BASE_PASS {
                let mut next = state.clone();
                    if next.step(db, action).is_ok() {
                    total += count_recursive(&next, db, depth + 1, max_depth);
                }
            }
        }
        let mut pass_state = state.clone();
        if pass_state.step(db, ACTION_BASE_PASS).is_ok() {
            total += 1;
        }
        total
    }
    
    let seq_count = count_recursive(&state, &db, 0, 10);
    let count_time = count_start.elapsed();
    println!("[SEQUENCE COUNTING] Recursive count to depth 10:");
    println!("  Sequences: {}", seq_count);
    println!("  Time: {:.3}ms", count_time.as_secs_f32() * 1000.0);
    println!("  Est. clones: {} (if each node cloned once)", seq_count * 2);
    
    // Plan turn (our optimized version)
    let plan_start = Instant::now();
    let (_seq, _val, _brk, evals) = engine_rust::core::logic::turn_sequencer::TurnSequencer::plan_full_turn(&state, &db);
    let plan_time = plan_start.elapsed();
    println!("\n[PLAN TURN] Optimized plan_full_turn:");
    println!("  Evaluations: {}", evals);
    println!("  Time: {:.3}ms", plan_time.as_secs_f32() * 1000.0);
    
    let _total_time = turn_start.elapsed();
    println!("\n[TURN TOTAL] Complete turn 1:");
    println!("  Without counting: {:.3}ms", plan_time.as_secs_f32() * 1000.0);
    println!("  With counting (current simple_game): {:.3}ms", 
        (count_time.as_secs_f32() + plan_time.as_secs_f32()) * 1000.0);
    println!("  Overhead from counting: {:.3}ms ({:.1}% of total)", 
        count_time.as_secs_f32() * 1000.0,
        (count_time.as_secs_f32() / (count_time.as_secs_f32() + plan_time.as_secs_f32())) * 100.0);
}
