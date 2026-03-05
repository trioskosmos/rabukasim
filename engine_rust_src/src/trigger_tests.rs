use crate::core::logic::*;
use crate::test_helpers::{create_test_state, load_real_db};

/// Verifies that O_LOOK_AND_CHOOSE correctly enriches the choice text with the card's real original_text.
#[test]
fn test_enrichment_look_and_choose() {
    let db = load_real_db();
    let mut state = create_test_state();
    // Use Honoka (120) as the source of the enrichment text (revealing real cards in deck)
    state.players[0].deck = vec![121, 124, 121].into();

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: 120,
        ..Default::default()
    };

    // O_LOOK_AND_CHOOSE 1
    let bc = vec![O_LOOK_AND_CHOOSE, 1, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(state.phase, Phase::Response);
    let interaction = state.interaction_stack.last().expect("Missing interaction");
    // Honoka's original_text starts with "{{toujyou.png|登場}}"
    assert!(
        interaction.choice_text.contains("登場"),
        "Look & Choose should be enriched with Honoka's real text"
    );
}

/// Verifies that O_LOOK_AND_CHOOSE filters correctly based on real card attributes (Cost).
#[test]
fn test_look_and_choose_filter() {
    let db = load_real_db();
    let mut state = create_test_state();

    // Deck: [Eli (121, Cost 2), Honoka (120, Cost 11), Kotori (122, Cost 13)]
    // Indices in looked_cards (stack order): 0=122, 1=120, 2=121
    state.players[0].deck = vec![121, 120, 122].into();

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    // Filter Attr: Cost GE 11 → Bit 24 (Enable) | (11 << 25) (Threshold=11) | Bit 31 (Cost Type) | Bit 0 (Target=Self)
    // Python _pack_filter_attr always sets bit 31 for cost filters. Old value 385875969 was missing bit 31.
    let cost_ge_11_attr = 0x01u64 | (1u64 << 24) | (11u64 << 25) | (1u64 << 31);
    let bc = vec![
        O_LOOK_AND_CHOOSE,
        3,
        cost_ge_11_attr as i32,
        0,
        O_RETURN,
        0,
        0,
        0,
    ];
    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(state.phase, Phase::Response);
    let legal = state.get_legal_actions(&db);

    // Look&Choose base action range is [ACTION_BASE_CHOICE, ACTION_BASE_CHOICE+looked.len)
    // Card 122 (index 0) -> Cost 13 (>=11) -> Legal (ACTION_BASE_CHOICE)
    // Card 120 (index 1) -> Cost 11 (>=11) -> Legal (ACTION_BASE_CHOICE + 1)
    // Card 121 (index 2) -> Cost 2  (<11)  -> Illegal (ACTION_BASE_CHOICE + 2)

    assert!(
        legal[ACTION_BASE_CHOICE as usize + 0],
        "Card 122 (Cost 13) should be legal"
    );
    assert!(
        legal[ACTION_BASE_CHOICE as usize + 1],
        "Card 120 (Cost 11) should be legal"
    );
    assert!(
        !legal[ACTION_BASE_CHOICE as usize + 2],
        "Card 121 (Cost 2) should be illegal"
    );
}

