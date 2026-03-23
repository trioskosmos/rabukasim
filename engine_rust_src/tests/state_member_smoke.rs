use engine_rust::core::logic::interpreter::instruction::BytecodeInstruction;
use engine_rust::core::logic::{AbilityContext, Phase};
use engine_rust::test_helpers::{create_test_db, create_test_state, BytecodeBuilder};

#[test]
fn set_tapped_updates_the_requested_stage_slot() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.phase = Phase::Main;
    state.players[0].set_tapped(1, false);

    let mut ctx = AbilityContext::default();
    ctx.player_id = 0;

    let words = BytecodeBuilder::new(engine_rust::core::logic::O_SET_TAPPED)
        .v(1)
        .slot(1)
        .build();
    let instr = BytecodeInstruction::decode(&words, 0);

    state.resolve_bytecode_slice(&db, &words, &ctx);

    assert!(state.players[0].is_tapped(1));
    assert!(!state.players[0].is_tapped(0));
    assert!(!state.players[0].is_tapped(2));
    assert_eq!(instr.op, engine_rust::core::logic::O_SET_TAPPED);
}

#[test]
fn activate_member_clears_the_requested_tapped_slot() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.phase = Phase::Main;
    state.players[0].set_tapped(0, true);
    state.players[0].set_tapped(1, false);
    state.players[0].set_tapped(2, false);

    let mut ctx = AbilityContext::default();
    ctx.player_id = 0;
    ctx.source_card_id = 3000;

    let words = BytecodeBuilder::new(engine_rust::core::logic::O_ACTIVATE_MEMBER)
        .v(0)
        .slot(0)
        .build();

    state.resolve_bytecode_slice(&db, &words, &ctx);

    assert!(!state.players[0].is_tapped(0));
    assert!(!state.players[0].is_tapped(1));
    assert!(!state.players[0].is_tapped(2));
    assert_eq!(state.players[0].activated_member_group_mask, 1 << 1);
}

#[test]
fn play_member_from_discard_places_the_selected_card() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.phase = Phase::Main;
    state.players[0].discard.clear();
    state.players[0].discard.push(3000);
    state.players[0].looked_cards.clear();
    state.players[0].looked_cards.push(3000);
    state.players[0].stage[0] = -1;

    let mut ctx = AbilityContext::default();
    ctx.player_id = 0;
    ctx.activator_id = 0;
    ctx.choice_index = 0;
    ctx.v_remaining = 1;

    let words = BytecodeBuilder::new(engine_rust::core::logic::O_PLAY_MEMBER_FROM_DISCARD)
        .v(1)
        .slot(0)
        .build();

    state.resolve_bytecode_slice(&db, &words, &ctx);

    assert_eq!(state.players[0].stage[0], 3000);
    assert!(state.players[0].is_tapped(0));
    assert!(state.players[0].is_moved(0));
    assert!(state.players[0].discard.is_empty());
}
