//! Tests for Response phase flow, ability pausing, and resumption.
//! These tests verify that the engine correctly captures state and resumes
//! execution after player input.

use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::test_helpers::create_test_state;

use crate::core::logic::*;

fn create_test_db() -> CardDatabase {
    let mut db = CardDatabase::default();
    
    // Member 500 with O_RECOVER_MEMBER ability
    let m = MemberCard {
        card_id: 500,
        abilities: vec![
            Ability {
                trigger: TriggerType::Activated, // or whatever triggers manually
                bytecode: vec![O_RECOVER_MEMBER, 1, 0, 0, O_RETURN, 0, 0, 0],
                ..Default::default()
            }
        ],
        ..Default::default()
    };
    db.members.insert(500, m.clone());
    db.members.insert(99, MemberCard { card_id: 99, ..Default::default() });
    db.members_vec.resize(8431, None);
    db.members_vec[(500 as usize) & LOGIC_ID_MASK as usize] = Some(db.members[&500].clone());
    db.members_vec[(99 as usize) & LOGIC_ID_MASK as usize] = Some(db.members[&99].clone());

    db
}

/// Verifies that an ability requiring a target selection correctly pauses and enters Response phase.
#[test]
fn test_ability_pause_for_selection() {
    let db = create_test_db();
    let mut state = create_test_state();

    state.core.players[0].stage[0] = 500;
    state.core.players[0].discard = vec![99].into(); // ID 99 is in our test DB
    println!("DEBUG: Discard before recovery: {:?}", state.core.players[0].discard);
    
    // Activate ability 0 on slot 0
    state.activate_ability(&db, 0, 0).unwrap();
    
    // Should be in Response phase, waiting for choice
    assert_eq!(state.phase, Phase::Response);
    assert_eq!(state.interaction_stack.last().map(|p| p.effect_opcode).unwrap_or(0), O_RECOVER_MEMBER);
    assert!(!state.interaction_stack.is_empty());
    assert_eq!(state.core.players[0].looked_cards.len(), 1);
}

/// Verifies that providing a choice correctly resumes the ability and transitions back to Main phase.
#[test]
fn test_ability_resumption_after_choice() {
    let db = create_test_db();
    let mut state = create_test_state();

    state.core.players[0].stage[0] = 500;
    state.core.players[0].discard = vec![99].into();
    
    // 1. Pause
    state.activate_ability(&db, 0, 0).unwrap();
    assert_eq!(state.phase, Phase::Response);
    
    // 2. Resume with choice (Select Card 99 at index 0)
    state.activate_ability_with_choice(&db, 0, 0, 0, 0).unwrap();
    
    // 3. Verify results
    assert_eq!(state.phase, Phase::Main);
    assert!(state.core.players[0].hand.contains(&99));
    assert!(state.core.players[0].discard.is_empty());
    assert!(state.interaction_stack.is_empty());
}

/// Verifies that multiple activations or nested triggers correctly manage the pending context.
#[test]
fn test_nested_trigger_flow_simple() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Trigger depth acts as a recursion counter. It should return to its initial state
    // after the trigger chain finishes.
    let initial_depth = state.trigger_depth;
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    
    state.trigger_abilities(&db, TriggerType::TurnStart, &ctx);
    
    // Verify that depth returned to its starting value
    assert_eq!(state.trigger_depth, initial_depth); 
}
