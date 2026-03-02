use engine_rust::core::logic::{GameState, Phase};
use engine_rust::core::mcts::{MCTS, SearchHorizon};
use engine_rust::core::heuristics::OriginalHeuristic;
use engine_rust::test_helpers::load_real_db;
use rand::Rng;

fn main() {
    println!("=== Face-off: Random (P0) vs MCTS AlphaZero Heuristic (P1) ===");
    let db = load_real_db();
    
    // Decks
    let p_main: Vec<i32> = db.members.keys().take(50).cloned().collect();
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();
    
    let mut wins_random = 0;
    let mut wins_mcts = 0;
    let mut draws = 0;

    let num_games = 10;
    let timeout_sec = 0.1;

    for game_idx in 0..num_games {
        println!("\n--- Game {} ---", game_idx + 1);
        let mut sim = GameState::default();
        sim.initialize_game(
            p_main.clone(), p_main.clone(), 
            energy_ids.clone(), energy_ids.clone(), 
            Vec::new(), Vec::new()
        );
        sim.ui.silent = true;
        sim.phase = Phase::Main;

        let mut mcts = MCTS::new();
        let heuristic = OriginalHeuristic::default();
        
        let mut steps = 0;
        let mut rng = rand::rng();

        while !sim.is_terminal() && steps < 500 {
            let current_player = sim.current_player;

            let action = if current_player == 0 {
                // Player 0: Random
                let mut mask = vec![false; engine_rust::core::logic::ACTION_SPACE];
                sim.get_legal_actions_into(&db, 0, &mut mask);
                let valid_actions: Vec<i32> = mask.iter().enumerate().filter_map(|(i, &b)| if b { Some(i as i32) } else { None }).collect();
                if valid_actions.is_empty() {
                    println!("No legal actions for Random! Phase: {:?}", sim.phase);
                    break;
                }
                let idx = rng.random_range(0..valid_actions.len());
                valid_actions[idx]
            } else {
                // Player 1: MCTS (0.1s)
                let (stats, _) = mcts.search(&sim, &db, 0, timeout_sec, SearchHorizon::GameEnd(), &heuristic);
                if stats.is_empty() {
                    println!("No legal actions for MCTS! Phase: {:?}", sim.phase);
                    break;
                }
                stats[0].0
            };

            let _ = sim.step(&db, action);
            
            if steps % 20 == 0 {
                print!(".");
                use std::io::Write;
                std::io::stdout().flush().unwrap();
            }
            
            steps += 1;
        }
        
        println!("\nGame {} finished in {} steps.", game_idx + 1, steps);
        let winner = sim.get_winner();
        match winner {
            0 => {
                println!("Winner: Random (P0) - Score: {} vs {}", sim.players[0].score, sim.players[1].score);
                wins_random += 1;
            },
            1 => {
                println!("Winner: MCTS (P1) - Score: {} vs {}", sim.players[1].score, sim.players[0].score);
                wins_mcts += 1;
            },
            _ => {
                println!("Draw - Score: {} vs {}", sim.players[0].score, sim.players[1].score);
                draws += 1;
            }
        }
    }
    
    println!("\n=== Final Results ===");
    println!("Total Games: {}", num_games);
    println!("Random (P0) Wins: {}", wins_random);
    println!("MCTS (P1) Wins: {}", wins_mcts);
    println!("Draws: {}", draws);
}
