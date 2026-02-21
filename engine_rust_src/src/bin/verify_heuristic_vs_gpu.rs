use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::core::heuristics::{OriginalHeuristic, Heuristic, EvalMode};
use engine_rust::test_helpers::load_real_db;

fn parse_deck(path: &str, db: &CardDatabase) -> Vec<i32> {
    let content = std::fs::read_to_string(path).expect("Failed to read deck file");
    let mut ids = Vec::new();
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') { continue; }
        let parts: Vec<&str> = line.split('x').map(|s| s.trim()).collect();
        let no = parts[0];
        let count = if parts.len() > 1 { parts[1].parse::<usize>().unwrap_or(1) } else { 1 };
        if let Some(&id) = db.card_no_to_id.get(no) {
            for _ in 0..count { ids.push(id); }
        }
    }
    ids
}

fn main() {
    println!("=== Heuristic vs GPU Verifier ===");
    let db = load_real_db();
    let heuristic = OriginalHeuristic::default();

    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() { "ai/decks/muse_cup.txt" } else { "../ai/decks/muse_cup.txt" };
    let p0_deck = parse_deck(deck_path, &db);
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    let mut state = GameState::default();
    state.initialize_game(p0_deck.clone(), p0_deck.clone(), energy_ids.clone(), energy_ids.clone(), Vec::new(), Vec::new());
    
    let eval = heuristic.evaluate(&state, &db, 0, 0, EvalMode::Normal, None, None);
    println!("Initial State Prediction (P0 Win Prob): {:.2}%", eval * 100.0);
    
    println!("\nExpected from GPU Simulation: 72.33%");
}
