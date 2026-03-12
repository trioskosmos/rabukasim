use std::fs;
use std::time::Instant;
use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::logic::turn_sequencer::TurnSequencer;
use engine_rust::core::enums::Phase;
use engine_rust::core::ACTION_BASE_PASS;

fn main() {
    println!("\n=== LOVECA AI GAME ===\n");
    
    let start_total = Instant::now();
    
    println!("[init] Loading database...");
    let db = load_vanilla_db();
    println!("[init] ✓ DB loaded");
    
    println!("[init] Building decks...");
    let (deck, lives, energy) = build_decks(&db);
    println!("[init] ✓ Decks built");
    
    println!("[init] Initializing game state...");
    let mut state = GameState::default();
    state.initialize_game(
        deck.clone(), deck.clone(),
        energy.clone(), energy.clone(),
        lives.clone(), lives.clone(),
    );
    println!("[init] ✓ Game initialized\n");
    
    let mut turn_count = 0;
    
    println!("--- GAME START ---\n");
    
    while state.phase != Phase::Terminal && turn_count < 100 {
        // Auto-step through non-interactive phases
        while state.phase != Phase::Terminal && !state.phase.is_interactive() {
            state.auto_step(&db);
        }
        
        if state.phase == Phase::Terminal {
            break;
        }
        
        turn_count += 1;
        let current_player = state.current_player as usize;
        let player_name = if current_player == 0 { "P0" } else { "P1" };
        
        println!("[Turn {}] {} (Phase: {:?}, Scores: P0={} P1={})",
                 turn_count, player_name, state.phase,
                 state.players[0].score, state.players[1].score);
        
        // Handle interactive phases
        match state.phase {
            Phase::Main => {
                let seq_start = Instant::now();
                let (seq, _, _) = TurnSequencer::find_best_main_sequence(&state, &db);
                let seq_time = seq_start.elapsed().as_secs_f32();
                
                if seq.is_empty() {
                    println!("  No moves, passing");
                } else {
                    println!("  Found sequence: {} moves ({:.3}s)", seq.len(), seq_time);
                    for &action in &seq {
                        if state.step(&db, action).is_err() {
                            break;
                        }
                    }
                }
                
                // Pass if still in Main
                if state.phase == Phase::Main {
                    let _ = state.step(&db, ACTION_BASE_PASS);
                }
            },
            Phase::LiveSet => {
                let (seq, _, _) = TurnSequencer::find_best_liveset_selection(&state, &db);
                for &action in &seq {
                    let _ = state.step(&db, action);
                }
                let _ = state.step(&db, ACTION_BASE_PASS);
            },
            Phase::LiveResult => {
                let legal = state.get_legal_action_ids(&db);
                let action = legal.first().copied().unwrap_or(ACTION_BASE_PASS);
                let _ = state.step(&db, action);
            },
            Phase::Energy => {
                let legal = state.get_legal_action_ids(&db);
                if !legal.is_empty() {
                    let _ = state.step(&db, legal[0]);
                } else {
                    state.auto_step(&db);
                }
            },
            Phase::MulliganP1 | Phase::MulliganP2 => {
                let legal = state.get_legal_action_ids(&db);
                let action = legal.first().copied().unwrap_or(ACTION_BASE_PASS);
                let _ = state.step(&db, action);
            },
            _ => {
                let legal = state.get_legal_action_ids(&db);
                if !legal.is_empty() {
                    let _ = state.step(&db, legal[0]);
                }
            }
        }
    }
    
    println!("--- GAME END ---\n");
    
    // Determine winner
    let winner = state.get_winner();
    let p0_score = state.players[0].score;
    let p1_score = state.players[1].score;
    
    println!("[result] P0 score: {}", p0_score);
    println!("[result] P1 score: {}", p1_score);
    println!("[result] Total turns: {}", turn_count);
    println!("[result] Total time: {:.2}s\n", start_total.elapsed().as_secs_f32());
    
    if winner == 0 {
        println!("🏆 WINNER: P0 (score {})", p0_score);
    } else if winner == 1 {
        println!("🏆 WINNER: P1 (score {})", p1_score);
    } else {
        println!("⚖️  DRAW (scores: P0={} P1={})", p0_score, p1_score);
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
    panic!("cards_vanilla.json not found");
}
