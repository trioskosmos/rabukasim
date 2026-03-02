use engine_rust::core::logic::{GameState, Phase};
use engine_rust::core::mcts::{MCTS, SearchHorizon};
use engine_rust::core::heuristics::OriginalHeuristic;
use engine_rust::test_helpers::load_real_db;

fn main() {
    println!("=== MCTS AI Verification ===");
    let db = load_real_db();
    
    // Decks
    let p_main: Vec<i32> = db.members.keys().take(50).cloned().collect();
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();
    
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
    while !sim.is_terminal() && steps < 500 {
        let (stats, _) = mcts.search(&sim, &db, 200, 0.0, SearchHorizon::GameEnd(), &heuristic);
        
        if stats.is_empty() {
             println!("No legal actions! Phase: {:?}", sim.phase);
             break;
        }
        
        // Take best action
        let action = stats[0].0;
        let _ = sim.step(&db, action);
        
        if steps % 10 == 0 {
            println!("Step {}: Phase={:?}, P0 Score={}, P1 Score={}", steps, sim.phase, sim.players[0].score, sim.players[1].score);
        }
        
        steps += 1;
    }
    
    println!("\n=== Final Result ===");
    println!("Winner: {}", sim.get_winner());
    println!("P0 Score: {}", sim.players[0].score);
    println!("P1 Score: {}", sim.players[1].score);
    println!("Steps: {}", steps);
}
