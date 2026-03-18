use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::enums::*;
use engine_rust::core::models::AbilityContext;

#[test]
fn test_rule_4_1_4_negation_cleanup() {
    let mut state = GameState::default();
    let db = CardDatabase::default();
    let p_idx = 0;
    let card_id = 101;
    let slot = 0;

    // Setup: Card on stage with a negated trigger
    state.core.players[p_idx].stage[slot] = card_id;
    state.core.players[p_idx].negated_triggers.push((card_id, TriggerType::OnPlay, 1));

    assert!(state.is_trigger_negated(p_idx, card_id, TriggerType::OnPlay));

    // Action: Card leaves stage
    let ctx = AbilityContext::default();
    state.handle_member_leaves_stage(p_idx, slot, &db, &ctx);

    // Verification: Negation should be cleared
    assert!(!state.is_trigger_negated(p_idx, card_id, TriggerType::OnPlay), "Negation should be cleared after leaving stage (Rule 4.1.4)");
}

#[test]
fn test_rule_8_4_7_1_tie_catchup() {
    let mut state = GameState::default();
    let mut db = CardDatabase::default();
    
    // Manually insert valid live cards into DB for lookup
    let mut lc = engine_rust::core::logic::LiveCard::default();
    lc.card_id = 6;
    db.lives.insert(6, lc);

    // Setup: P0 has 2 lives, P1 has 0 lives. Both have success and equal scores.
    state.core.players[0].success_lives.push(1);
    state.core.players[0].success_lives.push(2);
    state.core.players[1].success_lives.clear();

    // Performance result snapshot
    let mut results = std::collections::HashMap::new();
    results.insert(0, serde_json::json!({"success": true, "lives": [{"passed": true, "score": 10}, {"passed": false}, {"passed": false}]}));
    results.insert(1, serde_json::json!({"success": true, "lives": [{"passed": true, "score": 10}, {"passed": false}, {"passed": false}]}));
    state.ui.performance_results = results;

    // Use ID 6 which is a valid LIVE card in the DB
    state.core.players[0].live_zone[0] = 6;
    state.core.players[1].live_zone[0] = 6; 
    
    // Add members to stage so they can be moved to success pile
    state.core.players[0].stage[0] = 1;
    state.core.players[1].stage[0] = 1;
    
    // Give enough hearts to meet requirements
    use engine_rust::core::hearts::HeartBoard;
    let hb = HeartBoard::from_array(&[5; 7]);
    state.core.players[0].heart_buffs[0] = hb;
    state.core.players[1].heart_buffs[0] = hb;

    // Action: Run live result
    state.do_live_result(&db);

    // Debugging
    println!("[TEST DEBUG] P0 lives: {}, P1 lives: {}", 
        state.core.players[0].success_lives.len(),
        state.core.players[1].success_lives.len());
    
    // Verification:
    // Rule 8.4.7.1: P0 (2 lives) should NOT move card. P1 (0 lives) SHOULD move card.
    assert_eq!(state.core.players[0].success_lives.len(), 2, "P0 should stay at 2 lives due to Rule 8.4.7.1 catch-up");
    assert_eq!(state.core.players[1].success_lives.len(), 1, "P1 should gain a life on tie");
}

#[test]
fn test_rule_9_5_3_timing_interleaving() {
    let mut state = GameState::default();
    let db = CardDatabase::default();

    // Setup: Slot 0 has a member and some energy.
    state.core.players[0].stage[0] = 101;
    state.core.players[0].stage_energy[0].push(501);
    state.core.players[0].stage_energy_count[0] = 1;

    // Queue two triggers:
    // 1. Remove member from Slot 0.
    // 2. Dummy that does nothing but check if SBA ran.
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    
    // We manually simulate the first resolution because immediate resolve is easier to test timing
    // Instead of full interpreter, we check if perform_rule_processing cleans up energy
    
    state.core.players[0].stage[0] = -1; // Simulate member being discarded/removed by Ability 1
    
    // Current Rule 10.5.3: Reclaiming energy happens during rule checks
    state.perform_rule_processing(&db);
    
    assert_eq!(state.core.players[0].stage_energy_count[0], 0, "Energy should be reclaimed by SBA immediately (Rule 10.5.3)");
    assert!(state.core.players[0].energy_deck.contains(&501), "Energy should be in energy deck");
}
