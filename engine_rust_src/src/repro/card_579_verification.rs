use crate::core::logic::filter::CardFilter;
use crate::core::logic::*;
use crate::test_helpers::{create_test_state, load_real_db, TestUtils};

#[test]
fn test_card_579_ability_0_cost_comparison() {
    // Card No: PL!N-bp1-006-P
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

    // Find a Liella member for stage setup.
    let liella_member_id = *db
        .members
        .iter()
        .filter(|(_, m)| m.groups.contains(&3))
        .max_by_key(|(_, m)| m.cost)
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
        .find(|a| {
            matches!(a.trigger, TriggerType::OnLiveStart)
                && a.frames().iter().any(|frame| frame.opcode() == 16)
        })
        .unwrap();

    writeln!(log_file, "Ability frames: {:?}", ability.frames()).unwrap();
    
    // Debug: Show raw slot values
    for (i, frame) in ability.frames().iter().enumerate() {
        writeln!(log_file, "  Frame {}: raw_slot={:#x}, area_idx={}", 
                 i, frame.components().raw_slot, frame.components().slot.area_idx).unwrap();
    }

    // Test Case 1: P0 Cost > P1 Cost -> Should boost score
    state.resolve_ability(&db, ability, &ctx);

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

    state.resolve_ability(&db, ability, &ctx);
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

    let (liella_member_id, base_yellow_hearts) = db
        .members
        .iter()
        .filter(|(_, m)| m.groups.contains(&3) && m.hearts[2] == 0)
        .min_by_key(|(id, _)| *id)
        .map(|(id, m)| (*id, m.hearts[2]))
        .expect("Need a deterministic Liella member with zero yellow hearts for test 1");

    assert_eq!(
        base_yellow_hearts, 0,
        "Test fixture must start with zero yellow hearts so the initial filter check is deterministic"
    );

    state.set_stage(0, 0, liella_member_id); // Member in Left Side (0) - Group 3

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: target_id,
        area_idx: 1,
        trigger_type: TriggerType::OnLiveStart,
        ability_index: 1, // Explicitly testing ability 1
        ..Default::default()
    };

    let ability = &target_live.abilities[1];

    // Test Case 1: Left side has 0 hearts -> Should NOT add blades
    state.resolve_ability(&db, ability, &ctx);
    assert_eq!(
        state.players[0].blade_buffs[0], 0,
        "Should NOT add blades if heart count is insufficient"
    );

    state.interaction_stack.clear();
    state.phase = Phase::Main;

    // Test Case 2: Raise the same member to 3 Yellow hearts total.
    println!("--- Test Case 2: Sufficient Hearts ---");
    state.players[0].heart_buffs[0].add_to_color(2, (3 - base_yellow_hearts) as i32);

    // Verify filter matches manually using the builder (Proof of Phase 3 readability)
    let mut filter = CardFilter::new();
    filter.target_player = 1; // Me
    filter.group_enabled = true;
    filter.group_id = 3; // Liella!
    filter.value_enabled = true;
    filter.value_threshold = 3; // 3+ Hearts
    filter.color_mask = 1 << 2; // Yellow (Color 2)
    filter.compare_accumulated = true; // Need to compare hearts
    filter.is_enabled = true;

    let member_id = liella_member_id;
    let hearts = state.get_effective_hearts(0, 0, &db, 0).to_array();
    println!("Hearts array: {:?}", hearts);
    println!("Filter: target_player={}, group_enabled={}, group_id={}, value_enabled={}, value_threshold={}, color_mask={:#x}", 
        filter.target_player, filter.group_enabled, filter.group_id, filter.value_enabled, filter.value_threshold, filter.color_mask);
    println!("compare_accumulated: {}", filter.compare_accumulated);
    assert!(
        filter.matches(
            &state,
            &db,
            member_id,
            None,
            false,
            Some(&hearts),
            &crate::core::logic::AbilityContext::default()
        ),
        "Builder filter should match the stage member with hearts"
    );

    state.resolve_ability(&db, ability, &ctx);

    assert!(
        state
            .interaction_stack
            .last()
            .map(|interaction| !interaction.actions.is_empty())
            .unwrap_or(false),
        "SelectMember prompt should expose at least one legal stage slot"
    );
}
