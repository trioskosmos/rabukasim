use engine_rust::core::logic::{check_condition_opcode, AbilityContext, CardDatabase, GameState};

#[test]
fn test_repro_count_success_live_comparison() {
    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let db = CardDatabase::default();

    let p1 = 0;
    let ctx = AbilityContext {
        player_id: p1 as u8,
        ..Default::default()
    };

    // Case 1: Player has 0 lives. Condition COUNT_SUCCESS_LIVE {COUNT=0}
    // Compiled as Opcode=218, Val=0, Slot=0 (EQ)
    state.core.players[p1].success_lives.clear();

    let passed = check_condition_opcode(&state, &db, 218, 0, 0, 0, &ctx, 0);
    assert!(passed, "COUNT=0 should pass when lives=0");

    // Case 2: Player has 1 life. Condition COUNT_SUCCESS_LIVE {COUNT=0}
    state.core.players[p1].success_lives.push(101);
    let passed = check_condition_opcode(&state, &db, 218, 0, 0, 0, &ctx, 0);
    // current buggy engine: does 1 >= 0 -> true. Correct: 1 == 0 -> false.
    assert!(!passed, "COUNT=0 should FAIL when lives=1");
}
