use crate::core::logic::*;
use crate::core::generated_constants::{O_PLAY_MEMBER_FROM_DISCARD, O_RETURN, FLAG_EMPTY_SLOT_ONLY};
use crate::test_helpers::load_real_db;

#[test]
fn test_repro_card_103_placement() { // Card No: LL-bp2-001-R
    let mut state = GameState::default();
    let db = load_real_db();

    let p_idx = 0;
    state.players[p_idx].player_id = 0;

    // Fill all stage slots
    state.players[p_idx].stage = [1, 2, 3];

    // Add a cost 2 member to discard
    state.players[p_idx].discard = vec![100].into(); // Assume 100 is a valid member

    // Card 103 Bytecode for Ability 0 (simplified)
    // Opcode 63 (PLAY_MEMBER_FROM_DISCARD), v=1, a=Filter(Cost<=2), s=FLAG_EMPTY_SLOT_ONLY | Stage
    let s_word = FLAG_EMPTY_SLOT_ONLY | 4; // 4 is Stage zone
    let bytecode = vec![
        O_PLAY_MEMBER_FROM_DISCARD as i32, 1, 0, 0, s_word as i32,
        O_RETURN as i32, 0, 0, 0, 0
    ];

    let ctx = AbilityContext {
        player_id: p_idx as u8,
        source_card_id: 103,
        ability_index: 0,
        ..Default::default()
    };

    // Execute
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // Generate actions
    let mut actions = Vec::new();
    state.generate_legal_actions(&db, p_idx, &mut actions);

    // If all slots are full and FLAG_EMPTY_SLOT_ONLY is set,
    // it should either offer Action 0 (Pass) or skip if mandatory.
    // If it's mandatory but no slots exist, it should likely end without softlocking.

    println!("Actions: {:?}", actions);
    // Action 0 should be available if no slots are available
    assert!(actions.contains(&0), "Action 0 (Pass) should be available when no empty slots exist");
    // Action 500+ (Choice) should NOT contain stage slots 0, 1, 2 if they are full
    for i in 0..3 {
        let action_id = crate::core::logic::ACTION_BASE_CHOICE + i as i32;
        assert!(!actions.contains(&action_id), "Slot {} should not be selectable for EMPTY_SLOT_ONLY play", i);
    }
}
