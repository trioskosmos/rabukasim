use engine_rust::core::enums::{ChoiceType, Phase};
use engine_rust::test_helpers::{create_test_state, load_real_db};

#[test]
fn card_574_discards_itself_without_stage_selection() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.phase = Phase::Main;
    state.current_player = 0;
    state.ui.silent = true;

    state.players[0].stage = [574, 121, 124];

    state
        .activate_ability(&db, 0, 0)
        .expect("card 574 should activate cleanly");

    assert_eq!(state.players[0].stage[0], -1);
    assert_eq!(state.players[0].stage[1], 121);
    assert_eq!(state.players[0].stage[2], 124);
    assert!(state.players[0].discard.contains(&574));
    if let Some(pending) = state.interaction_stack.last() {
        assert_ne!(pending.choice_type, ChoiceType::SelectStage);
    }
}
