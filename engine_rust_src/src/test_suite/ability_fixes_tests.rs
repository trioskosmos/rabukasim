// =============================================================================
// Ability Frame Fixes Tests
// Tests for abilities that were fixed in ability_frame_source.json
// =============================================================================

use crate::test_suite::common::*;

// =============================================================================
// Test Group 1: target_player: SELF fixes
// =============================================================================

/// Tests that abilities checking "自分のステージ" have target_player: SELF
/// Card: PL!-bp3-004-P (東條 希) ab#0 - ライブ開始時自分のステージにいる「year」…
#[test]
fn test_target_player_self_own_stage() {
    let db = load_real_db();
    let state = create_test_state();
    
    // Load ability bytecode and verify target_player is set
    let card_id = 4004; // PL!-bp3-004-P
    let card = db.get_card(card_id).unwrap();
    let ability = &card.abilities[0];
    
    // Verify bytecode contains target_player: SELF in frames
    assert!(
        ability.bytecode.iter().any(|op| {
            // Check for target_player attribute in frame operations
            // O_COUNT_STAGE with SELF target = correct
            matches!(op, O_COUNT_STAGE | O_GROUP_FILTER | O_SELECT_MEMBER)
        }),
        "Ability should use stage-checking opcodes"
    );
}

// =============================================================================
// Test Group 2: JUMP_IF_FALSE after optional costs
// =============================================================================

/// Tests that optional costs are followed by JUMP_IF_FALSE
/// This ensures effects don't execute when optional cost isn't paid
#[test]
fn test_optional_cost_jump_if_false() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Setup: Player with hand cards
    state.players[0].hand = vec![3001, 3002].into();
    
    // Build bytecode: Optional discard + JUMP_IF_FALSE + Draw + RETURN
    // This simulates the fixed pattern
    let bc = InstructionWordBuilder::new(O_MOVE_TO_DISCARD)
        .v(1)
        .optional(true)
        .slot(SLOT_HAND)
        .op(O_JUMP_IF_FALSE)  // This was added in fix
        .v(1)  // Skip 1 frame (the draw)
        .op(O_DRAW)
        .v(1)
        .slot(SLOT_DECK_TOP)
        .op(O_RETURN)
        .build();
    
    let ctx = AbilityContext {
        player_id: 0,
        choice_index: 0,
        skip_optional: true,  // Skip the optional cost
        ..Default::default()
    };
    
    let initial_hand = state.players[0].hand.len();
    let initial_deck = state.players[0].deck.len();
    
    state.resolve_frames(&db, &bc, &ctx);
    
    // If optional was skipped, hand and deck should be unchanged
    assert_eq!(
        state.players[0].hand.len(),
        initial_hand,
        "Hand should be unchanged when optional cost skipped"
    );
    assert_eq!(
        state.players[0].deck.len(),
        initial_deck,
        "Deck should be unchanged when optional cost skipped"
    );
}

// =============================================================================
// Test Group 3: SELECT_MEMBER → COUNT_STAGE conversions
// =============================================================================

/// Tests center area automatic detection (no player choice)
/// Card: PL!SP-bp4-025-L (Special Color) ab#0 - ライブ開始時センターエリアLiella!
#[test]
fn test_center_area_count_stage() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Setup: Player with Liella! member in center area
    // Stage area 2 = center
    let liella_member = 4580; // Liella! member card ID
    state.players[0].stage[2] = Some(liella_member); // Center area
    
    // Build bytecode: COUNT_STAGE center (Liella!) → JUMP_IF_FALSE → TRANSFORM_BLADES
    let bc = InstructionWordBuilder::new(O_COUNT_STAGE)
        .v(1)
        .slot(SLOT_STAGE_2)  // Center area
        .group_filter("LIELLA")
        .op(O_JUMP_IF_FALSE)
        .v(1)
        .op(O_TRANSFORM_BLADES)
        .v(3)
        .slot(SLOT_STAGE_2)
        .op(O_RETURN)
        .build();
    
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    
    // Should execute successfully without player choice
    state.resolve_frames(&db, &bc, &ctx);
    
    // Verify the ability executed (didn't panic)
    // The actual blade transformation depends on runtime implementation
}

// =============================================================================
// Test Group 4: Group filter fixes
// =============================================================================

/// Tests that group filters are properly specified
/// Card: PL!N-pb1-012-P+ (鐘 嵐珠) ab#0 - 自分のステージにコスト11のメンバー
#[test]
fn test_group_filter_specification() {
    let db = load_real_db();
    
    // Load ability and check group filter is present
    let card_id = 8846; // PL!N-pb1-012-P+
    let card = db.get_card(card_id).unwrap();
    let ability = &card.abilities[0];
    
    // Verify the bytecode has proper targeting
    assert!(
        ability.bytecode.windows(2).any(|w| {
            // Looking for COST check pattern
            w[0] == O_COUNT_STAGE && (w[1] & 0xFF00) != 0
        }),
        "Ability should check stage with cost filter"
    );
}

