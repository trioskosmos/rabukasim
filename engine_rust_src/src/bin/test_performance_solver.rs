use engine_rust::core::logic::game::GameState;
// use engine_rust::core::logic::card_db::{CardDatabase, MemberCard, LiveCard};
use engine_rust::core::analysis::performance_solver::PerformanceProbabilitySolver;
use engine_rust::test_helpers::load_real_db;

fn main() {
    let db = load_real_db();
    
    // Let's find some real cards in the DB
    // We'll look for a live card with some interesting requirements
    // Live: PL!-bp3-026-L (Oh,Love&Peace!)
    // ID 49: Score 6, Req: Pink 2, Yellow 5, Blue 2, Purple 6
    let live_id = 49; 
    let live_card = db.get_live(live_id).expect("Live card 49 not found");
    
    println!("--- TESTING WITH REAL LIVE CARD: {} ({}) ---", live_card.name, live_card.card_no);
    println!("Required Hearts: {:?}", live_card.hearts_board.to_array());
    println!("Base Score: {}", live_card.score);

    // Dynamic Discovery: Find some valid members
    println!("\nSearching for members in DB...");
    let mut valid_members = Vec::new();
    for i in 1..10000 {
        if let Some(m) = db.get_member(i) {
            if m.volume_icons > 0 || valid_members.len() < 10 {
                valid_members.push(i);
                if valid_members.len() == 1 {
                    println!("  Debug Member ID {}: {:?}", i, m);
                }
                if valid_members.len() < 15 {
                    println!("  Found: ID {}, Name: {}, Hearts: {:?}, Volume: {}", i, m.name, m.hearts, m.volume_icons);
                }
            }
        }
        if valid_members.len() >= 100 { break; }
    }

    if valid_members.len() < 3 {
        println!("Error: Found only {} members. Test might fail.", valid_members.len());
    }

    let mut state = GameState::default();
    let p_idx = 0;
    
    // Pick some members for the stage
    if valid_members.len() >= 3 {
        state.core.players[p_idx].stage[0] = valid_members[0];
        state.core.players[p_idx].stage[1] = valid_members[1];
        state.core.players[p_idx].stage[2] = valid_members[2];
    }
    
    // Fill deck with other real cards
    for &mid in valid_members.iter().skip(3) {
        state.core.players[p_idx].deck.push(mid);
    }
    
    state.core.players[p_idx].cheer_mod_count = 10; // 10 yells

    let chance = PerformanceProbabilitySolver::calculate_win_chance(&state, &db, p_idx, live_id);
    
    println!("\nRESULTS (10 Yells):");
    println!("Yells: {}", chance.k_yells);
    println!("Expected Hearts: {:?}", chance.expected_hearts);
    println!("Expected Score: {:.2} (Base {} + Expected Volume Bonus)", chance.expected_score, live_card.score);
    println!("Win Probability (Hearts only): {:.2}%", chance.success_probability * 100.0);

    println!("\n--- SCENARIO: Massive Yells (25) ---");
    state.core.players[p_idx].cheer_mod_count = 25;
    let chance2 = PerformanceProbabilitySolver::calculate_win_chance(&state, &db, p_idx, live_id);
    println!("Win Probability: {:.2}%", chance2.success_probability * 100.0);
    println!("Expected Score: {:.2}", chance2.expected_score);
}
