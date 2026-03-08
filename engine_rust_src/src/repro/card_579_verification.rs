use crate::core::logic::*;
use crate::core::logic::filter::CardFilter;
use crate::test_helpers::{create_test_state, load_real_db, TestUtils};

#[test]
fn test_card_579_ability_0_cost_comparison() { // Card No: PL!N-bp1-006-P
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

    // Find "ノンフィクション!!"
    let (target_id, target_live) = db
        .lives
        .iter()
        .find(|(_, m)| m.name == "ノンフィクション!!")
        .expect("Could not find ノンフィクション!! target card for test 0");
    let target_id = *target_id;

    // Find a Liella member for stage setup
    let liella_member_id = *db
        .members
        .iter()
        .find(|(_, m)| m.groups.contains(&3))
        .map(|(id, _)| id)
        .expect("Need a Liella member for stage");
    let target_cost = db.members[&liella_member_id].cost;

    writeln!(
        log_file,
        "Target Live: {} (ID: {}), Member Cost: {}",
        target_live.name, target_id, target_cost
    )
    .unwrap();

    // P0 Center: Liella Member
    state.set_stage(0, 1, liella_member_id);

    // Find a card with strictly lower cost for Opponent
    let (low_cost_id, low_cost_cost) = db
        .members
        .iter()
        .find(|(_, m)| m.cost < target_cost)
        .map(|(id, m)| (*id, m.cost))
        .unwrap_or((130, 0));

    state.set_stage(1, 1, low_cost_id); // P1 Center: Lower Cost

    writeln!(
        log_file,
        "Opponent Card ID: {}, Cost: {}",
        low_cost_id, low_cost_cost
    )
    .unwrap();

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: target_id,
        area_idx: 1,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    let ability = db.lives[&target_id]
        .abilities
        .iter()
        .find(|a| matches!(a.trigger, TriggerType::OnLiveStart) && a.bytecode.contains(&16))
        .unwrap();
    let bytecode = ability.bytecode.clone();

    writeln!(log_file, "Bytecode: {:?}", bytecode).unwrap();

    // Test Case 1: P0 Cost > P1 Cost -> Should boost score
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    writeln!(
        log_file,
        "Resulting Bonus (Case 1): {}",
        state.players[0].live_score_bonus
    )
    .unwrap();

    assert_eq!(
        state.players[0].live_score_bonus, 1,
        "Should boost score when P0 Cost > P1 Cost"
    );

    // Reset score and swap situations
    state.players[0].live_score_bonus = 0;
    state.set_stage(1, 1, liella_member_id); // P1 Center: High Cost
    state.set_stage(0, 1, low_cost_id); // P0 Center: Lower Cost

    state.resolve_bytecode_cref(&db, &bytecode, &ctx);
    writeln!(
        log_file,
        "Resulting Bonus (Case 2): {}",
        state.players[0].live_score_bonus
    )
    .unwrap();
    assert_eq!(
        state.players[0].live_score_bonus, 0,
        "Should NOT boost score when P0 Cost < P1 Cost"
    );
}

#[test]
fn test_card_579_ability_1_heart_filter() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    // Ability 1: SELECT_MEMBER(1) {AREA="LEFT_SIDE", FILTER="GROUP_ID=3, HAS_HEART_02_X3"} -> ADD_BLADES(2)
    // Note: The report said "HAS_COLOR_YELLOW_X3" in effects params but "HAS_HEART_02_X3" in pseudocode.
    // Heart 02 is Yellow 2-value heart.

    // Find "ノンフィクション!!"
    let (target_id, target_live) = db
        .lives
        .iter()
        .find(|(_, m)| m.name == "ノンフィクション!!")
        .expect("Could not find ノンフィクション!! target card for test 1");
    let target_id = *target_id;
    crate::test_helpers::generate_card_report(target_id);

    // Find a Liella member for stage setup
    let liella_member_id = *db
        .members
        .iter()
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
    assert_eq!(
        state.players[0].blade_buffs[0], 0,
        "Should NOT add blades if heart count is insufficient"
    );

    // Test Case 2: Left side has 3 Yellow hearts (Color 2)
    println!("--- Test Case 2: Sufficient Hearts ---");
    state.players[0].heart_buffs[0].add_to_color(2, 3);

    // Verify filter matches manually using the builder (Proof of Phase 3 readability)
    let mut filter = CardFilter::new();
    filter.target_player = 1;        // Me
    filter.group_enabled = true;
    filter.group_id = 3;             // Liella!
    filter.value_enabled = true;
    filter.value_threshold = 3;       // 3+ Hearts
    filter.color_mask = 1 << 2;      // Yellow (Color 2)
    filter.is_enabled = true;
        
    let member_id = liella_member_id;
    let hearts = state.players[0].heart_buffs[0].to_array();
    assert!(
        filter.matches(&state, &db, member_id, None, false, Some(&hearts), &crate::core::logic::AbilityContext::default()),
        "Builder filter should match the stage member with hearts"
    );

    state.resolve_bytecode_cref(&db, &bytecode, &ctx);
    state.dump_verbose();
    assert_eq!(
        state.players[0].blade_buffs[0], 2,
        "Should add 2 blades if heart count is >= 3"
    );
}
