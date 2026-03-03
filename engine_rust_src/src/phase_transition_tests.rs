use crate::core::logic::*;
use crate::test_helpers::{create_test_state, load_real_db};

#[test]
fn test_phase_flow_mulligan_to_main() {
    let _db = load_real_db();
    let mut state = create_test_state();

    // Setup Mulligan Phase
    state.phase = Phase::MulliganP1;
    // ensure deck has cards to draw if mulligan needs them
    state.core.players[0].deck = vec![121, 124, 137, 121, 124, 137].into();
    state.core.players[0].hand = vec![19, 137, 121, 124, 137, 121].into();
    state.first_player = 0;
    state.current_player = 0;

    // Simulate Player 0 confirming mulligan (Keep all = discard empty list)
    state.execute_mulligan(0, vec![]);

    // Should transition to P2 Mulligan
    assert_eq!(state.phase, Phase::MulliganP2);
    assert_eq!(state.current_player, 1);

    // Simulate Player 1 confirming mulligan
    state.core.players[1].deck = vec![121, 124, 137].into();
    state.execute_mulligan(1, vec![]);

    // Should transition to Active Phase (Game Start)
    assert_eq!(state.phase, Phase::Active);
    assert_eq!(state.current_player, 0); // Back to first player
}

#[test]
fn test_phase_flow_main_to_next_turn() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.first_player = 0;
    state.current_player = 0;
    state.phase = Phase::Main;
    state.turn = 1;

    // P1 Ends Main Phase -> Should go to P2 Active
    state.end_main_phase(&db);

    assert_eq!(state.phase, Phase::Active);
    assert_eq!(state.current_player, 1);

    // P2 Ends Main Phase -> Should go to LiveSet (Round End)
    state.end_main_phase(&db);

    assert_eq!(state.phase, Phase::LiveSet);
    assert_eq!(state.current_player, 0);
}

#[test]
fn test_phase_flow_active_to_main() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.phase = Phase::Active;
    state.current_player = 0;
    state.core.players[0].energy_deck = vec![137, 121, 124].into();
    state.core.players[0].deck = vec![19, 137].into();

    // auto_step should drive: Active -> Energy -> Draw -> Main
    state.auto_step(&db);

    // Check if we reached Main
    assert_eq!(state.phase, Phase::Main);

    // Check side effects were applied
    // Energy phase: +1 energy (10 base + 1 new = 11)
    assert_eq!(state.core.players[0].energy_zone.len(), 4);
    // Draw phase: +1 card (Hand was 0, now 1)
    assert_eq!(state.core.players[0].hand.len(), 1);
}
