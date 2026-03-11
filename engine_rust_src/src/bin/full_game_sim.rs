use engine_rust::core::logic::{GameState, Phase, ACTION_BASE_PASS};
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::test_helpers::load_real_db;
use std::time::Instant;
use std::fs;
use rand::seq::SliceRandom;

fn load_deck_and_lives(path: &str, db: &engine_rust::core::logic::CardDatabase) -> (Vec<i32>, Vec<i32>) {
    let content = fs::read_to_string(path).expect("Could not read deck file");
    let mut members = Vec::new();
    let mut lives = Vec::new();
    
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') { continue; }
        
        let parts: Vec<&str> = line.split(' ').collect();
        let card_no = parts[0];
        let count = if parts.len() >= 3 && parts[1] == "x" {
            parts[2].parse::<usize>().unwrap_or(1)
        } else {
            1
        };
        
        if let Some(id) = db.id_by_no(card_no) {
            if db.get_live(id).is_some() {
                for _ in 0..count {
                    lives.push(id);
                }
            } else {
                for _ in 0..count {
                    members.push(id);
                }
            }
        }
    }
    (members, lives)
}

fn main() {
    println!("Loading Database...");
    let db = load_real_db();
    
    let mut deck_path = "../ai/decks/liella_cup.txt".to_string();
    if !std::path::Path::new(&deck_path).exists() {
        deck_path = "ai/decks/liella_cup.txt".to_string();
    }
    
    let (p_members, p_lives) = load_deck_and_lives(&deck_path, &db);
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();
    
    println!("Loaded {} members, {} lives, and {} energy cards.", p_members.len(), p_lives.len(), energy_ids.len());

    let mut rng = rand::rng();
    let mut p0_deck = p_members.clone();
    let mut p1_deck = p_members.clone();
    p0_deck.shuffle(&mut rng);
    p1_deck.shuffle(&mut rng);

    let mut state = GameState::default();
    state.initialize_game(
        p0_deck,
        p1_deck,
        energy_ids.clone(),
        energy_ids.clone(),
        p_lives.clone(),
        p_lives.clone(),
    );
    
    // IMPORTANT: start silent to avoid flooding, but we'll print key events
    state.ui.silent = true;

    println!("\nSequencer Configuration Loaded: {:?}", engine_rust::core::logic::turn_sequencer::CONFIG.clone());
    println!("\nStarting Realistic AI vs AI Game Simulation...");

    let mut step_count = 0;
    let mut total_seqs = 0;
    let mut total_micros: u128 = 0;
    let start_all = Instant::now();

    while !state.is_terminal() && step_count < 1000 {
        // 1. Process deterministic transitions (Energy, Draw, Active, Performance Result)
        state.auto_step(&db);
        
        if state.is_terminal() { break; }

        let p_idx = state.current_player as usize;
        let phase = state.phase;

        // 2. Decide actions for the current phase
        match phase {
            Phase::Rps => {
                // Just pick a fixed choice to move on (0 = Rock)
                let _ = state.step(&db, 4000); 
            }
            Phase::MulliganP1 | Phase::MulliganP2 => {
                // Pass mulligan (id=1)
                let _ = state.step(&db, 1);
            }
            Phase::Main => {
                let hand_len = state.core.players[p_idx].hand.iter().filter(|&&c| c != -1).count();
                let untapped_energy = state.core.players[p_idx].energy_zone.len() - state.core.players[p_idx].tapped_energy_count() as usize;
                
                println!("[Turn {}] Player {} - Main Phase (Hand: {}, Energy: {})", 
                         state.turn, p_idx, hand_len, untapped_energy);

                let (evals, best_seq, count, _) = TurnSequencer::plan_full_turn(&state, &db);
                total_seqs += count;
                
                if best_seq.is_empty() {
                    let _ = state.step(&db, 1); // Pass
                } else {
                    for &action in &best_seq {
                        let label = state.get_verbose_action_label(action, &db);
                        println!("  Action: {}", label);
                        let _ = state.step(&db, action);
                    }
                }
            }
            Phase::LiveSet => {
                let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
                if seq.is_empty() {
                    let _ = state.step(&db, 1); // Pass
                } else {
                    for &action in &seq {
                        let label = state.get_verbose_action_label(action, &db);
                        println!("  Action: {}", label);
                        let _ = state.step(&db, action);
                    }
                }
            }
            _ => {
                // For other decision phases like ColorSelect or Interaction, just pass or pick index 0
                let legal = state.get_legal_action_ids(&db);
                if !legal.is_empty() {
                    let _ = state.step(&db, legal[0]);
                } else {
                    let _ = state.step(&db, 1); // Fallback pass
                }
            }
        }

        step_count += 1;
    }

    let elapsed_all = start_all.elapsed();
    println!("\n--- Simulation Results ---");
    println!("Final Turn Count: {}", state.turn);
    println!("Winning Player: {}", state.get_winner());
    println!("Final Score: Player 0: {} - Player 1: {}", state.core.players[0].score, state.core.players[1].score);
    println!("Total Sequences Analyzed: {}", total_seqs);
    println!("Overall Simulation Time: {:?}", elapsed_all);
    if total_micros > 0 {
        println!("Average Performance: {} seq/s", (total_seqs as f64 / (total_micros as f64 / 1_000_000.0)) as u64);
    }
}
