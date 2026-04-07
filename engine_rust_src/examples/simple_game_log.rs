use engine_rust::core::enums::Phase;
use engine_rust::core::logic::card_db::CardDatabase;
use engine_rust::core::logic::game::GameState;

fn load_db() -> CardDatabase {
    let db_path = "../data/cards_compiled.json";
    let json_content = std::fs::read_to_string(db_path).expect("Failed to read database file");
    CardDatabase::from_json(&json_content).expect("Failed to parse database")
}

fn setup_game(state: &mut GameState, _db: &CardDatabase) {
    // Simple deck setup
    let deck: Vec<i32> = (1000..1100).collect();
    let lives: Vec<i32> = (4000..4100).collect();
    let energy: Vec<i32> = (5000..5100).collect();

    state.initialize_game(
        deck.clone(),
        deck,
        energy.clone(),
        energy,
        lives.clone(),
        lives,
    );
    state.phase = Phase::LiveSet;
    state.current_player = 0;
    state.first_player = 0;
    state.turn = 1;
    state.ui.headless = true;
    state.ui.silent = true;
}

fn main() {
    println!("=== SIMPLE GAME LOG ===\n");

    let db = load_db();
    let mut state = GameState::default();
    setup_game(&mut state, &db);

    println!("INITIAL STATE:");
    println!("Phase: {:?}", state.phase);
    println!("Current Player: {}", state.current_player);
    println!("P0 Hand: {:?}", state.core.players[0].hand);
    println!("P1 Hand: {:?}", state.core.players[1].hand);
    println!("P0 Live: {:?}", state.core.players[0].live_zone);
    println!("P1 Live: {:?}", state.core.players[1].live_zone);

    for step in 0..10 {
        println!("\n=== STEP {} ===", step);
        println!("Phase: {:?}", state.phase);
        println!("Player: {}", state.current_player);

        // Get legal actions
        let legal_actions = state.get_legal_actions(&db);
        let legal_count = legal_actions.iter().filter(|&&x| x).count();
        println!("Legal actions: {}", legal_count);

        // Show first few legal actions
        let mut legal_list = Vec::new();
        for (i, &is_legal) in legal_actions.iter().enumerate().take(20) {
            if is_legal {
                legal_list.push(i);
            }
        }
        println!("Legal action indices: {:?}", legal_list);

        // Choose first legal action (not pass if possible)
        let chosen_action = if legal_list.len() > 1 && legal_list[0] != 0 {
            legal_list[1] as i32 // Skip pass (0) if there are other options
        } else {
            0 // Pass
        };

        println!("Chosen action: {}", chosen_action);

        // Record state before
        let p0_hand_before = state.core.players[0].hand.len();
        let p1_hand_before = state.core.players[1].hand.len();
        let p0_live_before = state.core.players[0].live_zone.clone();
        let p1_live_before = state.core.players[1].live_zone.clone();

        // Execute action
        let result = state.step(&db, chosen_action);

        // Record state after
        let p0_hand_after = state.core.players[0].hand.len();
        let p1_hand_after = state.core.players[1].hand.len();
        let p0_live_after = state.core.players[0].live_zone.clone();
        let p1_live_after = state.core.players[1].live_zone.clone();

        println!("Result: {:?}", result);
        println!("New Phase: {:?}", state.phase);
        println!("New Player: {}", state.current_player);

        // Show what changed
        if p0_hand_before != p0_hand_after {
            println!("P0 hand size: {} -> {}", p0_hand_before, p0_hand_after);
        }
        if p1_hand_before != p1_hand_after {
            println!("P1 hand size: {} -> {}", p1_hand_before, p1_hand_after);
        }
        if p0_live_before != p0_live_after {
            println!("P0 live: {:?} -> {:?}", p0_live_before, p0_live_after);
        }
        if p1_live_before != p1_live_after {
            println!("P1 live: {:?} -> {:?}", p1_live_before, p1_live_after);
        }

        // Show current hands
        println!("P0 Hand: {:?}", state.core.players[0].hand);
        println!("P1 Hand: {:?}", state.core.players[1].hand);
        println!("P0 Live: {:?}", state.core.players[0].live_zone);
        println!("P1 Live: {:?}", state.core.players[1].live_zone);

        if state.phase == Phase::Terminal {
            break;
        }
    }

    println!("\n=== FINAL STATE ===");
    println!("Phase: {:?}", state.phase);
    println!("P0 Hand: {:?}", state.core.players[0].hand);
    println!("P1 Hand: {:?}", state.core.players[1].hand);
    println!("P0 Live: {:?}", state.core.players[0].live_zone);
    println!("P1 Live: {:?}", state.core.players[1].live_zone);
}
