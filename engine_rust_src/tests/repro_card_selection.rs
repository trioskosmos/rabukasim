use engine_rust::core::logic::*;
use engine_rust::test_helpers::{create_test_state, load_real_db, TestActionReceiver};

#[test]
fn test_card_selection_filtering() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.debug.debug_mode = true;
    state.phase = Phase::Main;

    let muse_cid = 100;
    let aqours_cid = 8587;

    // Put Muse member in slot 0, Aqours member in slot 1
    state.players[0].stage[0] = muse_cid;
    state.players[0].stage[1] = aqours_cid;
    state.players[0].stage[2] = -1;

    let mut ctx = AbilityContext::default();
    ctx.player_id = 0;

    // Add pending interaction for SELECT_MEMBER
    let pending = PendingInteraction {
        card_id: aqours_cid,
        ability_index: 0,
        choice_type: ChoiceType::SelectMember,
        choice_text: "Choose Aqours member".to_string(),
        filter_attr: 48, // Group Filter for Aqours (enabled bit 0x10 + Group ID 1 << 5 = 0x20 = 48)
        v_remaining: 1,
        effect_opcode: 65, // O_SELECT_MEMBER
        ctx: ctx,
        original_phase: Phase::Main,
        original_current_player: 0,
        ..Default::default()
    };
    state.interaction_stack.push(pending);
    state.phase = Phase::Response;

    let mut receiver = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut receiver);
    let actions = receiver.actions;

    println!("Legal actions: {:?}", actions);

    // ACTION_BASE_STAGE_SLOTS (600) + slot
    // We expect action 600 (slot 0 - Muse) to NOT be present,
    // and action 601 (slot 1 - Aqours) to be present.
    assert!(
        !actions.contains(&600),
        "Should not allow selecting Muse member (Slot 0)"
    );
    assert!(
        actions.contains(&601),
        "Should allow selecting Aqours member (Slot 1)"
    );
}
