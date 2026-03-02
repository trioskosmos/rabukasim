use crate::core::logic::*;
use crate::test_helpers::{load_real_db, create_test_state, TestUtils};

#[test]
fn test_card_579_ability_0_cost_comparison() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let mut log_file = std::fs::OpenOptions::new()
        .create(true)
        .write(true)
        .truncate(true)
        .open("../reports/card_579_debug.txt")
        .expect("Failed to open debug log");
    
    use std::io::Write;

    // Find the Liella card that has the SYNC_COST condition (opcode 311) and BOOST_SCORE (opcode 16)
    let (target_id, target_live) = db.lives.iter()
        .find(|(_, m)| m.groups.contains(&3) && m.abilities.iter().any(|a| matches!(a.trigger, TriggerType::OnLiveStart) && a.bytecode.contains(&311) && a.bytecode.contains(&16)))
        .expect("Could not find Liella target card with SYNC_COST for test 0");
    let target_id = *target_id;

    // Find a Liella member for stage setup
    let liella_member_id = *db.members.iter()
        .find(|(_, m)| m.groups.contains(&3))
        .map(|(id, _)| id)
        .expect("Need a Liella member for stage");
    let target_cost = db.members[&liella_member_id].cost;

    writeln!(log_file, "Target Live: {} (ID: {}), Member Cost: {}", target_live.name, target_id, target_cost).unwrap();

    // P0 Center: Liella Member
    state.set_stage(0, 1, liella_member_id);
    
    // Find a card with strictly lower cost for Opponent
    let (low_cost_id, low_cost_cost) = db.members.iter()
        .find(|(_, m)| m.cost < target_cost)
        .map(|(id, m)| (*id, m.cost))
        .unwrap_or((130, 0));

    state.set_stage(1, 1, low_cost_id); // P1 Center: Lower Cost

    writeln!(log_file, "Opponent Card ID: {}, Cost: {}", low_cost_id, low_cost_cost).unwrap();

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: target_id,
        area_idx: 1,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    let ability = db.lives[&target_id].abilities.iter().find(|a| matches!(a.trigger, TriggerType::OnLiveStart) && a.bytecode.contains(&16)).unwrap();
    let bytecode = ability.bytecode.clone();
    
    writeln!(log_file, "Bytecode: {:?}", bytecode).unwrap();

    // Test Case 1: P0 Cost > P1 Cost -> Should boost score
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);
    
    writeln!(log_file, "Resulting Bonus (Case 1): {}", state.core.players[0].live_score_bonus).unwrap();
    
    assert_eq!(state.core.players[0].live_score_bonus, 1, "Should boost score when P0 Cost > P1 Cost");

    // Reset score and swap situations
    state.core.players[0].live_score_bonus = 0;
    state.set_stage(1, 1, target_id); // P1 Center: High Cost
    state.set_stage(0, 1, low_cost_id); // P0 Center: Lower Cost
    
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);
    writeln!(log_file, "Resulting Bonus (Case 2): {}", state.core.players[0].live_score_bonus).unwrap();
    assert_eq!(state.core.players[0].live_score_bonus, 0, "Should NOT boost score when P0 Cost < P1 Cost");
}

#[test]
fn test_card_579_ability_1_heart_filter() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    // Ability 1: SELECT_MEMBER(1) {AREA="LEFT_SIDE", FILTER="GROUP_ID=3, HAS_HEART_02_X3"} -> ADD_BLADES(2)
    // Note: The report said "HAS_COLOR_YELLOW_X3" in effects params but "HAS_HEART_02_X3" in pseudocode.
    // Heart 02 is Yellow 2-value heart.

    // Find the card with the specific HAS_HEART_02_X3 bytecode or similar ability
    let (target_id, target_live) = db.lives.iter()
        .find(|(_, m)| m.groups.contains(&3) && m.abilities.len() > 1 && matches!(m.abilities[1].trigger, TriggerType::OnLiveStart))
        .expect("Could not find Liella target card for test 1");
    let target_id = *target_id;
    crate::test_helpers::generate_card_report(target_id);

    // Find a Liella member for stage setup
    let liella_member_id = *db.members.iter()
        .find(|(_, m)| m.groups.contains(&3))
        .map(|(id, _)| id)
        .expect("Need a Liella member for stage");

    state.set_stage(0, 1, liella_member_id); // Source card (Member)
    state.set_stage(0, 0, liella_member_id); // Member in Left Side (0) - Group 3

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: target_id,
        area_idx: 1,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    let bytecode = target_live.abilities[1].bytecode.clone();

    // Test Case 1: Left side has 0 hearts -> Should NOT add blades
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);
    assert_eq!(state.core.players[0].blade_buffs[0], 0, "Should NOT add blades if heart count is insufficient");

    // Test Case 2: Left side has 3 Yellow hearts (Color 2)
    println!("--- Test Case 2: Sufficient Hearts ---");
    state.core.players[0].heart_buffs[0].add_to_color(2, 3);
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);
    state.dump_verbose();
    assert_eq!(state.core.players[0].blade_buffs[0], 2, "Should add 2 blades if heart count is >= 3");
}
