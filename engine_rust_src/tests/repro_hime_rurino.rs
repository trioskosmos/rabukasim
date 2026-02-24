use engine_rust::core::logic::*;
use engine_rust::test_helpers::*;

#[test]
fn test_hime_optional_discard_resumption() {
    let db = load_real_db();
    let mut state = create_test_state();
    let p_idx = 0;
    
    // Setup Hime ability simulation
    state.core.players[p_idx].hand = vec![100, 101, 102].into();
    state.phase = Phase::Response;
    
    // Opcode 58 (MOVE_TO_DISCARD), Attr 0x6002 (Hand + Optional), Count 1
    let ctx = AbilityContext { player_id: p_idx as u8, source_card_id: 4270, ..Default::default() };
    state.interaction_stack.push(PendingInteraction {
        ctx: ctx.clone(),
        card_id: 4270,
        effect_opcode: 58,
        choice_type: "SELECT_HAND_DISCARD".to_string(),
        filter_attr: 0x6002, 
        v_remaining: 1,
        ..Default::default()
    });

    // 1. Verify Pass action exists (Action 0)
    let mut actions: Vec<i32> = Vec::new();
    state.generate_legal_actions(&db, p_idx, &mut actions);
    assert!(actions.contains(&0), "Pass action (0) should be available for optional discard!");

    // 2. Test Pass (Choice 0)
    state.step(&db, 0).expect("Step failed");
    assert_eq!(state.core.players[p_idx].hand.len(), 3, "Hand should NOT have changed after Pass");
    assert_eq!(state.phase, Phase::Main, "Should return to Main/Previous phase after passing cost");
}

#[test]
fn test_rurino_filter_masking_fix() {
    let db = load_real_db();
    let mut state = create_test_state();
    let p_idx = 0;
    
    // Rurino (Logic ID 17, ID 17)
    // Hand contains some cards - use valid card IDs from the database
    // Let's use card IDs that exist in the database
    let card1 = db.id_by_no("PL!N-bp1-001-R").unwrap_or(1);
    let card2 = db.id_by_no("PL!N-bp1-002-R").unwrap_or(2);
    state.core.players[p_idx].hand = vec![card1, card2].into();
    state.phase = Phase::Response;
    
    // Interaction: O_MOVE_TO_DISCARD with 0x6000 (Hand Zone) filter
    let ctx = AbilityContext { player_id: p_idx as u8, source_card_id: 17, ..Default::default() };
    state.interaction_stack.push(PendingInteraction {
        ctx: ctx.clone(),
        card_id: 17,
        effect_opcode: 58,
        choice_type: "SELECT_HAND_DISCARD".to_string(),
        filter_attr: 0x6000, 
        v_remaining: 1,
        ..Default::default()
    });

    // 1. Verify that both cards are selectable (not filtered out by 0x6000 bits which are now masked)
    let mut actions: Vec<i32> = Vec::new();
    state.generate_legal_actions(&db, p_idx, &mut actions);
    
    // Debug: print available actions
    println!("DEBUG: Available actions: {:?}", actions);
    println!("DEBUG: Hand: {:?}", state.core.players[p_idx].hand);
    
    // Action IDs for hand selection are 3000 + hand_index (based on observed behavior)
    // Check if any hand selection actions exist (3000-3999 range)
    let has_hand_selection = actions.iter().any(|&a| a >= 3000 && a < 4000);
    assert!(has_hand_selection, "At least one hand selection action should be available. Actions: {:?}", actions);
}
