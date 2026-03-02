use engine_rust::core::heuristics::OriginalHeuristic;
use engine_rust::core::logic::{GameState, Phase};
use engine_rust::core::mcts::{SearchHorizon, MCTS};
use engine_rust::test_helpers::load_real_db;
use rand::Rng;

#[derive(Clone, Copy)]
enum Agent {
    Random,
    Greedy,    // AlphaZero 1-move lookahead
    Mcts(f32), // AlphaZero Full MCTS, Timeout in seconds
}

impl Agent {
    fn name(&self) -> String {
        match self {
            Agent::Random => "Random".to_string(),
            Agent::Greedy => "AlphaZero Greedy (1-Move)".to_string(),
            Agent::Mcts(t) => format!("AlphaZero MCTS ({}s)", t),
        }
    }
}

fn get_action(
    agent: Agent,
    state: &GameState,
    db: &engine_rust::core::logic::CardDatabase,
    mcts: &mut MCTS,
    heuristic: &OriginalHeuristic,
    rng: &mut rand::rngs::ThreadRng,
) -> i32 {
    let p_idx = state.current_player as usize;
    let mut mask = vec![false; engine_rust::core::logic::ACTION_SPACE];
    state.get_legal_actions_into(db, p_idx, &mut mask);

    let valid_actions: Vec<i32> = mask
        .iter()
        .enumerate()
        .filter_map(|(i, &b)| if b { Some(i as i32) } else { None })
        .collect();
    if valid_actions.is_empty() {
        return 0;
    }
    if valid_actions.len() == 1 {
        return valid_actions[0];
    }

    match agent {
        Agent::Random => {
            let idx = rng.random_range(0..valid_actions.len());
            valid_actions[idx]
        }
        Agent::Greedy => {
            // AlphaZero Heuristic evaluated perfectly at Depth 1
            let mut best_action = valid_actions[0];

            // To maximize our win chance, we want the highest heuristic score from *our* perspective.
            // But state.step might change turns. Heuristic is typically absolute P0 win rate,
            // so we must invert it if it's P1's turn.
            let mut best_score = f32::NEG_INFINITY;

            for &action in &valid_actions {
                let mut next_sim = state.clone();
                let _ = next_sim.step(db, action);

                let mut eval = if next_sim.is_terminal() {
                    match next_sim.get_winner() {
                        w if w == p_idx as i32 => 1.0,
                        w if w == 1 - p_idx as i32 => 0.0,
                        _ => 0.5,
                    }
                } else {
                    use engine_rust::core::heuristics::Heuristic;
                    let h_val = heuristic.evaluate(
                        &next_sim,
                        db,
                        state.players[0].score,
                        state.players[1].score,
                        engine_rust::core::heuristics::EvalMode::Normal,
                        None,
                        None,
                    );
                    if p_idx == 1 {
                        1.0 - h_val
                    } else {
                        h_val
                    } // Convert P0 win rate to Current Player win rate
                };

                // Tiebreaker: avoid passing instantly unless it's strictly better
                if action == 0 {
                    eval -= 0.0001;
                }

                if eval > best_score {
                    best_score = eval;
                    best_action = action;
                }
            }
            best_action
        }
        Agent::Mcts(timeout) => {
            let (stats, _) =
                mcts.search(state, db, 0, timeout, SearchHorizon::GameEnd(), heuristic);
            if stats.is_empty() {
                valid_actions[0]
            } else {
                stats[0].0
            }
        }
    }
}

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

fn run_matchup(agent0: Agent, agent1: Agent, num_games: usize) {
    println!("\n=======================================================");
    println!("Face-off: {} (P0) vs {} (P1)", agent0.name(), agent1.name());
    println!("=======================================================");

    let db = load_real_db();

    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() {
        "ai/decks/muse_cup.txt"
    } else {
        "../ai/decks/muse_cup.txt"
    };

    let mut p_main = parse_deck(deck_path, &db);

    if p_main.is_empty() {
        println!("Warning: Could not parse deck, using fallback.");
        p_main = db.members.keys().take(48).cloned().collect();
        let mut fallback_lives: Vec<i32> = db.lives.keys().take(12).cloned().collect();
        p_main.append(&mut fallback_lives);
    }

    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    let mut wins_0 = 0;
    let mut wins_1 = 0;
    let mut draws = 0;

    for _ in 0..num_games {
        let mut sim = GameState::default();
        sim.initialize_game(
            p_main.clone(),
            p_main.clone(),
            energy_ids.clone(),
            energy_ids.clone(),
            Vec::new(),
            Vec::new(),
        );
        sim.ui.silent = true;
        sim.phase = Phase::Main;

        let mut mcts = MCTS::new();
        let heuristic = OriginalHeuristic::default();
        let mut steps = 0;
        let mut rng = rand::rng();

        while !sim.is_terminal() && steps < 500 {
            let action = if sim.current_player == 0 {
                get_action(agent0, &sim, &db, &mut mcts, &heuristic, &mut rng)
            } else {
                get_action(agent1, &sim, &db, &mut mcts, &heuristic, &mut rng)
            };

            let _ = sim.step(&db, action);

            if steps % 50 == 0 {
                print!(".");
                use std::io::Write;
                std::io::stdout().flush().unwrap();
            }
            steps += 1;
        }

        let winner = sim.get_winner();
        match winner {
            0 => {
                wins_0 += 1;
            }
            1 => {
                wins_1 += 1;
            }
            _ => {
                draws += 1;
            }
        }
    }

    println!(
        "\n--- Results for {} vs {} ---",
        agent0.name(),
        agent1.name()
    );
    println!("Total Games: {}", num_games);
    println!("{} (P0) Wins: {}", agent0.name(), wins_0);
    println!("{} (P1) Wins: {}", agent1.name(), wins_1);
    println!("Draws: {}", draws);
}

fn main() {
    let num_games = 10;

    // As requested:
    // 1. Random vs AlphaZero (0.1s)
    run_matchup(Agent::Random, Agent::Mcts(0.1), num_games);

    // 2. Greedy vs AlphaZero (0.01s)
    run_matchup(Agent::Greedy, Agent::Mcts(0.01), num_games);

    // 3. AlphaZero (0.01s) vs AlphaZero (0.01s)
    run_matchup(Agent::Mcts(0.01), Agent::Mcts(0.01), num_games);
}