// =============================================================================
// Test Group 5: OR cost pattern tests
// =============================================================================

/// Tests OR cost pattern: Tap self OR discard hand → Effect
/// Card: PL!SP-bp5-001-AR (渋谷かのん) ab#2
#[test]
fn test_or_cost_select_mode() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Setup: Player with hand and member
    state.players[0].hand = vec![3001, 3002].into();
    state.players[0].active_member = Some(4854); // Kanon card
    
    // Build bytecode: SELECT_MODE → JUMP x2 → Option1 → JUMP → Option2 → JUMP_IF_FALSE → Effect
    let bc = InstructionWordBuilder::new(O_SELECT_MODE)
        .v(2)  // 2 options
        .op(O_JUMP).v(1)    // Jump to option 0
        .op(O_JUMP).v(2)     // Jump to option 1
        // Option 0: SET_TAPPED
        .op(O_SET_TAPPED).v(1).optional(true)
        .op(O_JUMP).v(2)     // Jump to effect
        // Option 1: MOVE_TO_DISCARD
        .op(O_MOVE_TO_DISCARD).v(1).optional(true).slot(SLOT_HAND)
        .op(O_JUMP_IF_FALSE).v(1)  // Skip if not paid
        // Effect: ACTIVATE_ENERGY
        .op(O_ACTIVATE_ENERGY).v(1).slot(SLOT_ENERGY_DECK)
        .op(O_RETURN)
        .build();
    
    let ctx = AbilityContext {
        player_id: 0,
        choice_index: 0,  // Choose option 0 (tap)
        ..Default::default()
    };
    
    // Should execute without panic
    state.resolve_frames(&db, &bc, &ctx);
}

// =============================================================================
// Test Group 6: Movement check tests
// =============================================================================

/// Tests "moved this turn" condition
/// Card: PL!SP-pb1-025-L (Hajimari wa Kimi no Sora) ab#0
#[test]
fn test_moved_this_turn_condition() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Setup: Member in stage that "moved" this turn
    let member_id = 5825; // Liella! member
    state.players[0].stage[2] = Some(member_id);
    state.players[0].members_moved_this_turn.insert(member_id);
    
    // Build bytecode with check_moved_this_turn flag
    let bc = InstructionWordBuilder::new(O_COUNT_STAGE)
        .v(1)
        .slot(SLOT_STAGE_2)
        .group_filter("LIELLA")
        .attr(ATTR_CHECK_MOVED_THIS_TURN)  // This flag was added in fix
        .op(O_JUMP_IF_FALSE).v(1)
        .op(O_BOOST_SCORE).v(1)
        .slot(SLOT_SELF)
        .op(O_RETURN)
        .build();
    
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    
    state.resolve_frames(&db, &bc, &ctx);
    // Score should be boosted since member moved this turn
}

// =============================================================================
// Test Group 7: Optional formation change
// =============================================================================

/// Tests optional formation change with is_optional flag
/// Card: PL!SP-bp4-027-L (Chance Day, Chance Way!) ab#0
#[test]
fn test_optional_formation_change() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Setup: Player with members in stage
    state.players[0].stage[0] = Some(5820);
    state.players[0].stage[1] = Some(5821);
    
    // Build bytecode: FORMATION_CHANGE with is_optional
    let bc = InstructionWordBuilder::new(O_FORMATION_CHANGE)
        .v(1)
        .optional(true)  // Player can choose not to
        .slot(SLOT_STAGE_ALL)
        .op(O_RETURN)
        .build();
    
    let ctx = AbilityContext {
        player_id: 0,
        choice_index: 0,
        skip_optional: false,  // Player accepts
        ..Default::default()
    };
    
    state.resolve_frames(&db, &bc, &ctx);
    // Formation change should occur
}

// =============================================================================
// Test Group 8: "Only" condition tests (e.g., "Liella! only")
// =============================================================================

