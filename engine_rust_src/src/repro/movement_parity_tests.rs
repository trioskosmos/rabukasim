use crate::core::logic::*;

#[test]
fn test_move_to_discard_from_deck_mill() {
    let mut db = CardDatabase::default();
    db.members.insert(101, MemberCard::default());
    db.members.insert(102, MemberCard::default());
    db.members.insert(103, MemberCard::default());
    db.members.insert(104, MemberCard::default());
    db.members.insert(105, MemberCard::default());
    let mut state = GameState::default();

    // Setup: 5 cards in deck
    state.core.players[0].deck = vec![101, 102, 103, 104, 105].into();
    state.core.players[0].discard = vec![].into();

    // Bytecode: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}
    // v=3, a=1 (implies t=8 via interpreter logic), s=1 (but t is derived from a=1 usually? lets check logic)
    // In interpreter.rs:
    // let t = if s == 6 ... else if a >= 1 && a <= 4 { match a { 1 => 8 ... } }
    // So a=1 maps to t=8 (Deck).
    let bc = vec![O_MOVE_TO_DISCARD, 3, 1, 0, O_RETURN, 0, 0, 0];

    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };

    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(state.core.players[0].deck.len(), 2, "Should have 2 cards left in deck");
    assert_eq!(state.core.players[0].discard.len(), 3, "Should have 3 cards in discard");
    // Verify specific cards moved (popped from end of vector)
    assert!(state.core.players[0].discard.contains(&105));
    assert!(state.core.players[0].discard.contains(&104));
    assert!(state.core.players[0].discard.contains(&103));
}

#[test]
fn test_move_to_deck_from_stage() {
    let mut db = CardDatabase::default();
    db.members.insert(101, MemberCard::default());
    db.members.insert(102, MemberCard::default());
    db.members.insert(103, MemberCard::default());
    db.members.insert(104, MemberCard::default());
    db.members.insert(105, MemberCard::default());
    let mut state = GameState::default();

    // Setup: Card on stage slot 0
    state.core.players[0].stage[0] = 101;
    state.core.players[0].deck = vec![].into();

    // Bytecode: MOVE_TO_DECK(1) {FROM="STAGE", SLOT=0}
    // a=4 (Stage), area_idx=0
    let bc = vec![O_MOVE_TO_DECK, 1, 4, 0, O_RETURN, 0, 0, 0];

    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0, // Slot 0
        ..Default::default()
    };

    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(state.core.players[0].stage[0], -1, "Stage slot 0 should be empty");
    assert_eq!(state.core.players[0].deck.len(), 1, "Deck should have 1 card");
    assert_eq!(state.core.players[0].deck[0], 101, "Deck should contain the card");
}

#[test]
fn test_search_deck_to_stage() {
    let mut db = CardDatabase::default();
    db.members.insert(101, MemberCard::default());
    db.members.insert(102, MemberCard::default());
    db.members.insert(103, MemberCard::default());
    db.members.insert(104, MemberCard::default());
    db.members.insert(105, MemberCard::default());
    let mut state = GameState::default();

    // Setup: Card in deck at index 0
    state.core.players[0].deck = vec![101].into();
    state.core.players[0].stage[0] = -1;

    // Bytecode: SEARCH_DECK(1) {TO="STAGE", SLOT=0}
    // s=4 (Stage), a=0 (Slot 0), target_slot=0 (Index in deck)
    let bc = vec![O_SEARCH_DECK, 1, 0, 4, O_RETURN, 0, 0, 0];

    let ctx = AbilityContext {
        player_id: 0,
        target_slot: 0, // Deck index to remove
        ..Default::default()
    };

    state.resolve_bytecode_cref(&db, &bc, &ctx);

    assert_eq!(state.core.players[0].stage[0], 101, "Stage slot 0 should have card 101");
    assert!(state.core.players[0].deck.is_empty(), "Deck should be empty");
}

#[test]
fn test_look_and_choose_to_stage() {
    let mut db = CardDatabase::default();
    db.members.insert(101, MemberCard::default());
    db.members.insert(102, MemberCard::default());
    db.members.insert(103, MemberCard::default());
    db.members.insert(104, MemberCard::default());
    db.members.insert(105, MemberCard::default());
    let mut state = GameState::default();

    // Setup: Card in looked_cards
    state.core.players[0].looked_cards = vec![101, 102].into();
    state.core.players[0].stage[0] = -1;
    state.core.players[0].deck = vec![].into(); // Deck empty to ensure no refill issues

    // Bytecode: LOOK_AND_CHOOSE(1) {TO="STAGE", SLOT=0}
    // s=0 (Slot 0), a=4 (Stage)
    // Destination determination logic: if a == 4 { 4 }
    // Inside destination 4 branch: slot = s as usize = 0
    let bc = vec![O_LOOK_AND_CHOOSE, 1, 4, 0, O_RETURN, 0, 0, 0];

    let ctx = AbilityContext {
        player_id: 0,
        choice_index: 0, // Choose first card (101)
        ..Default::default()
    };

    state.resolve_bytecode_cref(&db, &bc, &ctx);

    // Assertions
    // Remainder should go back to Discard for source=Deck (7 | _)
    assert!(state.core.players[0].discard.contains(&102), "Unchosen card should be in discard");
    assert_eq!(state.core.players[0].looked_cards.len(), 0, "Looked cards should be cleared");
    assert_eq!(state.core.players[0].stage[0], 101, "Stage slot 0 should have card 101");
}
