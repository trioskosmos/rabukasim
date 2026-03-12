use std::fs;
use std::time::Instant;
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use engine_rust::core::logic::turn_sequencer::{TurnSequencer};
use engine_rust::core::enums::Phase;

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
    (members, lives)
}

fn main() {
    println!("\n=== MICRO-BENCHMARKS ===\n");
    
    let db = load_vanilla_db();
    let (p0_members, p0_lives) = load_deck("ai/decks/liella_cup.txt", &db);
    let (p1_members, p1_lives) = load_deck("ai/decks/liella_cup.txt", &db);

    let mut state = GameState::default();
    let energy_vec: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    
    println!("[INIT] Creating game state...");
    let t = Instant::now();
    state.initialize_game(
        p0_members,
        p1_members,
        energy_vec.clone(),
        energy_vec,
        p0_lives,
        p1_lives,
    );
    println!("  Game init: {:.3}ms", t.elapsed().as_secs_f32() * 1000.0);
    state.ui.silent = true;

    // Measure state clone
    let t = Instant::now();
    for _ in 0..1000 {
        let _ = state.clone();
    }
    println!("[CLONE] 1000 clones: {:.3}µs per clone", t.elapsed().as_secs_f32() * 1_000_000.0 / 1000.0);

    // Measure action generation
    let mut actions: Vec<i32> = Vec::new();
    let t = Instant::now();
    for _ in 0..10000 {
        actions.clear();
        state.generate_legal_actions(&db, state.current_player as usize, &mut actions);
    }
    println!("[ACTIONS] 10000 gens: {:.3}µs per gen ({} actions)", t.elapsed().as_secs_f32() * 1_000_000.0 / 10000.0, actions.len());

    // Measure state.step()
    let t = Instant::now();
    for _ in 0..1000 {
        let mut temp = state.clone();
        let _ = temp.step(&db, ACTION_BASE_PASS);
    }
    println!("[STEP] 1000 steps: {:.3}µs per step", t.elapsed().as_secs_f32() * 1_000_000.0 / 1000.0);

    // Measure full op
    let t = Instant::now();
    for _ in 0..1000 {
        let mut acts: Vec<i32> = Vec::new();
        state.generate_legal_actions(&db, state.current_player as usize, &mut acts);
        if !acts.is_empty() {
            let mut temp = state.clone();
            let _ = temp.step(&db, acts[0]);
        }
    }
    println!("[FULL-OP] 1000x (gen+clone+step): {:.3}µs per op", t.elapsed().as_secs_f32() * 1_000_000.0 / 1000.0);

    println!("\n=== PHASE TRANSITION ===\n");
    
    // Skip to Main phase
    let t = Instant::now();
    while state.phase != Phase::Main && !state.is_terminal() {
        state.auto_step(&db);
    }
    println!("[STARTUP] Reached Main phase in {:.3}s", t.elapsed().as_secs_f32());
    println!("  Current state: Player={}, Phase={:?}", state.current_player, state.phase);

    // Generate actions
    let mut main_actions: Vec<i32> = Vec::new();
    state.generate_legal_actions(&db, state.current_player as usize, &mut main_actions);
    println!("  Legal actions in Main: {}", main_actions.len());

    println!("\n=== SINGLE TURN SEARCH ===\n");

    let search_start = Instant::now();
    let (best_seq, best_val, (board_ev, live_ev), evals) = TurnSequencer::plan_full_turn(&state, &db);
    let search_elapsed = search_start.elapsed();

    println!("[SEARCH] Completed in {:.3}ms", search_elapsed.as_secs_f32() * 1000.0);
    println!("  Best sequence: {} actions", best_seq.len());
    println!("  Evaluation: {:.2} (board={:.2}, live={:.2})", best_val, board_ev, live_ev);
    println!("  Evaluations run: {}", evals);
    println!("  Time per eval: {:.3}µs", search_elapsed.as_secs_f32() * 1_000_000.0 / evals.max(1) as f32);

    println!("\n=== EXECUTE SEQUENCE ===\n");

    let exec_start = Instant::now();
    for &action in &best_seq {
        if state.phase != Phase::Main {
            break;
        }
        let legal = state.get_legal_action_ids(&db);
        if !legal.contains(&action) {
            break;
        }
        let _ = state.step(&db, action);
    }
    println!("[EXEC] Executed {} actions in {:.3}ms", best_seq.len(), exec_start.elapsed().as_secs_f32() * 1000.0);
    
    if state.phase == Phase::Main {
        let _ = state.step(&db, ACTION_BASE_PASS);
        println!("[PASS] Turn ended");
    }

    println!("\n=== ANALYSIS ===\n");
    println!("Turn search (search + exec): {:.3}ms", (search_elapsed + exec_start.elapsed()).as_secs_f32() * 1000.0);
    println!("If repeated 10 times: {:.3}s", (search_elapsed + exec_start.elapsed()).as_secs_f32() * 1000.0 * 10.0 / 1000.0);
}
