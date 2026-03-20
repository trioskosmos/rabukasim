use crate::test_helpers::{create_test_state, create_test_db, add_card};
use crate::core::enums::{Phase, TriggerType};

#[test]
fn test_repro_card_4684_score_boost() {
    let mut db = create_test_db();
    
    // Explicitly add card 4684 to the test DB
    // ライブ成功時EEEEEE支払ってもよい：ライブの合計スコアを＋１する。
    // Bytecode: [64, 6, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 0, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0]
    add_card(
        &mut db,
        4684,
        "PL!SP-pb1-001-R",
        vec![3], // Liella!
        vec![(
            TriggerType::OnLiveSuccess,
            vec![64, 6, 0, 536870912, 0, 3, 2, 0, 0, 0, 312, 0, 0, 0, 0, 16, 1, 0, 0, 4, 1, 0, 0, 0, 0],
            vec![],
        )],
    );

    let mut state = create_test_state();
    state.debug.debug_ignore_conditions = true;
    let p_idx = 0;
    
    // Set up state
    state.core.players[p_idx].energy_zone = vec![3001, 3002, 3003, 3004, 3005, 3006].into(); // Need 6 Energy cards
    state.core.players[p_idx].stage[0] = 4684;
    state.core.players[p_idx].live_zone[0] = 55001; // Valid live card ID from test_helpers
    state.core.phase = Phase::PerformanceP1;

    // Simulate Live Success
    state.ui.performance_results.insert(
        p_idx as u8,
        serde_json::json!({
            "success": true,
            "lives": [
                {"passed": true, "score": 1, "slot_idx": 0}
            ],
            "note_icons": 0,
            "total_score": 1
        }),
    );
    
    // Trigger Live Result
    state.do_live_result(&db);
    
    // Check if we have a pending interaction for PAY_ENERGY
    assert!(!state.core.interaction_stack.is_empty(), "Expected a pending interaction for PAY_ENERGY");
    
    let pi = state.core.interaction_stack.last().unwrap().clone();
    assert_eq!(pi.effect_opcode, 64); // O_PAY_ENERGY (64)
    
    // Pay the energy (6) -> Choice 1 (Yes)
    // Note: choice 1 is "Yes" for O_PAY_ENERGY (optional).
    // Choice indices: 0 = No, 1 = Yes
    state.activate_ability_with_choice(&db, pi.ctx.area_idx as usize, pi.ctx.ability_index as usize, 1, -1).unwrap();
    
    // Now check if energy is tapped and score is boosted. 
    for i in 0..6 {
        assert!(state.core.players[p_idx].is_energy_tapped(i), "Energy {} should be tapped", i);
    }

    // Live card 55001 has base score 1.
    // Card 4684 adds +1 score bonus.
    // Total should be 2.
    assert_eq!(state.core.players[p_idx].score, 2, "Player score should be 2 after boost");
    println!("Test passed: Player score is {}", state.core.players[p_idx].score);
}
