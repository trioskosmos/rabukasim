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

#[test]
fn test_repro_count_success_live_opponent() {
    let mut state = GameState::default();
    state.debug.debug_mode = true;
    let db = CardDatabase::default();

    let p1 = 0;
    let ctx = AbilityContext {
        player_id: p1 as u8,
        ..Default::default()
    };

    // FILTER_OPPONENT is 1 << 41
    let filter_opponent = 1u64 << 41;

    // Case: Player has 0 lives, Opponent has 1 life.
    // Condition: COUNT_SUCCESS_LIVE {MIN=1, PLAYER=1}
    state.core.players[p1].success_lives.clear();
    state.core.players[1].success_lives.clear();
    state.core.players[1].success_lives.push(101);

    // Opcode=218, Val=1, Attr=FILTER_OPPONENT, Slot=0 (GE)
    let passed = check_condition_opcode(&state, &db, 218, 1, filter_opponent, 0, &ctx, 0);
    // Expected: true (checking opponent who has 1). Buggy result: false (checking self who has 0).
    assert!(
        passed,
        "MIN=1, PLAYER=1 should pass when opponent has 1 life"
    );
}
