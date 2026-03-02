use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::core::mcts::{MCTS, SearchHorizon};
use engine_rust::core::heuristics::{OriginalHeuristic, Heuristic};
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
    println!("=== AI Game Simulation Runner ===");
    let db = load_real_db();
    let heuristic = OriginalHeuristic::default();

    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() {
        "ai/decks/muse_cup.txt"
    } else {
        "../ai/decks/muse_cup.txt"
    };

    let p0_deck = parse_deck(deck_path, &db);
    let p1_deck = p0_deck.clone();

    let mut state = GameState::default();

    // Split into main and energy (Simplified: just use members for energy for now)
    let p0_main: Vec<i32> = p0_deck.iter().filter(|&&id| db.get_member(id).is_some() || db.get_live(id).is_some()).cloned().collect();
    let p1_main: Vec<i32> = p1_deck.iter().filter(|&&id| db.get_member(id).is_some() || db.get_live(id).is_some()).cloned().collect();

    // Take energy from DB directly for stability
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    state.initialize_game(
        p0_main,
        p1_main,
        energy_ids.clone(),
        energy_ids.clone(),
        Vec::new(), Vec::new(),
    );

    state.ui.silent = false; // LOG ALL STEPS
    let mut move_count = 0;
    let cpu_mcts = MCTS::new();
    let timeout_sec = 0.5; // High quality search

    println!("Initial Setup Complete. Starting Simulation...");

    while !state.is_terminal() && move_count < 1000 {
        let current_p = state.current_player as usize;
        println!("\n--- [MOVE {}] Turn {} | Phase {:?} | Player {} ---", move_count, state.turn, state.phase, current_p);

        // Log current probability as seen by the heuristic
        let current_eval = heuristic.evaluate(&state, &db, 0, 0, engine_rust::core::heuristics::EvalMode::Normal, None, None);
        println!("[AI View] Evaluation Score: {:.4} (higher favors P0)", current_eval);

        let suggestions = cpu_mcts.search_parallel(
            &state, &db, 0, timeout_sec, SearchHorizon::GameEnd(), &heuristic, false
        );

        if let Some((action, q_val, visits)) = suggestions.first() {
            println!("[AI Decision] Action {} | Q-Value: {:.4} | Visits: {}", action, q_val, visits);
            let _ = state.step(&db, *action);
        } else {
            println!("[ERROR] No legal actions found!");
            break;
        }

        move_count += 1;
    }

    println!("\n=== SIMULATION ENDED ===");
    println!("Winner: {}", state.get_winner());
    println!("Final Scores: P0={} P1={}", state.core.players[0].score, state.core.players[1].score);
    println!("Total Moves: {}", move_count);
}
