use crate::test_helpers::{create_test_db, create_test_state};
use crate::core::logic::*;
use crate::core::hearts::HeartBoard;
// use std::collections::HashMap;



/// O_RECOVER_LIVE must only show Live cards, never members.
#[test]
fn test_recov_l_only_shows_lives() {
    let db = create_test_db();
    let mut state = create_test_state();

    state.core.players[0].discard.push(19);    // Member
    state.core.players[0].discard.push(55001); // Live (exists in create_test_db)

    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    let bc = vec![O_RECOVER_LIVE, 1, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert_eq!(state.core.players[0].looked_cards.len(), 1);
    assert_eq!(state.core.players[0].looked_cards[0], 55001);
}

/// O_RECOVER_LIVE returns early when no live cards are in discard.
#[test]
fn test_recov_l_no_lives_returns_early() {
    let db = create_test_db();
    let mut state = create_test_state();

    state.core.players[0].discard.push(19); // Only members

    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    let bc = vec![O_RECOVER_LIVE, 1, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert!(state.core.players[0].looked_cards.is_empty());
    assert_ne!(state.phase, Phase::Response);
}

/// O_PAY_ENERGY auto-pays when sufficient energy is available.
#[test]
fn test_pay_energy_auto_pays() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    state.core.players[0].tapped_energy_mask = 0;

    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    let bc = vec![O_PAY_ENERGY, 2, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bc, &ctx);

    assert_ne!(state.phase, Phase::Response);
    assert_eq!(state.core.players[0].tapped_energy_mask.count_ones(), 2);
}

/// Deck refresh safety cap prevents >60 cards.
#[test]
fn test_deck_refresh_caps_at_60() {
    let mut state = create_test_state();
    state.ui.silent = true;

    // Stuff 65 cards into discard (simulating a bug elsewhere)
    for i in 0..65i32 {
        state.core.players[0].discard.push(i);
    }

    state.resolve_deck_refresh(0);

    assert!(state.core.players[0].deck.len() <= 60);
    assert!(state.core.players[0].discard.is_empty());
}

#[test]
fn test_poppin_up_success_repro() {
    let mut db = CardDatabase::default();
    
    // Insert Poppin' Up! with correct requirements
    // Need: [9, 0, 1, 0, 0, 0, 2]
    // Use a small card_id instead of 30047 to avoid HashMap overhead in test
    // and Ensure lives_vec is large enough if we want to use it
    let card_id: i32 = 30047;
    db.lives.insert(card_id, LiveCard {
        card_id,
        card_no: "PL!N-bp1-026-L".to_string(),
        name: "Poppin' Up!".to_string(),
        score: 1,
        required_hearts: [9, 0, 1, 0, 0, 0, 2],
        ..Default::default()
    });

    // Add a dummy member so we can possess hearts on stage
    db.members.insert(19, MemberCard {
        card_id: 19,
        ..Default::default()
    });

    let mut state = create_test_state();
    state.ui.silent = false;
    state.phase = Phase::LiveResult;
    
    // Set dummy member on stage
    state.core.players[0].stage[0] = 10;
    
    // Set Poppin' Up! in P0's live zone
    state.core.players[0].live_zone[0] = card_id;
    
    // Mock player hearts: Available: [10, 2, 1, 0, 1, 1, 1]
    state.core.players[0].heart_buffs[0] = HeartBoard::from_array(&[10, 2, 1, 0, 1, 1, 1]);

    // Give P1 a card too, but with 0 score or no success to avoid tie for now
    state.core.players[1].live_zone[0] = -1;

    let hearts = state.get_total_hearts(0, &db, 0);
    let req = HeartBoard::from_array(&[9, 0, 1, 0, 0, 0, 2]);
    println!("DEBUG: P0 Hearts: {:?}", hearts.to_array());
    println!("DEBUG: Req: {:?}", req.to_array());
    println!("DEBUG: Satisfies? {}", hearts.satisfies(req));

    state.do_live_result(&db);

    // Expect card to move to success_lives
    for msg in &state.ui.rule_log { println!("LOG: {}", msg); }
    assert!(hearts.satisfies(req), "Hearts should satisfy requirement");
    assert_eq!(state.core.players[0].success_lives.len(), 1, "Poppin' Up! should have succeeded hearts");
    assert_eq!(state.core.players[0].success_lives[0], card_id);
    assert_eq!(state.core.players[0].live_zone[0], -1, "Card should be removed from live_zone");
}
