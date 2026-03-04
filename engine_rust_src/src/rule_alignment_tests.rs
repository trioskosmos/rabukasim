use crate::core::logic::*;
use serde_json::json;

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
    state.players[0].live_zone[0] = 0;
    state.players[0].live_zone[1] = 1;

    // Run judgement
    state.do_live_result(&db);

    // Rule 8.3.16: Since one failed, both should be discarded
    assert_eq!(state.players[0].live_zone[0], -1);
    assert_eq!(state.players[0].live_zone[1], -1);
    assert_eq!(state.players[0].success_lives.len(), 0);
    assert!(state.players[0].discard.contains(&0));
    assert!(state.players[0].discard.contains(&1));
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

#[test]
fn test_priority_p1_triggers_first() {
    let mut db = CardDatabase::default();
    db.members_vec.resize(1000, None);

    // Member with OnLiveSuccess: +100 Score
    let mut m1 = MemberCard::default();
    m1.card_id = 101;
    m1.name = "P0 Member".to_string();
    m1.abilities.push(Ability {
        trigger: TriggerType::OnLiveSuccess,
        bytecode: vec![O_BOOST_SCORE, 100, 0, 0, 0, O_RETURN, 0, 0, 0, 0],
        ..Default::default()
    });
    db.members.insert(101, m1.clone());
    db.members_vec[101 as usize] = Some(m1);

    // Member with OnLiveSuccess: +200 Score
    let mut m2 = MemberCard::default();
    m2.card_id = 102;
    m2.name = "P1 Member".to_string();
    m2.abilities.push(Ability {
        trigger: TriggerType::OnLiveSuccess,
        bytecode: vec![O_BOOST_SCORE, 200, 0, 0, 0, O_RETURN, 0, 0, 0, 0],
        ..Default::default()
    });
    db.members.insert(102, m2.clone());
    db.members_vec[102 as usize] = Some(m2);

    let mut state = GameState::default();
    state.first_player = 1; // P1 IS FIRST PLAYER
    state.phase = Phase::LiveResult;

    // P0 has m1 on stage
    state.players[0].stage[0] = 101;
    // P1 has m2 on stage
    state.players[1].stage[0] = 102;

    // Both had successful lives (snapshot)
    state
        .ui
        .performance_results
        .insert(0, json!({"success": true}));
    state
        .ui
        .performance_results
        .insert(1, json!({"success": true}));

    // Run judgement
    state.do_live_result(&db);

    // Verify order in rule_log
    // Order should be P1 trigger (Score +200) then P0 trigger (Score +100)
    let logs: Vec<String> = state
        .ui
        .rule_log
        .as_ref()
        .unwrap()
        .iter()
        .filter(|s| s.contains("Score +"))
        .cloned()
        .collect();

    assert_eq!(logs.len(), 2);
    assert!(
        logs[0].contains("Score +200"),
        "P1 (First Player) should trigger first. Logs: {:?}",
        logs
    );
    assert!(
        logs[1].contains("Score +100"),
        "P0 should trigger second. Logs: {:?}",
        logs
    );
}

#[test]
fn test_priority_p1_choice_selection() {
    let mut db = CardDatabase::default();
    db.lives_vec.resize(1000, None);

    // Setup lives
    let mut l1 = LiveCard::default();
    l1.card_id = 1;
    l1.name = "L1".to_string();
    db.lives.insert(1, l1.clone());
    db.lives_vec[1] = Some(l1);
    let mut l2 = LiveCard::default();
    l2.card_id = 2;
    l2.name = "L2".to_string();
    db.lives.insert(2, l2.clone());
    db.lives_vec[2] = Some(l2);

    let mut state = GameState::default();
    state.first_player = 1; // P1 IS FIRST PLAYER
    state.phase = Phase::LiveResult;

    // Both players have 2 candidates (multiple candidates = choice needed)
    state.players[0].live_zone[0] = 1;
    state.players[0].live_zone[1] = 2;
    state.players[1].live_zone[0] = 1;
    state.players[1].live_zone[1] = 2;

    // Snapshot: both succeeded
    state.ui.performance_results.insert(
        0,
        json!({
            "success": true,
            "lives": [{"passed": true, "score": 10}, {"passed": true, "score": 10}]
        }),
    );
    state.ui.performance_results.insert(
        1,
        json!({
            "success": true,
            "lives": [{"passed": true, "score": 10}, {"passed": true, "score": 10}]
        }),
    );

    // Skip OnLiveSuccess triggers to reach choice logic
    state.live_result_processed_mask = [0x80, 0x80];

    state.do_live_result(&db);

    // P1 (First Player) should be current_player for choice
    assert_eq!(
        state.current_player, 1,
        "P1 should be selected for choice first when P1 is first_player"
    );
    assert!(state.live_result_selection_pending);
}