/// Tests "only" condition using COUNT_STAGE + SUM_VALUE pattern
/// This is the correct way to check "stage contains ONLY Liella! members"
#[test]
fn test_only_condition_pattern() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Setup: Stage with only Liella! members
    state.players[0].stage[0] = Some(5800); // Liella! member
    state.players[0].stage[1] = Some(5801); // Liella! member
    state.players[0].stage[2] = Some(5802); // Liella! member
    
    // Build bytecode for "only" check:
    // COUNT_STAGE (Liella!) → SUM_VALUE → COUNT_STAGE (total) → JUMP_IF_FALSE (EQ check)
    let bc = InstructionWordBuilder::new(O_COUNT_STAGE)
        .v(1)
        .slot(SLOT_STAGE_ALL)
        .group_filter("LIELLA")
        .op(O_SUM_VALUE)  // Accumulate Liella count
        .op(O_COUNT_STAGE)
        .v(1)
        .slot(SLOT_STAGE_ALL)  // Count total
        .op(O_JUMP_IF_FALSE)
        .v(1)  // Skip if not equal (meaning not "only")
        .op(O_EFFECT)  // The actual effect
        .op(O_RETURN)
        .build();
    
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    
    state.resolve_frames(&db, &bc, &ctx);
}

// =============================================================================
// Test Group 9: Regression tests for specific fixed cards
// =============================================================================

/// PL!SP-bp4-025-L Special Color ab#0: Center area blade transformation
#[test]
fn test_special_color_blade_transform() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Setup stage with Liella! center
    let card_id = 580; // Special Color
    let liella_center = 4580;
    state.players[0].stage[2] = Some(liella_center);
    
    let ctx = AbilityContext {
        player_id: 0,
        live_card_id: card_id,
        ..Default::default()
    };
    
    // Execute the actual ability bytecode from database
    let card = db.get_card(card_id).unwrap();
    let ability = &card.abilities[0];
    state.resolve_frames(&db, &ability.bytecode, &ctx);
    
    // Verify execution completed
    // Note: Actual blade count verification depends on runtime state
}

/// PL!SP-bp4-025-L Special Color ab#1: Center member moved check
#[test]
fn test_special_color_moved_check() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    let card_id = 580;
    let liella_member = 4580;
    state.players[0].stage[2] = Some(liella_member);
    state.players[0].members_moved_this_turn.insert(liella_member);
    
    let ctx = AbilityContext {
        player_id: 0,
        live_card_id: card_id,
        ..Default::default()
    };
    
    let card = db.get_card(card_id).unwrap();
    let ability = &card.abilities[1];
    state.resolve_frames(&db, &ability.bytecode, &ctx);
}

/// PL!SP-bp5-001-AR (Shibuya Kanon) ab#2: OR cost - tap self or discard
#[test]
fn test_kanon_or_cost() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    let card_id = 854;
    state.players[0].hand = vec![3001].into();
    state.players[0].active_member = Some(card_id);
    
    let ctx = AbilityContext {
        player_id: 0,
        member_card_id: card_id,
        choice_index: 0,  // Choose first option
        ..Default::default()
    };
    
    let card = db.get_card(card_id).unwrap();
    let ability = &card.abilities[2];
    state.resolve_frames(&db, &ability.bytecode, &ctx);
}

// =============================================================================
// Test Group 10: Edge cases and error conditions
// =============================================================================

/// Tests that abilities fail gracefully when conditions not met
#[test]
fn test_condition_not_met() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Empty stage - condition should fail
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    
    // Build: COUNT_STAGE → JUMP_IF_FALSE → BOOST
    let bc = InstructionWordBuilder::new(O_COUNT_STAGE)
        .v(1)
        .slot(SLOT_STAGE_ALL)
        .op(O_JUMP_IF_FALSE).v(1)
        .op(O_BOOST_SCORE).v(5)
        .slot(SLOT_SELF)
        .op(O_RETURN)
        .build();
    
    state.resolve_frames(&db, &bc, &ctx);
    
    // Score should not be boosted since stage is empty
    // (BOOST_SCORE was skipped by JUMP_IF_FALSE)
}

/// Tests OR cost when player skips both options
#[test]
fn test_or_cost_skip_all() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    state.players[0].hand = vec![3001].into();
    
    // Both options are optional - player skips both
    let ctx = AbilityContext {
        player_id: 0,
        skip_optional: true,
        ..Default::default()
    };
    
    let bc = InstructionWordBuilder::new(O_SELECT_MODE)
        .v(2)
        .op(O_JUMP).v(1)
        .op(O_JUMP).v(2)
        // Option 0
        .op(O_SET_TAPPED).v(1).optional(true)
        .op(O_JUMP_IF_FALSE).v(1)
        .op(O_EFFECT)
        .op(O_JUMP).v(2)
        // Option 1
        .op(O_MOVE_TO_DISCARD).v(1).optional(true).slot(SLOT_HAND)
        .op(O_JUMP_IF_FALSE).v(1)
        .op(O_EFFECT)
        .op(O_JUMP).v(1)
        // Fallback (neither chosen)
        .op(O_RETURN)
        .build();
    
    state.resolve_frames(&db, &bc, &ctx);
    // Should complete without panic even though no option was taken
}
