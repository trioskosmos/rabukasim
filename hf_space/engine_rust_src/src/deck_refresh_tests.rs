use crate::core::logic::*;
use crate::test_helpers::{create_test_state, load_real_db};

#[test]
fn test_refresh_on_empty_draw() {
    let mut state = create_test_state();
    state.players[0].deck = vec![].into();
    state.players[0].discard = vec![121, 124, 122].into(); // Real IDs

    let _db = load_real_db();

    // Drawing 1 card should trigger refresh
    state.draw_cards(0, 1);

    assert_eq!(state.players[0].hand.len(), 1);
    assert_eq!(state.players[0].deck.len(), 2);
    assert!(state.players[0].discard.is_empty());
    assert!(state.players[0].get_flag(PlayerState::FLAG_DECK_REFRESHED));
}

#[test]
fn test_refresh_on_look_at_top_x() {
    let mut state = create_test_state();
    state.players[0].deck = vec![120].into(); // Only 1 card in deck
    state.players[0].discard = vec![121, 124, 122].into();

    let db = load_real_db();

    let ctx = AbilityContext {
        player_id: 0,
        ..AbilityContext::default()
    };

    // O_LOOK_DECK, Value 3 (Look at top 3)
    // Rule 10.2.2.2: Refresh because deck (1) < needed (3)
    let bytecode = vec![O_LOOK_DECK, 3, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // After refresh, deck should have 1 (original) + 3 (refreshed) = 4 cards.
    // However, LOOK_DECK pops 3 cards from the deck.
    // So remaining deck should be 4 - 3 = 1 card.
    assert_eq!(state.players[0].deck.len(), 1);
    assert_eq!(state.players[0].discard.len(), 0);
    assert!(state.players[0].get_flag(PlayerState::FLAG_DECK_REFRESHED));

    // Looked cards should contain 3 cards (top of deck)
    assert_eq!(state.players[0].looked_cards.len(), 3);
    // Original card (120) MUST be one of them (the top one)
    assert_eq!(state.players[0].looked_cards[0], 120);
}

#[test]
fn test_refresh_order_preservation() {
    let mut state = create_test_state();
    state.players[0].deck = vec![121, 120].into(); // 120 is on top
    state.players[0].discard = vec![124, 122, 137].into();

    // Force refresh
    state.resolve_deck_refresh(0);

    // Rule 10.2.3: Existing cards (121, 120) stay on top
    // pop() should get 120, then 121.
    assert_eq!(state.players[0].deck.pop(), Some(120));
    assert_eq!(state.players[0].deck.pop(), Some(121));

    // Refreshed cards are at the bottom. Discard had 3, so total 5. After 2 pops, 3 left.
    assert_eq!(state.players[0].deck.len(), 3);
}

#[test]
fn test_refresh_on_look_and_choose() {
    let mut state = create_test_state();
    state.players[0].deck = vec![120].into(); // Only 1 card (Honoka)
    state.players[0].discard = vec![121, 124, 122].into();

    let db = load_real_db();

    let ctx = AbilityContext {
        player_id: 0,
        choice_index: 0, // Pick the top card
        ..AbilityContext::default()
    };

    // O_LOOK_AND_CHOOSE, Value 3, Attr 30 (Hand destination), Target 0 (Deck source)
    // Rule 10.2.2.2: Refresh because deck (1) < needed (3)
    let bytecode = vec![O_LOOK_AND_CHOOSE, 259, 0, 6, O_RETURN, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // After refresh, deck should have 1 + 3 = 4 cards.
    // Pop 3: 120, ?, ? -> These go to looked_cards.
    // Deck now has 1 card left: [?]
    // Choice 0: 120 goes to hand.
    // Rest [?, ?] go BACK to deck (since Attr doesn't say discard).
    // Final deck: [?, ?, ?] (length 3?)
    // Wait, resolution logic:
    // Looked cards: [120, ?, ?]
    // picked: 120
    // rest: [?, ?]
    // back to deck: [?, ?]
    // deck was [?]
    // new deck: [?, ?, ?]

    // assert_eq!(state.players[0].hand.len(), 1);
    assert_eq!(state.players[0].hand.last(), Some(&120));
    assert_eq!(state.players[0].deck.len(), 3);
}
