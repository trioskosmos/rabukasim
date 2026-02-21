use crate::core::logic::*;
// use crate::core::logic::card_db::LOGIC_ID_MASK;

#[test]
fn test_rule_8_3_16_all_or_nothing_failure() {
    let mut db = CardDatabase::default();
    
    // Card 0: Impossible (needs 100 Red hearts)
    let mut impossible_live = LiveCard::default();
    impossible_live.card_id = 0;
    impossible_live.hearts_board.set_color_count(1, 100);
    db.lives.insert(0, impossible_live.clone());
    db.lives_vec[0 as usize] = Some(impossible_live);
    
    // Card 1: Easy (needs 0 hearts)
    let mut easy_live = LiveCard::default();
    easy_live.card_id = 1;
    db.lives.insert(1, easy_live.clone());
    db.lives_vec[1 as usize] = Some(easy_live);

    let mut state = GameState::default();
    state.phase = Phase::LiveResult;
    
    // P0 sets both: 0 (impossible) and 1 (easy)
    state.core.players[0].live_zone[0] = 0;
    state.core.players[0].live_zone[1] = 1;

    // Run judgement
    state.do_live_result(&db);

    // Rule 8.3.16: Since one failed, both should be discarded
    assert_eq!(state.core.players[0].live_zone[0], -1);
    assert_eq!(state.core.players[0].live_zone[1], -1);
    assert_eq!(state.core.players[0].success_lives.len(), 0);
    assert!(state.core.players[0].discard.contains(&0));
    assert!(state.core.players[0].discard.contains(&1));
}

#[test]
fn test_rule_8_4_13_first_player_change() {
    let mut state = GameState::default();
    state.first_player = 0;
    state.current_player = 0;
    state.phase = Phase::LiveResult;
    
    // Only P1 gets a success live
    state.obtained_success_live = [false, true];
    
    // Finalize
    state.finalize_live_result();
    
    // Rule 8.4.13: P1 becomes first player
    assert_eq!(state.first_player, 1);
    assert_eq!(state.current_player, 1);
}

#[test]
fn test_rule_8_4_13_first_player_no_change_both_success() {
    let mut state = GameState::default();
    state.first_player = 0;
    state.current_player = 0;
    state.phase = Phase::LiveResult;
    
    // Both get success lives
    state.obtained_success_live = [true, true];
    
    // Finalize
    state.finalize_live_result();
    
    // Rule 8.4.13: Turn order unchanged
    assert_eq!(state.first_player, 0);
}
