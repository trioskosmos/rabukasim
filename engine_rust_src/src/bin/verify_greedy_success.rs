use engine_rust::core::logic::{GameState, ACTION_SPACE, Phase};
use engine_rust::core::analysis::performance_solver::PerformanceProbabilitySolver;
use engine_rust::test_helpers::load_real_db;

fn main() {
    println!("=== Greedy CPU Agent Verification (Debug) ===");
    let db = load_real_db();
    
    // Load Real Deck
    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() {
        "ai/decks/muse_cup.txt"
    } else {
        "../ai/decks/muse_cup.txt"
    };
    
    let master_deck = {
        let content = std::fs::read_to_string(deck_path).expect("Failed to read deck file");
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
    };

    let p_main = master_deck; 
    let p_energy: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();
    
    let mut sim = GameState::default();
    sim.initialize_game(
        p_main.clone(), p_main.clone(), 
        p_energy.clone(), p_energy.clone(), 
        Vec::new(), Vec::new()
    );

    sim.ui.silent = false; // Enable logs
    sim.phase = Phase::Main;

    let mut steps = 0;
    let mut mask = vec![false; ACTION_SPACE];

    while !sim.is_terminal() && steps < 200 { // Fewer steps for debug
        mask.fill(false);
        sim.get_legal_actions_into(&db, sim.current_player as usize, &mut mask);
        
        let mut valid_actions = Vec::new();
        for (i, &b) in mask.iter().enumerate() {
            if b { valid_actions.push(i as i32); }
        }
        
        if valid_actions.is_empty() { break; }
        
        let mut best_action = valid_actions[0];
        let mut best_score = -1000000.0;

        let current_player = sim.current_player as usize;

        for &action in &valid_actions {
            let mut next_sim = sim.clone();
            let _ = next_sim.step(&db, action);
            
            let mut eval = next_sim.players[current_player].score as f32 * 10000.0;
            let chances = PerformanceProbabilitySolver::analyze_current_permissible_lives(&next_sim, &db, current_player);
            let max_prob = chances.iter().map(|c| c.1.success_probability).fold(0.0, f32::max);
            eval += max_prob * 1000.0;
            
            if next_sim.phase == sim.phase && next_sim.players[current_player].score == sim.players[current_player].score && action == 0 {
                eval -= 5000.0; 
            }

            eval += next_sim.players[current_player].hand.len() as f32 * 1.0;
            eval += next_sim.players[current_player].energy_zone.len() as f32 * 5.0;
            eval += next_sim.players[current_player].success_lives.len() as f32 * 2000.0; // Higher weight for lives

            if eval > best_score {
                best_score = eval;
                best_action = action;
            }
        }

        let _ = sim.step(&db, best_action);
        
        println!("Step {}: Action={}, Phase={:?}", steps, best_action, sim.phase);
        
        steps += 1;
    }
    
    println!("\n=== Final Result ===");
    println!("Winner: {}", sim.get_winner());
    println!("P0 Score: {}", sim.players[0].score);
    println!("Steps: {}", steps);
}
