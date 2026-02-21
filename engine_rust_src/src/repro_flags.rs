#![allow(unused_imports)]
use crate::core::logic::*;
use crate::core::logic::card_db::LOGIC_ID_MASK;

// Types like ConditionType, MemberCard, LiveCard, PlayerState are all re-exported in logic.rs

#[test]
fn test_enforce_cannot_live() {
    let mut db = CardDatabase::default();
    // Create a live card that is easy to satisfy
    let live = LiveCard {
        card_id: 10001,
        name: "Test Live".to_string(),
        score: 10,
        required_hearts: [1, 0, 0, 0, 0, 0, 0], // 1 Pink
        ..Default::default()
    };
    db.lives.insert(10001, live.clone());
    db.lives_vec[(1 as usize) & LOGIC_ID_MASK as usize] = Some(live);

    // Create a member that gives 1 Pink heart
    let member = MemberCard {
        card_id: 100,
        name: "Test Member".to_string(),
        hearts: [1, 0, 0, 0, 0, 0, 0],
        ..Default::default()
    };
    db.members.insert(100, member.clone());
    db.members_vec[(100 as usize) & LOGIC_ID_MASK as usize] = Some(member);

    let mut state = GameState::default();
    state.core.players[0].stage[0] = 100i32;
    state.core.players[0].live_zone[0] = 10001i32;

    // Set FLAG_CANNOT_LIVE
    state.core.players[0].set_flag(PlayerState::FLAG_CANNOT_LIVE, true);
    
    state.phase = Phase::PerformanceP1;
    state.current_player = 0;
    
    // Run performance phase
    state.do_performance_phase(&db);
    
    // Check results
    if let Some(res) = state.ui.performance_results.get(&0) {
        let success = res["success"].as_bool().unwrap_or(false);
        assert!(!success, "Live show should have failed because FLAG_CANNOT_LIVE is set");
    } else {
        panic!("Performance results not generated");
    }
}
