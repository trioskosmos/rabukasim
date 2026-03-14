use engine_rust::core::heuristics::OriginalHeuristic;
use engine_rust::core::logic::{GameState, Phase};
use engine_rust::core::mcts::{SearchHorizon, MCTS};
use engine_rust::test_helpers::load_real_db;
use rand::prelude::*;
use rand::rngs::SmallRng;
use rand::SeedableRng;
use std::time::Instant;

fn parse_deck(path: &str, db: &engine_rust::core::logic::CardDatabase) -> Vec<i32> {
    let mut main_deck = Vec::new();
    if let Ok(content) = std::fs::read_to_string(path) {
        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            let parts: Vec<&str> = line.split('x').map(|s| s.trim()).collect();
            let no = parts[0];
            let count = if parts.len() > 1 {
                parts[1].parse::<usize>().unwrap_or(1)
            } else {
                1
            };
            if let Some(&id) = db.card_no_to_id.get(no) {
                for _ in 0..count {
                    main_deck.push(id);
                }
            }
        }
    }
    main_deck
}

fn analyze_state(
    label: &str,
    state: &GameState,
    db: &engine_rust::core::logic::CardDatabase,
    time_limits: &[f32],
) {
    println!("\n=== {} ===", label);
    println!(
        "Phase: {:?}, Turn: {}, Legal Actions: {}",
        state.phase,
        state.turn,
        {
            let mut mask = vec![false; engine_rust::core::logic::ACTION_SPACE];
            state.get_legal_actions_into(db, state.current_player as usize, &mut mask);
            mask.iter().filter(|&&b| b).count()
        }
    );

    for &timeout in time_limits {
        println!("\nTesting MCTS with timeout: {:.3}s", timeout);
        let mut mcts = MCTS::new();
        let heuristic = OriginalHeuristic::default();

        let start = Instant::now();
        // search_custom is used directly because search() isn't returning tree stats, but search() updates self.nodes.
        // Wait, MCTS is consumed and we only get back (stats, profiler) from search.
        // But `search()` takes `&mut self`, so the `mcts` object itself retains the nodes!
        let (stats, profiler) =
            mcts.search(state, db, 0, timeout, SearchHorizon::TurnEnd(), &heuristic);
        let elapsed = start.elapsed().as_secs_f64();

        let tree_size = mcts.get_tree_size();
        let max_depth = mcts.get_max_depth();
        let total_visits: u32 = stats.iter().map(|(_, _, v)| v).sum();

        println!("  - Real Elapsed Time: {:.3}s", elapsed);
        println!("  - Total Simulations: {}", total_visits);
        println!(
            "  - Sims per Second:   {:.0}",
            (total_visits as f64) / elapsed
        );
        println!("  - Tree Size (Nodes): {}", tree_size);
        println!("  - Max Search Depth:  {}", max_depth);
        profiler.print(std::time::Duration::from_secs_f64(elapsed));
    }
}

fn main() {
    println!("=== MCTS Depth/Breadth Analysis ===");
    let db = load_real_db();

    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() {
        "ai/decks/muse_cup.txt"
    } else {
        "../ai/decks/muse_cup.txt"
    };

    let mut p_main = parse_deck(deck_path, &db);
    if p_main.is_empty() {
        p_main = db.members.keys().take(48).cloned().collect();
        let mut fallback_lives: Vec<i32> = db.lives.keys().take(12).cloned().collect();
        p_main.append(&mut fallback_lives);
    }
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    let mut state = GameState::default();
    state.initialize_game(
        p_main.clone(),
        p_main.clone(),
        energy_ids.clone(),
        energy_ids.clone(),
        Vec::new(),
        Vec::new(),
    );
    state.ui.silent = true;
    state.phase = Phase::Main;

    let time_limits = vec![0.01, 0.05, 0.1, 0.5];

    // State 1: Very start of game (Main Phase)
    analyze_state("State 1: Main Phase (Turn 1)", &state, &db, &time_limits);

    // Play through randomly for 20 steps
    let mut rng = rand::rngs::SmallRng::from_os_rng();
    for _ in 0..20 {
        if state.is_terminal() {
            break;
        }
        let mut mask = vec![false; engine_rust::core::logic::ACTION_SPACE];
        state.get_legal_actions_into(&db, state.current_player as usize, &mut mask);
        let valid_actions: Vec<i32> = mask
            .iter()
            .enumerate()
            .filter_map(|(i, &b)| if b { Some(i as i32) } else { None })
            .collect();
        if !valid_actions.is_empty() {
            let action = valid_actions[rng.random_range(0..valid_actions.len())];
            let _ = state.step(&db, action);
        }
    }

    // State 2: Mid-game
    analyze_state(
        "State 2: Mid-game (After 20 random actions)",
        &state,
        &db,
        &time_limits,
    );
}
