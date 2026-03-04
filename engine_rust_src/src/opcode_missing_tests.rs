use crate::core::hearts::HeartBoard;
use crate::core::logic::*;
use crate::test_helpers::{create_test_db, create_test_state};
// use std::collections::HashMap;

#[test]
fn test_opcode_select_member() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Member in slot 0
    state.core.players[0].stage[0] = 10;

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // O_SELECT_MEMBER 1 (Count 1)
    let bc = vec![O_SELECT_MEMBER, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Updated behavior: Should enter Response phase and set pending choice
    assert_eq!(
        state.phase,
        Phase::Response,
        "O_SELECT_MEMBER should enter Phase::Response"
    );
    assert_eq!(
        state
            .interaction_stack
            .last()
            .map(|i| i.choice_type)
            .unwrap_or(ChoiceType::None),
        ChoiceType::SelectMember,
        "Pending choice type mismatch"
    );
}

#[test]
fn test_opcode_select_live() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Live in slot 0
    state.core.players[0].live_zone[0] = 1001;

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // O_SELECT_LIVE 1
    let bc = vec![O_SELECT_LIVE, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Updated behavior
    assert_eq!(
        state.phase,
        Phase::Response,
        "O_SELECT_LIVE should enter Phase::Response"
    );
    assert_eq!(
        state
            .interaction_stack
            .last()
            .map(|i| i.choice_type)
            .unwrap_or(ChoiceType::None),
        ChoiceType::SelectLive,
        "Pending choice type mismatch"
    );
}

#[test]
fn test_opcode_opponent_choose() {
    let db = create_test_db();
    let mut state = create_test_state();

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // O_OPPONENT_CHOOSE
    let bc = vec![O_OPPONENT_CHOOSE, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Updated behavior
    assert_eq!(
        state.phase,
        Phase::Response,
        "O_OPPONENT_CHOOSE should enter Phase::Response"
    );
    assert_eq!(
        state
            .interaction_stack
            .last()
            .map(|i| i.choice_type)
            .unwrap_or(ChoiceType::None),
        ChoiceType::OpponentChoose,
        "Pending choice type mismatch"
    );

    // Verify player context might be flipped?
    // In implementation: `p_ctx.player_id = 1 - p_idx as u8;`
    // Let's check pending_ctx
    if let Some(interaction) = state.interaction_stack.last() {
        assert_eq!(
            interaction.ctx.player_id, 1,
            "Pending context should be for opponent (player 1)"
        );
    }
}

#[test]
fn test_opcode_prevent_activate() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Add a dummy member to DB
    let mut m = MemberCard::default();
    m.card_id = 100;
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        costs: vec![Cost {
            cost_type: AbilityCostType::None,
            value: 0,
            ..Default::default()
        }],
        ..Default::default()
    });
    db.members.insert(12343, m.clone());

    // Place member on stage
    state.core.players[0].stage[0] = 12343;

    // 1. Initial check: Activation possible (mock check, logic.rs handles this)
    // We can't fully mock activate_ability without a complex DB setup,
    // but we can check the flag and the specific error condition if possible.
    // For now, let's verify the flag setting and the error from activate_ability.

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // 2. Apply Restriction
    // O_PREVENT_ACTIVATE, val=0, attr=0, target=0 (Self)
    let bc = vec![O_PREVENT_ACTIVATE, 0, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(
        state.core.players[0].prevent_activate, 1,
        "Flag should be set"
    );

    // 3. Try to activate
    // activate_ability uses current_player
    state.current_player = 0;
    // activate_ability(db, slot_idx, ab_idx)
    let res = state.activate_ability(&db, 0, 0);
    assert!(res.is_err(), "Activation should fail");
    // Depending on logic.rs implementation, error string might vary slightly
    // logic.rs: "Cannot activate abilities due to restriction"
    if let Err(e) = res {
        assert!(
            e.contains("restriction"),
            "Error should mention restriction: {}",
            e
        );
    }
}

