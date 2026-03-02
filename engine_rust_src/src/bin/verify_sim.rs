use engine_rust::core::logic::{GameState, Phase, ACTION_SPACE};
use engine_rust::test_helpers::load_real_db;
use std::fs::File;
use std::io::Write;

fn main() {
    println!("=== Simulation Logic Verification ===");
    let db = load_real_db();

    let _muse_deck_path = "ai/decks/muse_cup.txt";
    // Fallback deck initialization if path doesn't exist
    let p_main: Vec<i32> = db.members.keys().take(50).cloned().collect();
    let energy_ids: Vec<i32> = db.energy_db.keys().take(10).cloned().collect();

    let mut file = File::create("reports/sim_verification.log").expect("Could not create log file");
    writeln!(file, "=== Simulation Verification Log ===").unwrap();
    writeln!(file, "Timestamp: {:?}", std::time::SystemTime::now()).unwrap();

    let mut rng_state = 42u64;

    for game_idx in 0..5 {
        writeln!(file, "\n--- Game {} ---", game_idx).unwrap();
        let mut sim = GameState::default();
        sim.initialize_game(
            p_main.clone(),
            p_main.clone(),
            energy_ids.clone(),
            energy_ids.clone(),
            Vec::new(),
            Vec::new(),
        );
        sim.ui.silent = false;
        sim.debug.debug_mode = true; // Still want some logs
        sim.phase = Phase::Main;

        let mut steps = 0;
        let mut mask = vec![false; ACTION_SPACE];

        while !sim.is_terminal() && steps < 500 {
            mask.fill(false);
            sim.get_legal_actions_into(&db, sim.current_player as usize, &mut mask);

            let mut valid_actions = smallvec::SmallVec::<[i32; 64]>::new();
            for (i, &b) in mask.iter().enumerate() {
                if b {
                    valid_actions.push(i as i32);
                }
            }

            if valid_actions.is_empty() {
                writeln!(file, "Error: No legal actions at step {}", steps).unwrap();
                break;
            }

            // Random choice
            rng_state ^= rng_state << 13;
            rng_state ^= rng_state >> 17;
            rng_state ^= rng_state << 5;
            let action = valid_actions[(rng_state as usize) % valid_actions.len()];

            let _ = sim.step(&db, action);

            // Flush rule logs
            if let Some(logs) = sim.ui.rule_log.take() {
                for log in logs {
                    writeln!(file, "{}", log).unwrap();
                }
            }

            steps += 1;
        }
        let _ = writeln!(
            file,
            "Game {} finished in {} steps. Winner: {}",
            game_idx,
            steps,
            sim.get_winner()
        );
        println!("Game {} verified ({} steps)", game_idx, steps);
    }

    println!("Verification finished. Log saved to reports/sim_verification.log.");
}
