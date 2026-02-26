use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::test_helpers::load_real_db;
use std::time::Instant;

fn parse_deck(path: &str, db: &CardDatabase) -> Vec<i32> {
    let content = std::fs::read_to_string(path).unwrap_or_else(|_| String::new());
    if content.is_empty() { return vec![]; }
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
    let db = load_real_db();
    let deck_path = if std::path::Path::new("ai/decks/muse_cup.txt").exists() { "ai/decks/muse_cup.txt" } else { "../ai/decks/muse_cup.txt" };
    let p0_deck = parse_deck(deck_path, &db);
    
    // Fallback if deck not found
    let p0_main = if p0_deck.is_empty() {
        let all_members: Vec<i32> = db.members.keys().take(50).cloned().collect();
        all_members
    } else {
        p0_deck
    };

    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    let mut initial_state = GameState::default();
    initial_state.initialize_game(p0_main.clone(), p0_main.clone(), energy_ids.clone(), energy_ids.clone(), Vec::new(), Vec::new());
    initial_state.ui.silent = true;
    initial_state.phase = engine_rust::core::logic::Phase::Main;

    let iterations = 1000;
    println!("Running {} full CPU rollouts...", iterations);

    let mut total_steps = 0;
    let start = Instant::now();

    for i in 0..iterations {
        let mut sim = initial_state.clone();
        let mut steps = 0;
        
        // Fast seeded RNG for benchmark
        let mut rng_state = 12345;
        
        while !sim.is_terminal() && steps < 1000 {
            let actions_mask = sim.get_legal_actions(&db);
            let valid_actions: Vec<i32> = actions_mask.iter().enumerate().filter(|(_, &b)| b).map(|(i, _)| i as i32).collect();
            
            if valid_actions.is_empty() {
                if i == 0 {
                    println!("No valid actions! Phase: {:?}, Turn: {}", sim.phase, sim.turn);
                }
                break;
            }
            
            // Pick a random action
            rng_state ^= rng_state << 13;
            rng_state ^= rng_state >> 17;
            rng_state ^= rng_state << 5;
            let act_idx = (rng_state as usize) % valid_actions.len();
            
            let act = valid_actions[act_idx];
            let _ = sim.step(&db, act);
            steps += 1;
        }
        total_steps += steps;
    }

    let duration = start.elapsed().as_secs_f64();
    println!("Completed in {:.3} seconds", duration);
    println!("Rollouts/sec: {:.1}", iterations as f64 / duration);
    println!("Steps/sec (Transitions): {:.1}", total_steps as f64 / duration);
}
