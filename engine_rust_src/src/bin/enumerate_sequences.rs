use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::enums::Phase;
use serde_json::json;
use smallvec::SmallVec;
use engine_rust::core::{ACTION_BASE_PASS};
use std::fs;

fn main() {
    // Load vanilla database
    let db = load_vanilla_db();
    let mut state = GameState::default();
    
    // Build decks from actual cards in database
    let mut dummy_deck = Vec::new();
    let mut dummy_lives = Vec::new();
    
    // Collect real member cards
    for &id in db.members.keys() {
        dummy_deck.push(id);
        if dummy_deck.len() >= 48 {
            break;
        }
    }
    
    // Pad if needed
    while dummy_deck.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            dummy_deck.push(id);
        } else {
            break;
        }
    }
    
    // Collect real live cards
    for &id in db.lives.keys() {
        dummy_lives.push(id);
        if dummy_lives.len() >= 12 {
            break;
        }
    }
    
    // Pad if needed
    while dummy_lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            dummy_lives.push(id);
        } else {
            break;
        }
    }
    
    // Collect energy cards
    let dummy_energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
    
    state.initialize_game(
        dummy_deck.clone(),
        dummy_deck.clone(),
        dummy_energy.clone(),
        dummy_energy.clone(),
        dummy_lives.clone(),
        dummy_lives.clone(),
    );
    
    // Step through mulligan etc to reach Main phase
    while state.phase != Phase::Main {
        let legal = state.get_legal_action_ids(&db);
        if !legal.is_empty() {
            let action = legal[0];
            if state.step(&db, action).is_err() {
                break;
            }
        } else {
            break;
        }
    }
    
    // Get initial player to search from
    let root_player = state.current_player as usize;
    
    println!("Initial state - Current player: {}", root_player);
    let mut test_actions = SmallVec::<[i32; 64]>::new();
    state.generate_legal_actions(&db, state.current_player as usize, &mut test_actions);
    println!("Legal actions at start: {} actions", test_actions.len());
    
    println!("\nEnumerating ALL legal sequences from root state...");
    
    // Single DFS pass: count all sequences at each depth
    let mut stats = SequenceStats::new();
    enumerate_sequences(&state, &db, root_player, 0, &mut stats);
    
    // Output results
    println!("\n=== SEQUENCE ENUMERATION RESULTS ===");
    println!("Total sequences explored (leaf nodes): {}", stats.total_sequences);
    println!("\nSequences by depth:");
    for (depth, count) in &stats.by_depth {
        let ratio = if *depth == 0 {
            1.0
        } else {
            *count as f32 / stats.by_depth.get(&(depth - 1)).copied().unwrap_or(1) as f32
        };
        println!("  Depth {}: {} sequences (branching ratio from prev: {:.2}x)", depth, count, ratio);
    }
    
    // Compute average branching factor
    if stats.by_depth.len() >= 2 {
        let mut total_ratio = 0.0;
        let mut count = 0;
        for (depth, seq_count) in &stats.by_depth {
            if *depth > 0 {
                let prev_count = stats.by_depth.get(&(depth - 1)).copied().unwrap_or(1);
                if prev_count > 0 {
                    total_ratio += *seq_count as f32 / prev_count as f32;
                    count += 1;
                }
            }
        }
        if count > 0 {
            let avg_branching = total_ratio / count as f32;
            println!("\nAverage branching factor (seq_ratio): {:.2}x", avg_branching);
        }
    }
    
    // JSON output
    let json_stats = json!({
        "total_sequences": stats.total_sequences,
        "max_depth_explored": stats.by_depth.keys().max().copied().unwrap_or(0),
        "by_depth": stats.by_depth,
    });
    
    println!("\nJSON output:");
    println!("{}", serde_json::to_string_pretty(&json_stats).unwrap());
}

#[derive(Default)]
struct SequenceStats {
    total_sequences: usize,
    by_depth: std::collections::BTreeMap<usize, usize>,
}

impl SequenceStats {
    fn new() -> Self {
        Self::default()
    }
    
    fn record_sequence(&mut self, depth: usize) {
        self.total_sequences += 1;
        *self.by_depth.entry(depth).or_insert(0) += 1;
    }
}

/// Pure DFS: count all legal sequences without evaluation or pruning
fn enumerate_sequences(
    state: &GameState,
    db: &CardDatabase,
    root_player: usize,
    depth: usize,
    stats: &mut SequenceStats,
) {
    if depth == 0 {
        println!("DEBUG: Entering with depth=0");
    }
    
    // Base case: hard depth limit
    if depth > 15 {
        stats.record_sequence(depth);
        return;
    }
    
    // Check if current player HAS legal Main actions (excluding Pass means no real moves)
    let mut actions = SmallVec::<[i32; 64]>::new();
    state.generate_legal_actions(db, state.current_player as usize, &mut actions);
    
    if depth == 0 {
        println!("DEBUG: Total actions = {}", actions.len());
    }
    
    // Filter out Pass - if only Pass is legal, turn ends
    let main_actions: Vec<i32> = actions.into_iter()
        .filter(|&a| a != ACTION_BASE_PASS)
        .collect();
    
    if depth == 0 {
        println!("DEBUG: Non-Pass actions = {}", main_actions.len());
    }
    
    // If no real Main phase actions, sequence ends here
    if main_actions.is_empty() || state.phase != Phase::Main {
        if depth == 0 {
            println!("DEBUG: Hitting base case - main_actions.is_empty()={}, phase check would be needed", main_actions.is_empty());
        }
        stats.record_sequence(depth);
        return;
    }
    
    if depth == 0 {
        println!("DEBUG: Will recurse into {} actions", main_actions.len());
    }
    
    // Recursive case: try all non-Pass legal actions
    for action in main_actions {
        let mut next_state = state.clone();
        if next_state.step(db, action).is_ok() {
            // Continue exploring
            enumerate_sequences(&next_state, db, root_player, depth + 1, stats);
        }
    }
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
