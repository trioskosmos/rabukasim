use crate::core::logic::*;
use crate::test_helpers::{create_test_state, load_real_db};

#[test]
fn test_mulligan_logic_discard_and_draw() {
    let _db = load_real_db();
    let mut state = create_test_state();

    // Initialize deck and hand with real IDs
    // Eli (121), Rin (124), Kotori (122), Honoka (120)
    state.players[0].hand = vec![121, 124, 121, 124, 121, 124].into();
    state.players[0].deck = vec![120, 120, 120, 120, 120, 120].into(); // 6 cards in deck
    state.phase = Phase::MulliganP1;
    state.current_player = 0;
    state.first_player = 0;

    // Discard index 0, 1, 2 (Three cards)
    state.execute_mulligan(0, vec![0, 1, 2]);

    assert_eq!(state.players[0].hand.len(), 6);
    // Total cards for player 0 was 12. 6 in hand, 6 in deck.
    // After mulligan 3, deck should still have 6 cards total (some swapped).
    assert_eq!(state.players[0].deck.len(), 6);
}

#[test]
fn test_mulligan_empty_keep() {
    let _db = load_real_db();
    let mut state = create_test_state();

    state.players[0].hand = vec![121, 121, 121, 121, 121, 121].into();
    state.players[0].deck = vec![120].into();
    state.phase = Phase::MulliganP1;

    // Keep all
    state.execute_mulligan(0, vec![]);

    assert_eq!(state.players[0].hand.len(), 6);
    assert_eq!(state.players[0].hand[0], 121);
    assert_eq!(state.players[0].deck.len(), 1);
}
