/// Simple test to verify that the YELL_CARDS condition handler is working
use crate::core::logic::*;
use crate::test_helpers::{load_real_db, create_test_state};

#[test]
fn test_yell_cards_condition_directly() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    // Create a simple condition that matches "YELL_CARDS"
    let condition = Condition {
        condition_type: ConditionType::None,
        value: 3,
        attr: 0,
        target_slot: 0,
        is_negated: false,
        params: serde_json::json!({
            "raw_cond": "YELL_CARDS",
            "FILTER": "GROUP_ID=3, UNIQUE_NAMES",
            "MIN": 3
        }),
    };
    
    // Get some Liella! members
    let mut liella_members = Vec::new();  
    for cid in 100..600 {
        if let Some(member) = db.get_member(cid) {
            if member.groups.contains(&3) && liella_members.len() < 3 {
                liella_members.push(cid);
            }
        }
        if liella_members.len() >= 3 {
            break;
        }
    }
    
    assert!(liella_members.len() >= 3, "Should find 3+ Liella! members");
    
    // Add yelled cards
    for cid in liella_members {
        state.players[0].yell_cards.push(cid);
    }
    
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    
    // Check if condition passes
    let passes = crate::core::logic::interpreter::conditions::check_condition(
        &state,
        &db,
        0,
        &condition,
        &ctx,
        0
    );
    
    assert!(passes, "YELL_CARDS condition with 3+ unique Liella! members should pass");
}

#[test]
fn test_yell_cards_condition_insufficient() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    
    let condition = Condition {
        condition_type: ConditionType::None,
        value: 3,
        attr: 0,
        target_slot: 0,
        is_negated: false,
        params: serde_json::json!({
            "raw_cond": "YELL_CARDS",
            "FILTER": "GROUP_ID=3, UNIQUE_NAMES",
            "MIN": 3
        }),
    };
    
    // Add only 2 Liella! members
    let mut liella_members = Vec::new();
    for cid in 100..600 {
        if let Some(member) = db.get_member(cid) {
            if member.groups.contains(&3) && liella_members.len() < 2 {
                liella_members.push(cid);
            }
        }
        if liella_members.len() >= 2 {
            break;
        }
    }
    
    for cid in liella_members {
        state.players[0].yell_cards.push(cid);
    }
    
    let ctx = AbilityContext {
        player_id: 0,
        ..Default::default()
    };
    
    let passes = crate::core::logic::interpreter::conditions::check_condition(
        &state,
        &db,
        0,
        &condition,
        &ctx,
        0
    );
    
    assert!(!passes, "YELL_CARDS condition with only 2 unique Liella! members should fail");
}