#[test]
fn test_opcode_prevent_baton_touch() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Dummy member
    let mut m = MemberCard::default();
    m.card_id = 10;
    m.cost = 1;
    // Need abilities list initialized
    m.abilities = vec![];
    db.members.insert(19, m.clone());

    // Setup: Slot 0 has a card (ID 10)
    state.core.players[0].stage[0] = 10;
    state.core.players[0].baton_touch_limit = 1;
    state.core.players[0].hand.push(19); // Card to play
    state.core.players[0].hand_added_turn.push(0);

    // Give energy
    state.core.players[0].tapped_energy_mask = 0; // 2 energy

    // 1. Apply Restriction (Global prevent baton touch on player)
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    // O_PREVENT_BATON_TOUCH
    let bc = vec![O_PREVENT_BATON_TOUCH, 0, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(
        state.core.players[0].prevent_baton_touch, 1,
        "Flag should be set"
    );

    // 2. Try to Baton Touch (Play to slot 0)
    state.current_player = 0;
    let res = state.play_member(&db, 0, 0); // hand_idx=0, slot_idx=0
    assert!(res.is_err(), "Baton touch should fail");
    if let Err(e) = res {
        assert!(
            e.contains("restricted"),
            "Error should mention restricted: {}",
            e
        );
    }
}

#[test]
fn test_opcode_prevent_play_to_slot() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Dummy
    let mut m = MemberCard::default();
    m.card_id = 10;
    m.cost = 0;
    m.abilities = vec![];
    db.members.insert(10, m.clone());

    state.core.players[0].hand.push(10); // idx 0
    state.core.players[0].hand.push(10); // idx 1 (if needed)
    state.core.players[0].hand_added_turn.push(0);
    state.core.players[0].hand_added_turn.push(0);

    // 1. Apply Restriction to Slot 1 (Target=1)
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    // O_PREVENT_PLAY_TO_SLOT, val=0, attr=0, target_slot=1 (s parameter)
    // interpreter.rs: if target_slot >= 0 && target_slot < 3 ...
    // bc[3] is s/target_slot.
    let bc = vec![O_PREVENT_PLAY_TO_SLOT, 0, 0, 0, 1, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_ne!(
        state.core.players[0].prevent_play_to_slot_mask & (1 << 1),
        0,
        "Mask should be set for slot 1"
    );

    // 2. Try to play to Slot 1
    state.current_player = 0;
    let res = state.play_member(&db, 0, 1); // hand_idx 0 to slot 1
    assert!(res.is_err(), "Play to slot 1 should fail");
    if let Err(e) = res {
        assert!(
            e.contains("restriction"),
            "Error should mention restriction: {}",
            e
        );
    }
}

#[test]
fn test_opcode_heart_modifiers() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Create Live Card
    let mut l = LiveCard::default();
    l.card_id = 10001;
    l.name = "Test Live".to_string();
    // Requirements: 1 Pink (idx 0), 1 Red (idx 1)
    l.required_hearts = [10, 1, 0, 0, 0, 0, 0];
    l.hearts_board = HeartBoard::from_array(&l.required_hearts);

    // Ability 1: Increase Pink Cost by 1 (O_INCREASE_HEART_COST 1, 1 (Pink))
    // Ability 2: Transform Red to Blue (O_TRANSFORM_HEART 2(Red), 5(Blue))
    l.abilities.push(Ability {
        trigger: TriggerType::Constant,
        bytecode: vec![
            O_INCREASE_HEART_COST,
            1,
            1,
            0,
            0,
            O_TRANSFORM_HEART,
            2,
            5,
            0,
            0,
            O_RETURN,
            0,
            0,
            0,
            0,
        ],
        ..Default::default()
    });

    db.lives.insert(10001, l.clone());

    // Set up state
    state.core.players[0].live_zone[0] = 10001;
    state.core.players[0].live_zone[1] = -1;
    state.core.players[0].live_zone[2] = -1;

    // Verify Logic via check_live_success directly?
    // Or simulate total_hearts and see if it passes.

    // Requirement expectation:
    // Base: 1 Pink, 1 Red
    // Increase Pink by 1 -> 2 Pink
    // Transform Red (10) to Blue -> 0 Red, 1 Blue
    // Final: 2 Pink, 0 Red, 1 Blue.

    let pass_hearts = [11, 0, 0, 0, 1, 0, 0]; // Exact match
    let fail_hearts = [10, 1, 0, 0, 0, 0, 0]; // Original requirements (should fail)

    assert!(
        state.check_live_success(&db, 0, &l, &pass_hearts),
        "Should pass with modified requirements"
    );
    assert!(
        !state.check_live_success(&db, 0, &l, &fail_hearts),
        "Should fail with original requirements"
    );
}
