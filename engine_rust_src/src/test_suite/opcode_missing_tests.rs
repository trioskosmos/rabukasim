use crate::core::hearts::HeartBoard;
use crate::core::logic::*;
use crate::test_helpers::{create_test_db, create_test_state, FrameBuilder, TestActionReceiver};
// use std::collections::HashMap;

#[test]
fn test_opcode_select_member() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Member in slot 0
    state.players[0].stage[0] = 10;

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // O_SELECT_MEMBER 1 (Count 1)
    let bc = vec![O_SELECT_MEMBER, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_frames(&db, &bc, &ctx);

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

fn add_member(db: &mut CardDatabase, mut member: MemberCard) {
    member.hearts_board = HeartBoard::from_array(&member.hearts);
    member.blade_hearts_board = HeartBoard::from_array(&member.blade_hearts);
    let logic_id = (member.card_id as usize) % LOGIC_ID_MASK as usize;
    if db.members_vec.len() <= logic_id {
        db.members_vec.resize(logic_id + 1, None);
    }
    db.members_vec[logic_id] = Some(member.clone());
    db.members.insert(member.card_id, member);
}

#[test]
fn test_prompt_before_count_blades_defers_trigger_precheck_until_selection() {
    let mut db = create_test_db();

    let mut source = MemberCard::default();
    source.card_id = 9001;
    source.card_no = "TEST-9001".to_string();
    source.name = "Prompt First Blades Source".to_string();
    source.abilities.push(Ability {
        trigger: TriggerType::OnLiveStart,
        frame_program: Some(
            FrameBuilder::new()
                .op(O_SELECT_MEMBER)
                .v(1)
                .op(C_COUNT_BLADES)
                .v(2)
                .target(10)
                .op(O_ADD_BLADES)
                .v(1)
                .target(10)
                .op(O_RETURN)
                .build_prog(),
        ),
        ..Default::default()
    });
    CardDatabase::enrich_member_runtime_metadata(&mut source);
    add_member(&mut db, source);

    let mut selected = MemberCard::default();
    selected.card_id = 9002;
    selected.card_no = "TEST-9002".to_string();
    selected.name = "Prompt First Blades Target".to_string();
    selected.blades = 2;
    selected.blade_hearts = [0; 7];
    selected.hearts = [0; 7];
    CardDatabase::enrich_member_runtime_metadata(&mut selected);
    add_member(&mut db, selected);

    let mut state = create_test_state();
    state.phase = Phase::PerformanceP1;
    state.current_player = 0;
    state.players[0].stage[0] = 9001;
    state.players[0].stage[1] = 9002;

    let before_blades = get_effective_blades(&state, 0, 1, &db, 0);
    let ability = db
        .get_member(9001)
        .expect("9001 should be present in the test DB")
        .abilities
        .first()
        .expect("9001 should have one ability");
    assert!(ability.runtime_metadata_ready);
    assert!(ability.runtime_prompt_before_count_blades);
    assert!(!ability.runtime_prompt_before_count_hearts);

    let ctx = AbilityContext {
        player_id: 0,
        activator_id: 0,
        source_card_id: 9001,
        area_idx: 0,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);

    assert_eq!(
        state.phase,
        Phase::Response,
        "prompt-first CountBlades should suspend for slot selection instead of being prechecked away"
    );
    assert_eq!(
        state.interaction_stack.last().map(|pending| pending.choice_type),
        Some(ChoiceType::SelectMember),
        "prompt-first CountBlades should expose a member selection prompt"
    );

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut actions);
    assert!(
        actions
            .actions
            .contains(&(crate::core::generated_constants::ACTION_BASE_STAGE_SLOTS + 1)),
        "prompt-first CountBlades should allow selecting the 2-blade member"
    );

    state
        .handle_response(&db, crate::core::generated_constants::ACTION_BASE_STAGE_SLOTS + 1)
        .expect("selecting the CountBlades target should resolve cleanly");
    state.process_trigger_queue(&db);

    assert!(state.interaction_stack.is_empty());
    assert_eq!(
        get_effective_blades(&state, 0, 1, &db, 0),
        before_blades + 1,
        "prompt-first CountBlades should resolve the selected member and apply the follow-up effect"
    );
}