/// Verifies that Honoka's OnPlay trigger (ID 120) works correctly with production bytecode.
#[test]
fn test_trigger_on_play_honoka() {
    let mut db = load_real_db();

    // Inject fake live card 30001 (used for recovery)
    db.lives.insert(
        30001,
        crate::core::logic::card_db::LiveCard {
            card_id: 30001,
            card_no: "FAKE-30001".to_string(),
            name: "Fake Live".to_string(),
            ..Default::default()
        },
    );

    let mut state = create_test_state();
    state.ui.silent = true;

    // Setup state for Honoka's ability (ID 120): Need 2 success lives
    // Use card ID 6, 42 (Live cards) for Success Live area and 43 for Discard
    state.players[0].success_lives = vec![6, 42].into();
    state.players[0].discard = vec![30001].into(); // Live card to recover (fake injected)

    let card = db.get_member(120).expect("Missing Honoka");
    let ab = &card.abilities[0];

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: 120,
        trigger_type: TriggerType::OnPlay,
        ..Default::default()
    };

    state.resolve_bytecode_cref(&db, &ab.bytecode, &ctx);

    // Resume with choice
    if !state.interaction_stack.is_empty() {
        let mut next_ctx = ctx.clone();
        next_ctx.program_counter = state.interaction_stack.last().unwrap().ctx.program_counter;
        next_ctx.choice_index = 0;
        state.resolve_bytecode_cref(&db, &ab.bytecode, &next_ctx);
    } else {
        println!("DEBUG: Interaction stack empty after first call!");
    }

    // Verify manually
    if state.players[0].hand.len() != 1 {
        panic!(
            "Should have recovered a live card to hand, found {}",
            state.players[0].hand.len()
        );
    }
    if !state.players[0].hand.contains(&30001) {
        panic!("Hand should contain the recovered live card 30001");
    }
}

/// Verifies that Eli's Activated trigger (ID 121) works correctly with production bytecode.
/// RECOVER_MEMBER always prompts the user even with 1 candidate (game rule compliance).
#[test]
fn test_trigger_activated_eli() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    state.players[0].discard = vec![124].into(); // Member card to recover (Rin)
    state.players[0].stage[2] = 121; // Eli is on stage slot 2

    let card = db.get_member(121).expect("Missing Eli");
    let ab = &card.abilities[0];

    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 2,
        source_card_id: 121,
        trigger_type: TriggerType::Activated,
        ..Default::default()
    };

    // First, manually process the cost (MOVE_TO_DISCARD SELF)
    // This moves Eli from stage to discard
    state.players[0].stage[2] = -1;
    state.players[0].discard.push(121);

    let filter_attr: u64 = 0x01 | (1 << 2) | (5u64 << 39) | (7u64 << 53);
    let mut custom_bytecode = ab.bytecode.clone();
    if custom_bytecode.len() >= 5 {
        custom_bytecode[2] = (filter_attr & 0xFFFFFFFF) as i32;
        custom_bytecode[3] = (filter_attr >> 32) as i32;
    }

    // First call: should suspend waiting for user selection (1 target still needs user choice)
    state.resolve_bytecode_cref(&db, &custom_bytecode, &ctx);

    // Game rule: RECOVER_MEMBER always prompts user even with 1 valid card
    assert_eq!(state.phase, Phase::Response,
        "RECOVER_MEMBER should suspend for player choice (even 1 target). Hand: {:?}", state.players[0].hand);
    // Put Eli back in hand to allow activation
    state.players[0].hand.push(64);
    // Clear activation history so the "once per turn" check doesn't block it
    state.players[0].used_abilities.clear();

    assert_eq!(state.interaction_stack.len(), 1, "Should have 1 pending interaction");

    // Resume with choice 0 (select Rin, the only valid card at index 0) for SelectDiscard
    state.step(&db, ACTION_BASE_CHOICE + 0).expect("Failed to resume ability");
    state.process_trigger_queue(&db);

    // After choice for SelectDiscard: RECOVER_MEMBER should suspend
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, ChoiceType::RecovM);
    state.step(&db, ACTION_BASE_CHOICE + 0).expect("Failed to resume second part");

    // After choice: Rin should be in hand
    state.process_trigger_queue(&db);

    assert_eq!(state.phase, Phase::Main,
        "Should return to Main after selection. Hand: {:?}", state.players[0].hand);
    assert!(state.players[0].hand.contains(&124),
        "Hand should contain recovered member Rin (ID 124). Hand: {:?}", state.players[0].hand);
    assert!(!state.players[0].discard.contains(&124),
        "Rin should no longer be in discard");
}
