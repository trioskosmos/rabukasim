use crate::core::enums::Phase;
use crate::core::logic::*;
use crate::test_helpers::{load_real_db, Action};
use smallvec::smallvec;

#[test]
fn verify_on_reveal_trigger() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Card ID 454: ダイスキだったらダイジョウブ！ (Live)
    // Ability: ON_REVEAL -> MOVE_TO_DISCARD etc.
    state.core.players[0].live_zone[0] = 454;
    state.core.players[0].set_revealed(0, false);

    // Start performance phase to trigger reveal
    state.phase = Phase::PerformanceP1;
    state.do_performance_phase(&db);

    assert!(
        state.core.players[0].is_revealed(0),
        "Live card should be revealed during performance phase"
    );
    // Trigger should have executed (it meets conditions if yelled revealed is empty)
}

#[test]
fn verify_manual_recovery_pattern() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Card ID 406: 高海千歌 (Member)
    // Ability: ACTIVATED -> COST: MOVE_TO_DISCARD -> EFFECT: RECOVER_MEMBER(1)
    state.core.players[0].stage[0] = 406;
    state.core.players[0].discard = vec![121].into(); // Target Eli to recover
    state.core.players[0].deck = vec![123].into(); // Dummy
    state.phase = Phase::Main;

    // 1. Activate ability (Slot 0, Ability 0)
    state
        .step(
            &db,
            Action::ActivateAbility {
                slot_idx: 0,
                ab_idx: 0,
            }
            .id() as i32,
        )
        .unwrap();

    assert_eq!(
        state.core.players[0].stage[0], -1,
        "Member should be in discard after sacrifice"
    );
    assert!(state.core.players[0].discard.contains(&406));

    // 2. Resolve Recovery
    // Choice interaction: Pick the member to recover (121)
    assert_eq!(state.phase, Phase::Response);
    state
        .step(&db, Action::SelectChoice { choice_idx: 0 }.id() as i32)
        .unwrap();

    assert_eq!(state.core.players[0].hand.len(), 1);
    assert!(state.core.players[0].hand.contains(&121));
}

#[test]
fn verify_performance_transition_history() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Use common live card ID 6
    state.core.players[0].live_zone[0] = 6;
    state.core.players[0].set_revealed(0, true);
    state.phase = Phase::PerformanceP1;

    // P0 Perform (Pass)
    state.step(&db, 0).expect("P0 pass failed");
    // P1 Perform (Pass)
    state.step(&db, 0).expect("P1 pass failed");

    assert_eq!(
        state.ui.performance_history.len(),
        2,
        "Should have 2 performance records"
    );
}

#[test]
fn verify_full_win_condition() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // ID 6: Score 3 card
    state.core.players[0].success_lives = smallvec![6, 6];
    state.core.players[0].score = 2; // Internal engine score (not display score)
    state.phase = Phase::LiveResult;
    state.core.players[0].live_zone[0] = 6;

    // Select the live card to win (Slot 0 maps to action 600)
    state.step(&db, 600).expect("Decision step failed");

    assert_eq!(state.phase, Phase::Terminal, "Game should end");
    assert_eq!(state.core.players[0].success_lives.len(), 3);
    assert_eq!(state.get_winner(), 0);
}

#[test]
fn verify_buff_logic() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Card ID 120: PL!-sd1-001-SD
    // Ability: TRIGGER: CONSTANT -> ADD_BLADES(1, PER_CARD=SUCCESS_PILE)
    // Core Blades: 2
    state.core.players[0].stage[0] = 120;
    state.core.players[0].success_lives = smallvec![6, 7]; // 2 cards in success pile

    // Total should be 2 (base) + 2 (from ability) = 4
    let blades = state.get_effective_blades(0, 0, &db, 0);
    assert_eq!(
        blades, 4,
        "Card 120 should have 2 (base) + 2 (bonus) = 4 blades"
    );
}