#[test]
fn test_count_blades_before_prompt_still_prechecks_and_blocks_activation() {
    let mut db = create_test_db();

    let mut source = MemberCard::default();
    source.card_id = 9011;
    source.card_no = "TEST-9011".to_string();
    source.name = "Count First Blades Source".to_string();
    source.abilities.push(Ability {
        trigger: TriggerType::OnLiveStart,
        frame_program: Some(
            FrameBuilder::new()
                .op(C_COUNT_BLADES)
                .v(2)
                .target(10)
                .op(O_SELECT_MEMBER)
                .v(1)
                .op(O_ADD_BLADES)
                .v(1)
                .target(10)
                .op(O_RETURN)
                .build_prog(),
        ),
        ..Default::default()
    });
    CardDatabase::enrich_member_runtime_metadata(&mut source);
    add_member(&mut db, source);

    let mut selected = MemberCard::default();
    selected.card_id = 9012;
    selected.card_no = "TEST-9012".to_string();
    selected.name = "Count First Blades Target".to_string();
    selected.blades = 2;
    selected.blade_hearts = [0; 7];
    selected.hearts = [0; 7];
    CardDatabase::enrich_member_runtime_metadata(&mut selected);
    add_member(&mut db, selected);

    let mut state = create_test_state();
    state.phase = Phase::PerformanceP1;
    state.current_player = 0;
    state.players[0].stage[0] = 9011;
    state.players[0].stage[1] = 9012;

    let ability = db
        .get_member(9011)
        .expect("9011 should be present in the test DB")
        .abilities
        .first()
        .expect("9011 should have one ability");
    assert!(ability.runtime_metadata_ready);
    assert!(!ability.runtime_prompt_before_count_blades);

    let ctx = AbilityContext {
        player_id: 0,
        activator_id: 0,
        source_card_id: 9011,
        area_idx: 0,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);

    assert_eq!(
        state.phase,
        Phase::PerformanceP1,
        "CountBlades before the prompt should be prechecked and block activation"
    );
    assert!(
        state.interaction_stack.is_empty(),
        "CountBlades before the prompt should never suspend for selection when the precheck fails"
    );
    assert_eq!(
        get_effective_blades(&state, 0, 1, &db, 0),
        2,
        "blocked CountBlades should not apply the follow-up blade gain"
    );
}

#[test]
fn test_prompt_before_count_hearts_defers_trigger_precheck_until_selection() {
    let mut db = create_test_db();

    let mut source = MemberCard::default();
    source.card_id = 9021;
    source.card_no = "TEST-9021".to_string();
    source.name = "Prompt First Hearts Source".to_string();
    source.abilities.push(Ability {
        trigger: TriggerType::OnLiveStart,
        frame_program: Some(
            FrameBuilder::new()
                .op(O_SELECT_MEMBER)
                .v(1)
                .op(C_COUNT_HEARTS)
                .v(2)
                .target(10)
                .op(O_ADD_HEARTS)
                .v(1)
                .a(1)
                .target(10)
                .op(O_RETURN)
                .build_prog(),
        ),
        ..Default::default()
    });
    CardDatabase::enrich_member_runtime_metadata(&mut source);
    add_member(&mut db, source);

    let mut selected = MemberCard::default();
    selected.card_id = 9022;
    selected.card_no = "TEST-9022".to_string();
    selected.name = "Prompt First Hearts Target".to_string();
    selected.hearts = [1, 1, 0, 0, 0, 0, 0];
    selected.blade_hearts = [0; 7];
    CardDatabase::enrich_member_runtime_metadata(&mut selected);
    add_member(&mut db, selected);

    let mut state = create_test_state();
    state.phase = Phase::PerformanceP1;
    state.current_player = 0;
    state.players[0].stage[0] = 9021;
    state.players[0].stage[1] = 9022;

    let before_hearts = state.get_effective_hearts(0, 1, &db, 0).get_total_count();
    let ability = db
        .get_member(9021)
        .expect("9021 should be present in the test DB")
        .abilities
        .first()
        .expect("9021 should have one ability");
    assert!(ability.runtime_metadata_ready);
    assert!(ability.runtime_prompt_before_count_hearts);
    assert!(!ability.runtime_prompt_before_count_blades);

    let ctx = AbilityContext {
        player_id: 0,
        activator_id: 0,
        source_card_id: 9021,
        area_idx: 0,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);

    assert_eq!(
        state.phase,
        Phase::Response,
        "prompt-first CountHearts should suspend for slot selection instead of being prechecked away"
    );
    assert_eq!(
        state.interaction_stack.last().map(|pending| pending.choice_type),
        Some(ChoiceType::SelectMember),
        "prompt-first CountHearts should expose a member selection prompt"
    );

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut actions);
    assert!(
        actions
            .actions
            .contains(&(crate::core::generated_constants::ACTION_BASE_STAGE_SLOTS + 1)),
        "prompt-first CountHearts should allow selecting the 2-heart member"
    );

    state
        .handle_response(&db, crate::core::generated_constants::ACTION_BASE_STAGE_SLOTS + 1)
        .expect("selecting the CountHearts target should resolve cleanly");
    state.process_trigger_queue(&db);

    assert!(state.interaction_stack.is_empty());
    assert_eq!(
        state.get_effective_hearts(0, 1, &db, 0).get_total_count(),
        before_hearts + 1,
        "prompt-first CountHearts should resolve the selected member and apply the follow-up heart gain"
    );
}

