//! Tests for core rule enforcement (Referee Logic).
//! These tests verify that the engine correctly prevents actions when costs or conditions are not met.

use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::core::logic::*;
use crate::test_helpers::{create_test_db, create_test_state};

#[test]
fn test_enforce_cost_failure() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Create member with cost 2 energy
    let cid = 3991;
    let mut m = MemberCard::default();
    m.card_id = cid;
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        costs: vec![Cost {
            cost_type: AbilityCostType::Energy,
            value: 2,
            ..Default::default()
        }],
        frame_program: Some(FrameProgram::from_instruction_words(&[
            O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0,
        ])),
        ..Default::default()
    });
    db.members.insert(cid, m.clone());
    db.members_vec[(cid as usize) & LOGIC_ID_MASK as usize] = Some(m);

    state.players[0].stage[0] = cid;
    state.players[0].energy_zone.clear(); // 0 Energy
    state.debug.debug_ignore_conditions = false; // ENSURE ENFORCEMENT IS ON

    // Attempt to activate (0, 0)
    let res = state.activate_ability(&db, 0, 0);
    assert!(res.is_err(), "Should fail due to insufficient energy");
    assert!(res.unwrap_err().contains("Cannot afford cost"));
}

#[test]
fn test_enforce_condition_failure() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Create member with condition Stage >= 3
    let cid = 3992;
    let mut m = MemberCard::default();
    m.card_id = cid;
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        conditions: vec![Condition {
            condition_type: ConditionType::CountStage,
            value: 3,
            ..Default::default()
        }],
        frame_program: Some(FrameProgram::from_instruction_words(&[
            O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0,
        ])),
        ..Default::default()
    });
    db.members.insert(cid, m.clone());
    db.members_vec[(cid as usize) & LOGIC_ID_MASK as usize] = Some(m);

    state.players[0].stage = [cid, -1, -1]; // Only 1 member
    state.debug.debug_ignore_conditions = false;

    // Attempt to activate (0, 0)
    let res = state.activate_ability(&db, 0, 0);
    assert!(
        res.is_err(),
        "Should fail due to conditions not met (Stage count < 3)"
    );
    assert!(res.unwrap_err().contains("Conditions not met"));
}

#[test]
fn test_enforce_once_per_turn_failure() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Create member with Once Per Turn
    let cid = 3993;
    let mut m = MemberCard::default();
    m.card_id = cid;
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        is_once_per_turn: true,
        frame_program: Some(FrameProgram::from_instruction_words(&[
            O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0,
        ])),
        ..Default::default()
    });
    db.members.insert(cid, m.clone());
    db.members_vec[(cid as usize) & LOGIC_ID_MASK as usize] = Some(m);

    state.players[0].stage[0] = cid;
    state.players[0].deck = vec![1, 2, 3].into();
    state.debug.debug_ignore_conditions = false;

    // First activation - Success
    let res1 = state.activate_ability(&db, 0, 0);
    assert!(
        res1.is_ok(),
        "First activation should succeed. Error: {:?}",
        res1.err()
    );

    // Second activation - Failure
    let res2 = state.activate_ability(&db, 0, 0);
    assert!(
        res2.is_err(),
        "Second activation should fail due to Once-Per-Turn"
    );
    assert!(res2.unwrap_err().contains("Ability already used this turn"));
}

#[test]
fn test_enforce_turn2_limit() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    let cid = 3995;
    let mut m = MemberCard::default();
    m.card_id = cid;
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        turn_limit: 2,
        frame_program: Some(FrameProgram::from_instruction_words(&[
            O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0,
        ])),
        ..Default::default()
    });
    db.members.insert(cid, m.clone());
    db.members_vec[(cid as usize) & LOGIC_ID_MASK as usize] = Some(m);

    state.players[0].stage[0] = cid;
    state.players[0].deck = vec![1, 2, 3, 4].into();
    state.debug.debug_ignore_conditions = false;

    let res1 = state.activate_ability(&db, 0, 0);
    assert!(res1.is_ok(), "First activation should succeed");

    let res2 = state.activate_ability(&db, 0, 0);
    assert!(res2.is_ok(), "Second activation should also succeed");

    let res3 = state.activate_ability(&db, 0, 0);
    assert!(res3.is_err(), "Third activation should fail for turn 2 limit");
    assert!(res3.unwrap_err().contains("Ability already used this turn"));
}

#[test]
fn test_once_per_turn_is_tracked_per_ability_index() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    let cid = 3996;
    let mut m = MemberCard::default();
    m.card_id = cid;
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        is_once_per_turn: true,
        frame_program: Some(FrameProgram::from_instruction_words(&[
            O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0,
        ])),
        ..Default::default()
    });
    m.abilities.push(Ability {
        trigger: TriggerType::Activated,
        frame_program: Some(FrameProgram::from_instruction_words(&[
            O_DRAW, 1, 0, 0, O_RETURN, 0, 0, 0,
        ])),
        ..Default::default()
    });
    db.members.insert(cid, m.clone());
    db.members_vec[(cid as usize) & LOGIC_ID_MASK as usize] = Some(m);

    state.players[0].stage[0] = cid;
    state.players[0].deck = vec![1, 2, 3, 4].into();
    state.debug.debug_ignore_conditions = false;

    let res1 = state.activate_ability(&db, 0, 0);
    assert!(res1.is_ok(), "First ability should activate successfully");

    let res2 = state.activate_ability(&db, 0, 0);
    assert!(res2.is_err(), "The same ability index should remain limited");
    assert!(res2.unwrap_err().contains("Ability already used this turn"));

    let res3 = state.activate_ability(&db, 0, 1);
    assert!(res3.is_ok(), "A different ability index should not be blocked");
    assert_eq!(state.players[0].hand.len(), 2);
}

#[test]
fn test_enforce_play_member_cost_failure() {
    let mut db = create_test_db();
    let mut state = create_test_state();

    // Member with cost 2
    let cid = 3994;
    let mut m = MemberCard::default();
    m.card_id = cid;
    m.cost = 2;
    db.members.insert(cid, m.clone());
    db.members_vec[(cid as usize) & LOGIC_ID_MASK as usize] = Some(m);

    state.players[0].hand = vec![cid].into();
    state.players[0].energy_zone.clear(); // 0 Energy
    state.debug.debug_ignore_conditions = false;

    // Attempt to play to slot 0
    let res = state.play_member(&db, 0, 0);
    assert!(
        res.is_err(),
        "Should fail to play member due to insufficient energy"
    );
    assert!(res.unwrap_err().contains("Not enough energy"));
}
