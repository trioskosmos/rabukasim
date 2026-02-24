use crate::core::logic::*;
use crate::core::generated_constants::{O_SELECT_MODE, O_JUMP, O_PAY_ENERGY, O_MOVE_TO_DISCARD, O_RETURN, CHOICE_FLAG_MODE, ACTION_BASE_MODE};
use crate::core::enums::TriggerType;
use crate::test_helpers::load_real_db;
use smallvec::smallvec;

#[test]
fn test_repro_pb1_001_r_softlock_fix() {
    let mut state = GameState::default();
    let mut db = load_real_db();
    
    // Inject mock card for PL!SP-pb1-001-R
    let mut mock_member = MemberCard::default();
    mock_member.card_id = 4684;
    
    // Ability 0: ON_LIVE_START Select Mode -> [0] Pay 2 Energy, [1] Discard 2 Hand -> else [2] Start Live (Implicit)
    let mut ability = Ability::default();
    ability.trigger = TriggerType::OnLiveStart;
    ability.choice_flags = CHOICE_FLAG_MODE;
    // Compiled BC for pb1-001-R's Select Mode
    ability.bytecode = vec![
        O_SELECT_MODE as i32, 2, 12, 20, // 0, 1, 2, 3 (Jumps to 12 and 20)
        O_JUMP as i32, 2, 0, 0,         // 4, 5, 6, 7
        O_JUMP as i32, 3, 0, 0,         // 8, 9, 10, 11
        O_PAY_ENERGY as i32, 2, 0, 0,   // 12, 13, 14, 15
        O_JUMP as i32, 3, 0, 0,         // 16, 17, 18, 19
        O_MOVE_TO_DISCARD as i32, 2, 0, 6, // 20, 21, 22, 23
        O_JUMP as i32, 1, 0, 0,         // 24, 25, 26, 27
        O_RETURN as i32, 0, 0, 0        // 28, 29, 30, 31
    ];
    mock_member.abilities.push(ability);
    
    db.members.insert(4684, mock_member.clone());
    db.members_vec[4684 as usize % LOGIC_ID_MASK as usize] = Some(mock_member);

    state.core.players[0].player_id = 0;
    state.core.players[1].player_id = 1;

    // Test Case: Empty hand, enough energy.
    // Cost 1 (Pay 2 Energy) is VALID. Cost 2 (Discard 2 Hand) is INVALID.
    state.core.players[0].hand.clear();
    state.core.players[0].energy_zone = smallvec![100, 101]; // 2 Energy available
    
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: 4684,
        ability_index: 0,
        ..Default::default()
    };
    
    // Start the ability to hit the mode selection interaction suspension
    state.resolve_bytecode(&db, &db.get_member(4684).unwrap().abilities[0].bytecode, &ctx);
    
    // Engine should be suspended waiting for interaction
    assert_eq!(state.phase, Phase::Response);
    
    // Generate the actions available to the player at this pause
    let mut actions = Vec::new();
    state.generate_legal_actions(&db, 0, &mut actions);
    
    // Based on validation logic, only Mode 0 (Pay Energy) should be available. Mode 1 (Discard Hand) is skipped.
    assert!(actions.contains(&(ACTION_BASE_MODE as i32 + 0)), "Option 0 (Pay Energy) should be valid!");
    assert!(!actions.contains(&(ACTION_BASE_MODE as i32 + 1)), "Option 1 (Discard Hand) MUST BE HIDDEN to prevent softlock!");
}