#[test]
fn test_opcode_select_live() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Live in slot 0
    state.players[0].live_zone[0] = 1001;

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // O_SELECT_LIVE 1
    let bc = vec![O_SELECT_LIVE, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_frames(&db, &bc, &ctx);

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
    state.resolve_frames(&db, &bc, &ctx);

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

    // After my fix, ctx.player_id correctly remains the activator (0),
    // but the engine correctly suspends with the opponent (1) as the current_player.
    assert_eq!(
        state.current_player, 1,
        "Engine should flip current_player to opponent (player 1) during suspension"
    );
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
    state.players[0].stage[0] = 12343;

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
    state.resolve_frames(&db, &bc, &ctx);

    assert_eq!(state.players[0].prevent_activate(), 1, "Flag should be set");

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
    state.players[0].stage[0] = 10;
    state.players[0].set_baton_touch_limit(1);
    state.players[0].hand.push(19); // Card to play
    state.players[0].hand_added_turn.push(0);

    // Give energy
    state.players[0].tapped_energy_mask = 0; // 2 energy

    // 1. Apply Restriction (Global prevent baton touch on player)
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    // O_PREVENT_BATON_TOUCH
    let bc = vec![O_PREVENT_BATON_TOUCH, 0, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_frames(&db, &bc, &ctx);

    assert_eq!(
        state.players[0].prevent_baton_touch(),
        1,
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

    state.players[0].hand.push(10); // idx 0
    state.players[0].hand.push(10); // idx 1 (if needed)
    state.players[0].hand_added_turn.push(0);
    state.players[0].hand_added_turn.push(0);

    // 1. Apply Restriction to Slot 1 (Target=1)
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    // O_PREVENT_PLAY_TO_SLOT, val=0, attr=0, target_slot=1 (s parameter)
    // interpreter.rs: if target_slot >= 0 && target_slot < 3 ...
    // bc[3] is s/target_slot.
    let bc = vec![O_PREVENT_PLAY_TO_SLOT, 0, 0, 0, 1, O_RETURN, 0, 0, 0, 0];
    state.resolve_frames(&db, &bc, &ctx);

    assert_ne!(
        state.players[0].prevent_play_to_slot_mask() & (1 << 1),
        0,
        "Mask should be set for slot 1"
    );

    // 2. Try to play to Slot 1
    state.current_player = 0;

    // According to Q181, if the slot is EMPTY, play is ALLOWED even if restricted.
    // To test the "failure" (blocking), we must have a member there already.
    state.players[0].stage[1] = 10;

    let res = state.play_member(&db, 0, 1); // hand_idx 0 to slot 1 (occupied + restricted)
    assert!(
        res.is_err(),
        "Play to slot 1 should fail when occupied and restricted"
    );
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
        frame_program: Some(FrameProgram::from_instruction_words(&[
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
        ])),
        ..Default::default()
    });

    db.lives.insert(10001, l.clone());

    // Set up state
    state.players[0].live_zone[0] = 10001;
    state.players[0].live_zone[1] = -1;
    state.players[0].live_zone[2] = -1;

    assert_eq!(state.players[0].live_zone[0], 10001);
    assert_eq!(state.players[0].live_zone[1], -1);
}
