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
    state.players[0].live_zone[0] = 454;
    state.players[0].set_revealed(0, false);

    // Start performance phase to trigger reveal
    state.phase = Phase::PerformanceP1;
    state.do_performance_phase(&db);

    assert!(
        state.players[0].is_revealed(0),
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
    state.players[0].stage[0] = 406;
    state.players[0].discard.push(121); // Target Eli to recover
    state.players[0].deck = vec![123].into(); // Dummy
    state.phase = Phase::Main;

    // 1. Activate ability (Slot 0, Ability 0)
    let result = state.step(
        &db,
        Action::ActivateAbility {
            slot_idx: 0,
            ab_idx: 0,
        }
        .id() as i32,
    );
    result.unwrap();


    assert_eq!(
        state.players[0].stage[0], -1,
        "Member should be in discard after sacrifice (Cost processing)"
    );
    // SETUP: Put Card 121 (a member) in discard
    state.players[0].discard = vec![121].into();
    state.players[0].hand.clear();

    // EXECUTE: Trigger RECOVER_MEMBER (Card 120 Honoka has it at ab_idx 0)
    let ctx = AbilityContext { player_id: 0, source_card_id: 120, ..Default::default() };
    state.resolve_bytecode_cref(&db, &db.get_member(120).unwrap().abilities[0].bytecode, &ctx);

    // RESOLVE: The interactions (MOVE_TO_DISCARD then RecovM)
    let mut safety_counter = 0;
    while state.phase == Phase::Response && safety_counter < 5 {
        println!("[TEST] Resolving suspension. Interaction: {:?}", state.interaction_stack.last().unwrap().choice_type);
        state.step(&db, ACTION_BASE_CHOICE + 0).expect("Step failed to resolve recovery");
        state.process_trigger_queue(&db);
        safety_counter += 1;
    }

    println!("[TEST] Hand after recovery: {:?}", state.players[0].hand);
    assert!(state.players[0].hand.contains(&121), "Hand should contain card 121. Hand: {:?}", state.players[0].hand);
}

#[test]
fn verify_performance_transition_history() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Use common live card ID 6
    state.players[0].live_zone[0] = 6;
    state.players[0].set_revealed(0, true);
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
    state.players[0].success_lives = smallvec![6, 6];
    state.players[0].score = 2; // Internal engine score (not display score)
    state.phase = Phase::LiveResult;
    state.players[0].live_zone[0] = 6;

    // Select the live card to win (Slot 0 maps to action 600)
    state.step(&db, 600).expect("Decision step failed");

    assert_eq!(state.phase, Phase::Terminal, "Game should end");
    assert_eq!(state.players[0].success_lives.len(), 3);
    assert_eq!(state.get_winner(), 0);
}

#[test]
fn verify_buff_logic() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = true;

    // Card ID 120: PL!-sd1- 001-SD
    // Ability: TRIGGER: CONSTANT -> ADD_BLADES(1, PER_CARD=SUCCESS_PILE)
    // Core Blades: 3 (Actual DB value)
    state.players[0].stage[0] = 120;
    state.players[0].success_lives = smallvec![120, 120]; // 2 cards in success pile

    // Total should be 3 (base) + 2 (from ability: 1 * success_pile_count) = 5
    let blades = state.get_effective_blades(0, 0, &db, 0);
    assert_eq!(
        blades, 5,
        "Card 120 should have 3 (base) + 1 * 2 (success pile count) = 5 blades"
    );
}
