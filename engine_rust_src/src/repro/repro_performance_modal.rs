use crate::core::logic::*;
use crate::test_helpers::{create_test_db, create_test_state};

#[test]
fn test_performance_modal_breakdown_and_sum() {
    let db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    // Set Phase to Performance P1
    state.phase = Phase::PerformanceP1;
    state.current_player = 0;

    // 1. Setup two live cards
    let live_id_1 = 55001; // Score: 1, Req: 1 ANY
    let live_id_2 = 55001;
    state.players[0].live_zone[0] = live_id_1;
    state.players[0].live_zone[1] = live_id_2;
    state.players[0].set_revealed(0, true);
    state.players[0].set_revealed(1, true);

    // 2. Setup member with enough hearts (2 ANY)
    // Card 101 has 1 Pink heart. Let's use it twice.
    state.players[0].stage[0] = 101;
    state.players[0].stage[1] = 101;

    // 3. Add a score bonus
    state.players[0].live_score_bonus = 2;
    state.players[0].live_score_bonus_logs.push((101, 2));

    // 4. Run performance phase
    state.do_performance_phase(&db);

    // 5. Verify results
    let res = state.ui.performance_results.get(&0).expect("Should have results for P0");

    let total_score = res["total_score"].as_u64().expect("Should have total_score");
    assert_eq!(total_score, 1 + 1 + 2, "Total score should be sum of lives (1+1) + bonus (2)");

    let breakdown = &res["breakdown"]["scores"];
    assert!(breakdown.is_array());
    let scores = breakdown.as_array().unwrap();

    // Base scores should be summed
    let base = scores.iter().find(|s| s["type"] == "base").expect("Should have base score");
    assert_eq!(base["value"], 2);

    // Bonus should be present
    let bonus = scores.iter().find(|s| s["type"] == "triggered_ability").expect("Should have bonus score");
    assert_eq!(bonus["value"], 2);
    assert_eq!(bonus["source_id"], 101);
}
