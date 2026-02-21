use crate::core::logic::*;
use crate::test_helpers::{Action, load_real_db};

#[test]
fn test_energy_initialization() {
    let mut state = GameState::default();
    let _db = load_real_db();
    
    // Rule 6.1.1.1: Main Deck contains 60 cards
    // 121 = Eli (Member), 137 = START:DASH!! (Live)
    // 0 = Energy Card
    state.initialize_game_with_seed(
        vec![121i32; 60], // P0 main
        vec![121i32; 60], // P1 main
        vec![0i32; 12],   // P0 energy
        vec![0i32; 12],   // P1 energy
        Vec::new(), Vec::new(),
        Some(12345)
    );

    // Rule 6.2.1.7: Starts with 3 energy in zone, 9 left in deck (total 12)
    assert_eq!(state.core.players[0].energy_zone.len(), 3, "P0 should start with 3 energy");
    assert_eq!(state.core.players[1].energy_zone.len(), 3, "P1 should start with 3 energy");
    assert_eq!(state.core.players[0].energy_deck.len(), 9, "P0 should have 9 energy left in deck");
}

#[test]
fn test_phase_auto_advance_from_mulligan() {
    let mut state = GameState::default();
    let db = load_real_db();
    
    // Setup for reproducible test (seed 1)
    state.initialize_game_with_seed(
        vec![121i32; 60], vec![121i32; 60],
        vec![0i32; 12], vec![0i32; 12],
        Vec::new(), Vec::new(),
        Some(1)
    );

    // Sequence: Rps -> TurnChoice -> MulliganP1 -> MulliganP2 -> Active -> Energy -> Draw -> Main
    
    // 1. Rps
    state.step(&db, Action::Rps { player_idx: 0, choice: 0 }.id() as i32).unwrap(); // P0 choice: Rock
    state.step(&db, Action::Rps { player_idx: 1, choice: 2 }.id() as i32).unwrap(); // P1 choice: Scissors
    assert_eq!(state.phase, Phase::TurnChoice);

    // 2. TurnChoice
    state.step(&db, Action::ChooseTurnOrder { first: true }.id() as i32).unwrap(); // P0 chooses first
    assert_eq!(state.phase, Phase::MulliganP1);
    assert_eq!(state.current_player, 0);

    // 3. Mulligan P1
    state.step(&db, Action::Pass.id() as i32).unwrap();
    assert_eq!(state.phase, Phase::MulliganP2);
    assert_eq!(state.current_player, 1);

    // 4. Mulligan P2
    // After this, it should go to Active -> Energy -> Draw -> Main automatically!
    state.step(&db, Action::Pass.id() as i32).unwrap();
    
    assert_eq!(state.phase, Phase::Main, "Should have auto-advanced to Main phase");
    // P0 is first player, so P0's turn 1 starts.
    assert_eq!(state.current_player, 0, "P0 should be active player");
    assert_eq!(state.core.players[0].energy_zone.len(), 4, "Should have charged 1 energy (3+1=4)");
    assert_eq!(state.core.players[0].hand.len(), 7, "Should have drawn 1 card (6+1=7)");
}

#[test]
fn test_yell_source_deck_parity() {
    let mut state = GameState::default();
    let db = load_real_db();
    
    // 121 = Eli (1 Blade)
    // 137 = START:DASH!!
    state.core.players[0].hand = smallvec::smallvec![121, 121, 121]; // 3 cards in hand
    state.core.players[0].deck = smallvec::smallvec![121, 121, 121, 121, 121]; // 5 cards in deck
    state.core.players[0].stage[0] = 121; // Blade 1
    state.core.players[0].stage[1] = 121; // Blade 2
    state.core.players[0].stage[2] = 121; // Blade 3
    state.core.players[0].live_zone[0] = 137;
    state.current_player = 0;
    state.phase = Phase::PerformanceP1;

    // do_performance_phase should yell (count based on blades count, NOT hand size)
    // Eli has 1 blade. 3 Eli = 3 blades.
    state.do_performance_phase(&db);

    assert_eq!(state.core.players[0].hand.len(), 3, "Hand should NOT be consumed by Yell");
    assert_eq!(state.core.players[0].deck.len(), 2, "Deck should have lost 3 cards (blades=3) to Yell");
}
