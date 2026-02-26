use crate::core::logic::*;
use crate::test_helpers::{load_real_db, Action};
use crate::core::enums::Phase;
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
    
    assert!(state.core.players[0].is_revealed(0), "Live card should be revealed during performance phase");
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
    state.step(&db, Action::ActivateAbility { slot_idx: 0, ab_idx: 0 }.id() as i32).unwrap();
    
    assert_eq!(state.core.players[0].stage[0], -1, "Member should be in discard after sacrifice");
    assert!(state.core.players[0].discard.contains(&406));
    
    // 2. Resolve Recovery
    // Choice interaction: Pick the member to recover (121)
    assert_eq!(state.phase, Phase::Response);
    state.step(&db, Action::SelectChoice { choice_idx: 0 }.id() as i32).unwrap();
    
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
    
    assert_eq!(state.ui.performance_history.len(), 2, "Should have 2 performance records");
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
    let mut db = load_real_db();
    let mut mock_member = db.get_member(8360).unwrap().clone();
    mock_member.card_id = 9999;
    mock_member.blades = 3;
    // Clear conditions and use unconditional O_ADD_BLADES (11) targeting context area (4)
    mock_member.abilities[0].conditions.clear();
    mock_member.abilities[0].bytecode = vec![11, 1, 0, 0, 4, 1, 0, 0, 0, 0];
    db.members.insert(9999, mock_member);

    let mut state = GameState::default();
    state.ui.silent = true;
    
    // ID 9999: Mock Buffer (Buffer: Constant +1 Blade to Self using Opcode 11 (O_ADD_BLADES) Targeting 4)
    // Base Blades: 3. Total should be 4.
    state.core.players[0].stage[0] = 9999; 
    
    let blades = state.get_effective_blades(0, 0, &db, 0);
    assert_eq!(blades, 4, "9999 should have 3+1 blades");
}

