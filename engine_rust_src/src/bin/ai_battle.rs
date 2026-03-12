use std::fs;
use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::enums::Phase;
use engine_rust::core::ACTION_BASE_PASS;
use std::time::Instant;

fn main() {
    println!("\n== LOVECA AI BATTLE ==\n");
    
    let start = Instant::now();
    
    println!("[*] Loading database...");
    let db = load_vanilla_db();
    println!("[*] Building decks...");
    let (deck, lives, energy) = build_decks(&db);
    
    println!("[*] Initializing game...");
    let mut state = GameState::default();
    state.initialize_game(
        deck.clone(), deck.clone(),
        energy.clone(), energy.clone(),
        lives.clone(), lives.clone(),
    );
    println!("[*] Initial phase: {:?}", state.phase);
    
    let mut turn = 0;
    let mut auto_steps = 0;
    let max_auto_steps = 10000;
    
    // Play game
    while state.phase != Phase::Terminal && turn < 200 {
        // Safeguard against infinite loops
        if auto_steps > max_auto_steps {
            println!("[ERROR] Too many auto-steps, terminating");
            break;
        }
        
        if state.phase.is_interactive() {
            turn += 1;
            let p = if state.current_player == 0 { "P0" } else { "P1" };
            
            println!("[T{}] {} {:?} | Score: P0={} P1={}", 
                turn, p, state.phase,
                state.players[0].score, state.players[1].score);
            
            match state.phase {
                Phase::Main => {
                    let (seq, _, _) = TurnSequencer::find_best_main_sequence(&state, &db);
                    for a in seq { let _ = state.step(&db, a); }
                    if state.phase == Phase::Main {
                        let _ = state.step(&db, ACTION_BASE_PASS);
                    }
                },
                Phase::LiveSet => {
                    let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
                    for a in seq { let _ = state.step(&db, a); }
                    let _ = state.step(&db, ACTION_BASE_PASS);
                },
                _ => {
                    let actions = state.get_legal_action_ids(&db);
                    if !actions.is_empty() {
                        let _ = state.step(&db, actions[0]);
                    } else {
                        println!("[!] No legal actions in phase {:?}", state.phase);
                        break;
                    }
                }
            }
        } else {
            auto_steps += 1;
            
            // Manually step through non-interactive phases instead of auto_step
            let actions = state.get_legal_action_ids(&db);
            if !actions.is_empty() {
                let _ = state.step(&db, actions[0]);
            } else {
                // If no legal actions, try auto_step
                state.auto_step(&db);
            }
            
            if auto_steps % 500 == 0 {
                println!("[auto] Phase: {:?} Count: {}", state.phase, auto_steps);
            }
        }
    }
    
    println!("\n=== FINAL SCORES ===");
    println!("P0: {}", state.players[0].score);
    println!("P1: {}", state.players[1].score);
    println!("Turns: {}", turn);
    println!("Auto-steps: {}", auto_steps);
    println!("Time: {:.2}s", start.elapsed().as_secs_f32());
    
    let winner = state.get_winner();
    if winner == 0 {
        println!("\n🏆 P0 WINS!");
    } else if winner == 1 {
        println!("\n🏆 P1 WINS!");
    } else {
        println!("\n⚖️  DRAW");
    }
}

fn build_decks(db: &CardDatabase) -> (Vec<i32>, Vec<i32>, Vec<i32>) {
    let mut deck: Vec<i32> = db.members.keys().copied().take(48).collect();
    while deck.len() < 48 {
        if let Some(&id) = db.members.keys().next() {
            deck.push(id);
        } else { break; }
    }
    
    let mut lives: Vec<i32> = db.lives.keys().copied().take(12).collect();
    while lives.len() < 12 {
        if let Some(&id) = db.lives.keys().next() {
            lives.push(id);
        } else { break; }
    }
    
    let energy: Vec<i32> = db.energy_db.keys().copied().take(12).collect();
    (deck, lives, energy)
}

fn load_vanilla_db() -> CardDatabase {
    for path in &["data/cards_vanilla.json", "../data/cards_vanilla.json", "../../data/cards_vanilla.json"] {
        if std::path::Path::new(path).exists() {
            let json = fs::read_to_string(path).expect("read");
            let mut db = CardDatabase::from_json(&json).expect("parse");
            db.is_vanilla = true;
            return db;
        }
    }
    panic!("DB not found");
}
