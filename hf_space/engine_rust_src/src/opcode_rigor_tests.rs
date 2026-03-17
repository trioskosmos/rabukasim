use crate::core::logic::*;
use crate::test_helpers::{create_test_db, create_test_state};

#[test]
fn test_opcode_swap_cards_deck_refresh() {
    let db = create_test_db();
    let mut state = create_test_state();
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // Setup: Deck with 1 card, Discard with 3 cards.
    state.players[0].deck = vec![101].into();
    state.players[0].discard = vec![201, 202, 203].into();
    state.players[0].hand = vec![].into();

    // Opcode 21: O_SWAP_CARDS, v=2 (move 2 cards), target_slot=6 (Hand)
    let bc = vec![O_SWAP_CARDS, 2, 0, 0, 6, O_RETURN, 0, 0, 0, 0];

    state.resolve_bytecode_cref(&db, &bc, &ctx);

    println!("DECK: {:?}", state.players[0].deck);
    println!("HAND: {:?}", state.players[0].hand);

    assert_eq!(
        state.players[0].hand.len(),
        2,
        "Hand size should be 2 after moving 2 cards from deck (including refresh)"
    );
    assert_eq!(
        state.players[0].deck.len(),
        2,
        "Deck size should be 2 after moving 2 cards from deck+discard (total 4)"
    );
}

#[test]
fn test_opcode_increase_cost_ripple() {
    let db = create_test_db();
    let mut state = create_test_state();
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        ..Default::default()
    };

    // Member 3000 baseline cost is 1 in create_test_db
    let base_cost = state.get_member_cost(0, 3000, -1, -1, &db, 0);

    // Opcode 70: O_INCREASE_COST, v=2
    let bc = vec![O_INCREASE_COST, 2, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    let new_cost = state.get_member_cost(0, 3000, -1, -1, &db, 0);
    assert_eq!(
        new_cost,
        base_cost + 2,
        "Cost should increase by 2 (Baseline: {}, Actual: {})",
        base_cost,
        new_cost
    );
}

#[test]
fn test_opcode_select_live_rigor() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.players[0].live_zone[0] = 55001;
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        ..Default::default()
    };

    // Opcode 68: O_SELECT_LIVE, v=1 (Count 1)
    let bc = vec![O_SELECT_LIVE, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

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
        ChoiceType::SelectLive
    );

    // Submit choice for Live 55001 (idx 0)
    // SELECT_LIVE uses ACTION_BASE_STAGE_SLOTS for live zone slot selection
    let _ = state.step(&db, ACTION_BASE_STAGE_SLOTS + 0);

    assert_eq!(state.phase, Phase::Main, "Should resume to Phase::Main");
    assert!(
        state.interaction_stack.is_empty(),
        "Interaction stack should be empty after response"
    );
}

#[test]
fn test_opcode_opponent_choose_rigor() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.debug.debug_mode = true;
    // Use card 3001 which has O_OPPONENT_CHOOSE -> O_DRAW bytecode
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        source_card_id: 3001,
        ..Default::default()
    };

    // Get bytecode from card 3001
    let bc = if let Some(m) = db.get_member(3001) {
        m.abilities[0].bytecode.clone()
    } else {
        panic!("Card 3001 not found in test DB");
    };

    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(state.phase, Phase::Response);
    let interaction = state.interaction_stack.last().unwrap();
    println!(
        "DEBUG: interaction.ctx.player_id = {}",
        interaction.ctx.player_id
    );
    assert_eq!(
        interaction.ctx.player_id, 1,
        "Opponent (P1) should be the chooser"
    );

    let _ = state.step(&db, ACTION_BASE_CHOICE + 0); // P1 chooses index 0

    println!(
        "DEBUG: P0 hand len = {}, P1 hand len = {}",
        state.players[0].hand.len(),
        state.players[1].hand.len()
    );
    assert_eq!(state.phase, Phase::Main);
    // Note: O_OPPONENT_CHOOSE flips ctx.player_id during resumption.
    // Subsequent opcodes (O_DRAW) use the flipped context.
    assert_eq!(
        state.players[1].hand.len(),
        1,
        "Player 1 should have drawn the card due to context flip"
    );
}

#[test]
fn test_opcode_reduce_yell_count_functional() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.current_player = 0;
    state.players[0].deck = vec![3000, 3001, 3002].into();
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        ..Default::default()
    };

    // Opcode 62: O_REDUCE_YELL_COUNT, v=1
    let bc = vec![O_REDUCE_YELL_COUNT, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Call do_yell for 2 cards
    let revealed = crate::core::logic::performance::do_yell(&mut state, &db, 2);
    assert_eq!(
        revealed.len(),
        1,
        "Should reveal only 1 card due to reduction"
    );
}

#[test]
fn test_opcode_prevent_activate_rigor() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.current_player = 0;
    state.players[0].stage[0] = 3000;
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        ..Default::default()
    };

    // Opcode 82: O_PREVENT_ACTIVATE
    let bc = vec![O_PREVENT_ACTIVATE, 0, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Verify prevent_activate flag is set
    assert_eq!(
        state.players[0].prevent_activate, 1,
        "prevent_activate flag should be set"
    );

    // Cid 3121 has index 0 activated ability
    state.players[0].stage[0] = 3121;
    let res = state.activate_ability(&db, 0, 0);
    assert!(res.is_err(), "Activation should be blocked by restriction");
    assert!(res.unwrap_err().contains("restriction"));
}

#[test]
fn test_opcode_add_stage_energy_functional() {
    let db = create_test_db();
    let mut state = create_test_state();
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        ..Default::default()
    };

    state.players[0].stage[0] = 3000; // Member in slot 0 (exists in test DB)
    state.players[0].stage_energy[0] = vec![].into();

    // Add 2 stage energy. Opcode 50.
    let bc = vec![O_ADD_STAGE_ENERGY, 2, 0, 0, 4, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Verify stage_energy was added
    assert_eq!(state.players[0].stage_energy[0].len(), 2);
    assert_eq!(state.players[0].stage_energy_count[0], 2);

    // Verify the energy cards are CID 2000 (test energy card)
    assert_eq!(state.players[0].stage_energy[0][0], 2000);
    assert_eq!(state.players[0].stage_energy[0][1], 2000);
}
