use crate::test_helpers::{create_test_state, load_real_db};
use crate::core::logic::*;
use serde_json::json;

#[test]
fn test_megaphone_scoring_accumulation() {
    let db = load_real_db();
    let mut state = create_test_state();
    
    // Setup a winning performance with 1 card (ID 121, Eli, Score 1) and 2 megaphones
    state.ui.performance_results.insert(0, json!({
        "success": true,
        "total_score": 3, // 1 (base) + 2 (volume)
        "lives": [{"slot_idx": 0, "score": 1, "passed": true}]
    }));
    state.core.players[0].live_zone[0] = 137; // START:DASH!!
    state.obtained_success_live[0] = true;
    
    // Finalize should add 3 to persistent score
    state.finalize_live_result();
    
    assert_eq!(state.core.players[0].score, 3, "Persistent score should accumulate performance score");
}

#[test]
fn test_rule_8_4_7_1_success_cap_on_tie() {
    let db = load_real_db();
    let mut state = create_test_state();
    
    // SCENARIO 1: Tie at 1-0 success lives
    // Result: Both should move 1 card -> 2-1 lives.
    state.core.players[0].success_lives = vec![137].into(); // 1 life
    state.core.players[1].success_lives = vec![].into();    // 0 lives
    
    state.ui.performance_results.insert(0, json!({"success": true, "total_score": 10}));
    state.ui.performance_results.insert(1, json!({"success": true, "total_score": 10}));
    state.core.players[0].live_zone = [137, -1, -1];
    state.core.players[1].live_zone = [137, -1, -1];

    state.do_live_result(&db);
    
    assert_eq!(state.core.players[0].success_lives.len(), 2, "P0 should move 1 card (1->2)");
    assert_eq!(state.core.players[1].success_lives.len(), 1, "P1 should move 1 card (0->1)");

    // SCENARIO 2: Tie at 2-1 success lives
    // Result: P0 (at 2) stays at 2. P1 (at 1) moves to 2 -> 2-2 lives.
    let mut state2 = create_test_state();
    state2.players[0].success_lives = vec![137, 137].into(); // 2 lives
    state2.players[1].success_lives = vec![137].into();      // 1 life
    
    state2.ui.performance_results.insert(0, json!({"success": true, "total_score": 10}));
    state2.ui.performance_results.insert(1, json!({"success": true, "total_score": 10}));
    state2.players[0].live_zone = [137, -1, -1];
    state2.players[1].live_zone = [137, -1, -1];

    state2.do_live_result(&db);
    
    assert_eq!(state2.players[0].success_lives.len(), 2, "P0 should NOT move (stays at 2)");
    assert_eq!(state2.players[1].success_lives.len(), 2, "P1 should move (1->2)");

    // SCENARIO 3: Tie at 2-2 success lives
    // Result: Both stay at 2 -> 2-2 lives.
    let mut state3 = create_test_state();
    state3.players[0].success_lives = vec![137, 137].into(); // 2 lives
    state3.players[1].success_lives = vec![137, 137].into(); // 2 lives
    
    state3.ui.performance_results.insert(0, json!({"success": true, "total_score": 10}));
    state3.ui.performance_results.insert(1, json!({"success": true, "total_score": 10}));
    state3.players[0].live_zone = [137, -1, -1];
    state3.players[1].live_zone = [137, -1, -1];

    state3.do_live_result(&db);
    
    assert_eq!(state3.players[0].success_lives.len(), 2, "P0 stays at 2");
    assert_eq!(state3.players[1].success_lives.len(), 2, "P1 stays at 2");
}

#[test]
fn test_rule_8_4_13_first_player_logic() {
    let _db = load_real_db();
    let mut state = create_test_state();
    state.first_player = 0;
    
    // Case 1: P1 obtains a live, P0 doesn't -> P1 becomes first
    state.obtained_success_live = [false, true];
    state.finalize_live_result();
    assert_eq!(state.first_player, 1);
    
    // Case 2: Both obtain lives -> remains P1
    state.obtained_success_live = [true, true];
    state.finalize_live_result();
    assert_eq!(state.first_player, 1);
}
