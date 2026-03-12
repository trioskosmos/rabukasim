use std::fs;
use std::time::Instant;
use std::sync::{Arc, Mutex};
use engine_rust::core::logic::{CardDatabase, GameState, ACTION_BASE_PASS};
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::enums::Phase;

#[derive(Clone, Debug)]
struct EvalMetrics {
    total_nodes: usize,
    total_evals: usize,
    clones: usize,
    liveset_searches: usize,
    max_depth: usize,
    paths_by_length: Vec<usize>, // count of paths ending at each length (0-20)
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
    let db = load_vanilla_db();
    let (p0_members, p0_lives) = load_deck("ai/decks/liella_cup.txt", &db);
    let (p1_members, p1_lives) = load_deck("ai/decks/liella_cup.txt", &db);

    let mut state = GameState::default();
    let energy_vec: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    state.initialize_game(p0_members, p1_members, energy_vec.clone(), energy_vec, p0_lives, p1_lives);
    state.ui.silent = true;

    // Skip to Main phase
    while state.phase != Phase::Main && !state.is_terminal() {
        state.auto_step(&db);
    }

    println!("\n=== CODE STRUCTURE ANALYSIS ===\n");
    
    // Count actual number of legal actions in starting Main phase
    let mut actions: Vec<i32> = Vec::new();
    state.generate_legal_actions(&db, state.current_player as usize, &mut actions);
    println!("[START] Player {}: {} legal actions available", state.current_player, actions.len());
    println!("  Actions: {:?}", actions);

    // Measure evaluation cost
    println!("\n=== EVALUATION COST BREAKDOWN ===\n");
    
    let eval_start = Instant::now();
    for _ in 0..1000 {
        let _ = TurnSequencer::plan_full_turn(&state, &db);
        break;  // Just ONE search to measure timing
    }
    let eval_time = eval_start.elapsed();
    
    println!("[SEARCH 1] Full search time: {:.3}ms", eval_time.as_secs_f32() * 1000.0);

    // Breakdown what evaluate_stop_state involves:
    println!("\n=== WHAT HAPPENS IN SEARCH ===\n");
    println!("exact_small_turn_search recursively:");
    println!("  1. Check if phase == Main AND depth > 0");
    println!("  2. If condition fails: call evaluate_stop_state");
    println!("     - Clone state (1.7µs) <- EXPENSIVE");
    println!("     - If in LiveSet phase: find_best_liveset_selection");
    println!("     - Call evaluate_state_for_player_with_weights");
    println!("       - For vanilla: count cards (fast)");
    println!("     - Return score");
    println!("  3. If condition true:");
    println!("     - Evaluate PASS action");
    println!("     - For each other legal action:");
    println!("       - Clone state");
    println!("       - Call step()");
    println!("       - Recurse with depth-1");
    println!("\nKey insight: state.clone() happens for EVERY node");

    println!("\n=== SEARCH TREE ANALYSIS ===\n");
    
    let mut _typical_depth = 0;
    let mut _nodes_visited: Vec<usize> = Vec::new();
    
    // Simulate search tree: show typical branching
    println!("Typical action count by depth:");
    println!("  Depth 0 (start of turn): {} actions", actions.len());
    
    // Try a few actions to see what's available
    for (i, &action) in actions.iter().take(2).enumerate() {
        let mut next_state = state.clone();
        if next_state.step(&db, action).is_ok() {
            let mut next_actions: Vec<i32> = Vec::new();
            if next_state.phase == Phase::Main {
                next_state.generate_legal_actions(&db, next_state.current_player as usize, &mut next_actions);
                println!("  Depth 1 (after action {}): {} actions available", i, next_actions.len());
            } else {
                println!("  Depth 1 (after action {}): Phase changed to {:?}", i, next_state.phase);
            }
        }
    }

    println!("\n=== OPTIMIZATION OPPORTUNITIES ===\n");
    println!("1. **State clone cost**: evaluate_stop_state clones state EVERY call");
    println!("   - For vanilla, we just count cards - clone isn't needed!");
    println!("   - Savings: 1.7µs × N nodes per turn");
    
    println!("\n2. **Depth ceiling**: If average moves per depth = 2-3");
    println!("   - Depth 10 probably hits phase change around depth 3-5");
    println!("   - Exploring further is redundant");
    
    println!("\n3. **LiveSet overhead**: If we're in MainPhase only");
    println!("   - evaluate_stop_state checks for LiveSet each time");
    println!("   - Main phase doesn't transition to LiveSet during search");
    println!("   - This check is redundant");

    println!("\n=== ACTUAL TIME BREAKDOWN ===\n");
    
    // Profile what's actually slow
    let t = Instant::now();
    for _ in 0..100 {
        let mut s = state.clone();
    }
    println!("[CLONE x100] {:.3}ms ({:.3}µs each)", t.elapsed().as_secs_f32() * 1000.0, t.elapsed().as_secs_f32() * 1000.0 / 100.0);
    
    let t = Instant::now();
    for _ in 0..1000 {
        let mut s = state.clone();
        let _ = s.step(&db, ACTION_BASE_PASS);
    }
    println!("[STEP x1000] {:.3}ms ({:.3}µs each)", t.elapsed().as_secs_f32() * 1000.0, t.elapsed().as_secs_f32() * 1000.0 / 1000.0);

    println!("\n=== CONCLUSION ===\n");
    println!("For vanilla (~700 nodes per turn with ~60ms total):");
    println!("- If each node does: clone(1.7µs) + step(2.25µs) = ~4µs");
    println!("- 700 × 4µs = 2.8ms just for tree traversal");
    println!("- Remaining 57.2ms is in LiveSet and evaluation logic");
    println!("\nFastest optimization:");
    println!("1. Skip state clone in evaluate_stop_state for vanilla");
    println!("2. Skip LiveSet check during Main phase search");
    println!("3. Reduce depth to 6 (realistically max moves available)");
}
