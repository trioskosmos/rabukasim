use crate::core::logic::*;
use crate::test_helpers::{load_real_db, create_test_state};

/// Verifies that O_LOOK_AND_CHOOSE correctly enriches the choice text with the card's real original_text.
#[test]
fn test_enrichment_look_and_choose() {
    let db = load_real_db();
    let mut state = create_test_state();
    // Use Honoka (120) as the source of the enrichment text (revealing real cards in deck)
    state.core.players[0].deck = vec![121, 124, 121].into();

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: 120,
        ..Default::default()
    };

    // O_LOOK_AND_CHOOSE 1
    let bc = vec![O_LOOK_AND_CHOOSE, 1, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert_eq!(state.phase, Phase::Response);
    let interaction = state.interaction_stack.last().expect("Missing interaction");
    // Honoka's original_text starts with "{{toujyou.png|登場}}"
    assert!(interaction.choice_text.contains("登場"), "Look & Choose should be enriched with Honoka's real text");
}

/// Verifies that O_LOOK_AND_CHOOSE filters correctly based on real card attributes (Cost).
#[test]
fn test_look_and_choose_filter() {
    let db = load_real_db();
    let mut state = create_test_state();

    // Deck: [Eli (121, Cost 2), Honoka (120, Cost 11), Kotori (122, Cost 13)]
    // Indices in looked_cards (stack order): 0=122, 1=120, 2=121
    state.core.players[0].deck = vec![121, 120, 122].into();

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // Filter Attr: 385875969 (Enabled=1, Threshold=11, Mode=0/GE, DiscardBit=1)
    // GE 11 should match Honoka (11) and Kotori (13), but not Eli (2).
    let bc = vec![O_LOOK_AND_CHOOSE, 3, 385875969, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert_eq!(state.phase, Phase::Response);
    let legal = state.get_legal_actions(&db);

    // Look&Choose base action range is [8000, 8000+looked.len)
    // Card 122 (index 0) -> Cost 13 (>=11) -> Legal (8000)
    // Card 120 (index 1) -> Cost 11 (>=11) -> Legal (8001)
    // Card 121 (index 2) -> Cost 2  (<11)  -> Illegal (8002)

    assert!(legal[8000], "Card 122 (Cost 13) should be legal");
    assert!(legal[8001], "Card 120 (Cost 11) should be legal");
    assert!(!legal[8002], "Card 121 (Cost 2) should be illegal");
}

/// Verifies that Honoka's OnPlay trigger (ID 120) works correctly with production bytecode.
#[test]
fn test_trigger_on_play_honoka() {
    let mut db = load_real_db();

    // Inject fake live card 30001 (used for recovery)
    db.lives.insert(30001, crate::core::logic::card_db::LiveCard {
        card_id: 30001,
        card_no: "FAKE-30001".to_string(),
        name: "Fake Live".to_string(),
        ..Default::default()
    });

    let mut state = create_test_state();
    state.ui.silent = true;

    // Setup state for Honoka's ability (ID 120): Need 2 success lives
    // Use card ID 6, 42 (Live cards) for Success Live area and 43 for Discard
    state.core.players[0].success_lives = vec![6, 42].into();
    state.core.players[0].discard = vec![43].into(); // Live card to recover

    let card = db.get_member(120).expect("Missing Honoka");
    let ab = &card.abilities[0];

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: 120,
        trigger_type: TriggerType::OnPlay,
        ..Default::default()
    };

    state.resolve_bytecode(&db, &ab.bytecode, &ctx);

    // Resume with choice
    if !state.interaction_stack.is_empty() {
        let mut next_ctx = ctx.clone();
        next_ctx.program_counter = state.interaction_stack.last().unwrap().ctx.program_counter;
        next_ctx.choice_index = 0;
        state.resolve_bytecode(&db, &ab.bytecode, &next_ctx);
    } else {
        println!("DEBUG: Interaction stack empty after first call!");
    }

    // Verify manually
    if state.core.players[0].hand.len() != 1 {
        panic!("Should have recovered a live card to hand, found {}", state.core.players[0].hand.len());
    }
    if !state.core.players[0].hand.contains(&43) {
        panic!("Hand should contain the recovered live card 43");
    }
}

/// Verifies that Eli's Activated trigger (ID 121) works correctly with production bytecode.
#[test]
fn test_trigger_activated_eli() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    state.core.players[0].discard = vec![124].into(); // Member card to recover (Rin)
    state.core.players[0].stage[2] = 121; // Eli is on stage slot 2

    // Eli's Ability 0 Bytecode (from DB): [58, 0, 0, 4, 17, 1, 0, 6, 1, 0, 0, 0]
    // Instruction: Cost(MOVE_TO_DISCARD SELF), Effect(RECOVER_MEMBER 1)
    let card = db.get_member(121).expect("Missing Eli");
    let ab = &card.abilities[0];

    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 2,
        source_card_id: 121,
        trigger_type: TriggerType::Activated,
        ..Default::default()
    };

    state.resolve_bytecode(&db, &ab.bytecode, &ctx);

    // Manual checks: Eli should have been discarded as cost immediately
    if state.core.players[0].stage[2] != -1 {
        panic!("Eli should have been discarded as cost (Stage[2] still {})", state.core.players[0].stage[2]);
    }
    if !state.core.players[0].discard.contains(&121) {
        panic!("Discard should contain Eli (ID 121)");
    }

    // Since RECOVER_MEMBER is interactive, state should now be suspended
    if state.phase != Phase::Response {
        panic!("State should be in Phase::Response for recovery choice, found {:?}", state.phase);
    }

    // Simulate choosing the first card in the recovery list (the only one, ID 124)
    let mut pending = state.interaction_stack.pop().expect("No pending interaction");
    pending.ctx.choice_index = 0; // Choose first option (ID 124)
    let card = db.get_member(121).expect("Missing Eli for resume");
    state.resolve_bytecode(&db, &card.abilities[0].bytecode, &pending.ctx);

    // Now verify the hand
    if !state.core.players[0].hand.contains(&124) {
        panic!("Hand should contain the recovered member Rin (ID 124). Hand: {:?}", state.core.players[0].hand);
    }
}
