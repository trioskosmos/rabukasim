use crate::test_helpers::{create_test_db, create_test_state};
use crate::core::logic::*;
use crate::core::logic::handlers::PhaseHandlers;

#[test]
fn test_score_jump_repro() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.phase = Phase::LiveResult;

    // Player 0 has 1 success life already
    state.core.players[0].success_lives.push(55001);
    state.core.players[0].score = 1;

    // Player 0 has two live cards in zone
    let live_id_1 = 55001; 
    let live_id_2 = 55001;
    state.core.players[0].live_zone[0] = live_id_1;
    state.core.players[0].live_zone[1] = live_id_2;

    // Mock performance results showing both passed
    state.ui.performance_results.insert(0, serde_json::json!({
        "success": true,
        "lives": [
            {"passed": true, "score": 1, "slot_idx": 0},
            {"passed": true, "score": 1, "slot_idx": 1},
            {"passed": false, "score": 0, "slot_idx": 2}
        ]
    }));

    // Trigger do_live_result. 
    // It should see 2 valid candidates and set live_result_selection_pending = true
    state.do_live_result(&db);

    assert!(state.live_result_selection_pending, "Should be pending selection");
    assert_eq!(state.core.players[0].success_lives.len(), 1, "Should still have 1 life before selection");

    // Simulate selection of first card (action 600)
    // In the BUGGY version, this calls do_live_result() again.
    // Inside that call, valid_candidates will now be 1 (the remaining card).
    // It will AUTO-MOVE that card, pushing it to success_lives.
    // Then handle_liveresult itself pushed the selected card.
    // Total: 1 (original) + 1 (auto-move) + 1 (selected) = 3.
    state.handle_liveresult(&db, 600).expect("Selection should work");

    // After selection, we expect exactly 2 lives (1 original + 1 selected)
    // If the bug exists, this will be 3.
    assert_eq!(state.core.players[0].success_lives.len(), 2, "Should have exactly 2 lives after selecting one of two");
}
