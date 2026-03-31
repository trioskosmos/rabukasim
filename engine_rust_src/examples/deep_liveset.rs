use std::time::Instant;
use engine_rust::core::logic::game::GameState;
use engine_rust::core::logic::card_db::CardDatabase;
use engine_rust::core::enums::Phase;

fn load_db() -> CardDatabase {
    let db_path = "../data/cards_compiled.json";
    let json_content = std::fs::read_to_string(db_path).expect("Failed to read database file");
    CardDatabase::from_json(&json_content).expect("Failed to parse database")
}

fn setup_complex_liveset_state(state: &mut GameState, _db: &CardDatabase) {
    // Create a more complex scenario that might trigger expensive operations
    let deck: Vec<i32> = (1000..1100).collect();
    let lives: Vec<i32> = (4000..4100).collect();
    let energy: Vec<i32> = (5000..5100).collect();
    
    state.initialize_game(deck.clone(), deck, energy.clone(), energy, lives.clone(), lives);
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    state.ui.headless = true;
    state.ui.silent = true;
    
    // Add some triggers and complex state that might cause expensive operations
    for p in 0..2 {
        // Fill stage with cards that have abilities
        for slot in 0..3 {
            let cid = (1000 + p * 100 + slot) as i32;
            state.core.players[p].stage[slot] = cid;
            
            // Add some granted abilities to make trigger processing expensive
            if slot == 0 {
                state.core.players[p].granted_abilities.push((cid, 2000, 0));
                state.core.players[p].granted_abilities.push((cid, 2001, 1));
            }
        }
        
        // Add cards to live zone
        for slot in 0..2 {
            let cid = (4000 + p * 100 + slot) as i32;
            state.core.players[p].live_zone[slot] = cid;
            state.core.players[p].set_revealed(slot, false);
        }
        
        // Add some heart buffs and blade buffs to make calculations expensive
        for i in 0..10 {
            state.core.players[p].heart_buff_logs.push((2000 + i, 1, i as u8, 0));
            state.core.players[p].blade_buff_logs.push((2000 + i, 1, 0));
        }
        
        // Add some color transforms
        state.core.players[p].color_transforms.push((2000, 0, 1));
        state.core.players[p].color_transforms.push((2001, 0, 2));
    }
}

type SetupFn = fn(&mut GameState, &CardDatabase);

fn analyze_slow_liveset_scenarios() {
    println!("=== Deep LiveSet Performance Analysis ===\n");
    
    let db = load_db();
    
    // Test different scenarios that might cause slow LiveSet steps
    let scenarios: Vec<(&str, SetupFn)> = vec![
        ("Basic LiveSet", setup_basic_state),
        ("Complex State with Triggers", setup_complex_state),
        ("Full Board with Abilities", setup_full_board),
    ];
    
    for (name, setup_fn) in scenarios {
        println!("\n--- Testing: {} ---", name);
        
        let mut times = Vec::new();
        for i in 0..20 {
            let mut state = GameState::default();
            setup_fn(&mut state, &db);
            
            let start = Instant::now();
            let _ = state.step(&db, 0); // LiveSet pass action
            let elapsed = start.elapsed().as_nanos() as u64;
            times.push(elapsed);
            
            if i < 3 {
                println!("Run {}: {}μs -> {:?}", i, elapsed / 1000, state.phase);
            }
        }
        
        times.sort();
        let min = times[0];
        let max = times[times.len() - 1];
        let avg = times.iter().sum::<u64>() / times.len() as u64;
        
        println!("Results: min={}μs, max={}μs, avg={}μs", 
            min / 1000, max / 1000, avg / 1000);
    }
}

fn setup_basic_state(state: &mut GameState, _db: &CardDatabase) {
    let deck = vec![1001, 1002, 1003];
    let lives = vec![4001, 4002];
    let energy = vec![5001, 5002];
    
    state.initialize_game(deck.clone(), deck, energy.clone(), energy, lives.clone(), lives);
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    state.ui.headless = true;
    state.ui.silent = true;
}

fn setup_complex_state(state: &mut GameState, db: &CardDatabase) {
    setup_complex_liveset_state(state, db);
}

fn setup_full_board(state: &mut GameState, db: &CardDatabase) {
    setup_complex_liveset_state(state, db);
    
    // Make it even more complex - fill all zones
    for p in 0..2 {
        // Add more cards to hand
        for i in 0..10 {
            state.core.players[p].hand.push((6000 + p * 100 + i) as i32);
        }
        
        // Add more cards to deck
        for i in 0..20 {
            state.core.players[p].deck.push((7000 + p * 100 + i) as i32);
        }
        
        // Add yell cards
        for i in 0..5 {
            state.core.players[p].yell_cards.push((8000 + p * 100 + i) as i32);
        }
        
        // Set more flags
        state.core.players[p].set_flag(1, true); // Some random flag
        state.live_start_processed_mask[p] = 0xFF; // All live start processed
        state.performance_reveals_done[p] = true;
    }
}

fn main() {
    analyze_slow_liveset_scenarios();
}
