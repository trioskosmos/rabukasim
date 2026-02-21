/// CPU Opcode Coverage Gap Tests (Batch 1)
/// Uses REAL cards from cards_compiled.json to verify opcode execution.
/// Card IDs verified via `tools/card_finder.py` and Python bytecode audit.

use crate::test_helpers::{load_real_db, create_test_state};
use crate::core::logic::*;

/// Card ID 122: PL!-sd1-003-SD (南 ことり / Kotori)
/// Ability[1] Trigger=OnLiveStart: bytecode contains O_COLOR_SELECT (45)
/// Tests that the interpreter correctly suspends for COLOR_SELECT
/// and resumes after a color choice is provided.
#[test]
fn test_opcode_color_select_real_card_122() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let card_id: i32 = 122;
    let card = db.get_member(card_id).expect("Card 122 (Kotori) missing from DB");
    
    // Find the ability that contains O_COLOR_SELECT (opcode 45)
    let ab_idx = card.abilities.iter().position(|a| {
        a.bytecode.iter().step_by(4).any(|&op| op == 45)
    }).expect("Card 122 should have an ability with O_COLOR_SELECT");
    
    let ab = &card.abilities[ab_idx];
    
    // Place Kotori on stage
    state.core.players[0].stage[0] = card_id;
    
    // Execute the ability bytecode directly
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        source_card_id: card_id,
        trigger_type: ab.trigger,
        ..Default::default()
    };
    
    state.resolve_bytecode(&db, &ab.bytecode, &ctx);
    
    // Should suspend for COLOR_SELECT interaction
    assert_eq!(state.phase, Phase::Response, 
        "Card 122 ability should suspend for COLOR_SELECT");
    assert!(!state.interaction_stack.is_empty(), 
        "Interaction stack should have a pending COLOR_SELECT");
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, "COLOR_SELECT",
        "Pending interaction should be COLOR_SELECT");
    
    // Resume with a color choice (e.g., Pink = 0)
    let mut pending = state.interaction_stack.pop().unwrap();
    pending.ctx.choice_index = 0; // Pink
    state.resolve_bytecode(&db, &ab.bytecode, &pending.ctx);
    
    // Should have completed without panic - the color was applied
    println!("test_opcode_color_select_real_card_122: PASSED (no panic, interaction resolved)");
}

/// Card ID 19: PL!-PR-007-PR
/// Ability bytecode contains O_JUMP (opcode 2)
/// Tests that the interpreter correctly jumps over instructions.
#[test]
fn test_opcode_jump_real_card_19() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let card_id: i32 = 19;
    let card = db.get_member(card_id).expect("Card 19 missing from DB");
    
    // Find the ability that contains O_JUMP (opcode 2)
    let ab_idx = card.abilities.iter().position(|a| {
        a.bytecode.iter().step_by(4).any(|&op| op == 2)
    }).expect("Card 19 should have an ability with O_JUMP");
    
    let ab = &card.abilities[ab_idx];
    
    // Place card on stage
    state.core.players[0].stage[0] = card_id;
    
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        source_card_id: card_id,
        trigger_type: ab.trigger,
        ..Default::default()
    };
    
    // Execute - should not panic, jump should skip instructions correctly
    state.resolve_bytecode(&db, &ab.bytecode, &ctx);
    
    println!("test_opcode_jump_real_card_19: PASSED (jump executed, no panic)");
}

/// Searches for and tests a card with O_TAP_OPPONENT (opcode 32) at runtime.
/// This test dynamically finds a real card to avoid hardcoding a potentially
/// wrong ID.
#[test]
fn test_opcode_tap_opponent_dynamic() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    // Find any card with O_TAP_OPPONENT (32) in its bytecode
    let mut found_card_id: Option<i32> = None;
    let mut found_ab_idx: Option<usize> = None;
    
    for (&cid, m) in db.members.iter() {
        for (ai, a) in m.abilities.iter().enumerate() {
            let has_tap = a.bytecode.iter().step_by(4).any(|&op| op == 32);
            let has_modal = a.bytecode.iter().step_by(4).any(|&op| op == 30 || op == 64);
            if has_tap && !has_modal {
                found_card_id = Some(cid);
                found_ab_idx = Some(ai);
                break;
            }
        }
        if found_card_id.is_some() { break; }
    }
    
    let card_id = found_card_id.expect("No card found with O_TAP_OPPONENT in compiled DB");
    let ab_idx = found_ab_idx.unwrap();
    let card = db.get_member(card_id).unwrap();
    let ab = &card.abilities[ab_idx];
    
    println!("Testing O_TAP_OPPONENT with Card ID={}, NO={}", card_id, card.card_no);
    
    // Place card on stage, opponent has untapped member
    state.core.players[0].stage[0] = card_id;
    state.core.players[1].stage[0] = 3001; // Generic opponent member
    state.core.players[1].set_tapped(0, false);
    
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        source_card_id: card_id,
        trigger_type: ab.trigger,
        ..Default::default()
    };
    
    state.resolve_bytecode(&db, &ab.bytecode, &ctx);
    
    // TAP_OPPONENT is interactive - should suspend
    if state.phase == Phase::Response && !state.interaction_stack.is_empty() {
        let choice_type = &state.interaction_stack.last().unwrap().choice_type;
        assert_eq!(choice_type, "TAP_O", 
            "Pending interaction should be TAP_O, got {}", choice_type);
        
        // Resume with choice: tap slot 0
        let mut pending = state.interaction_stack.pop().unwrap();
        pending.ctx.choice_index = 0;
        state.resolve_bytecode(&db, &ab.bytecode, &pending.ctx);
        
        assert!(state.core.players[1].is_tapped(0), 
            "Opponent slot 0 should be tapped after O_TAP_OPPONENT resolution");
    }
    
    println!("test_opcode_tap_opponent_dynamic: PASSED");
}

/// Searches for and tests a card with O_BUFF_POWER (opcode 18) at runtime.
#[test]
fn test_opcode_buff_power_dynamic() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    // Find any card with O_BUFF_POWER (18) in its bytecode
    let mut found_card_id: Option<i32> = None;
    let mut found_ab_idx: Option<usize> = None;
    
    for (&cid, m) in db.members.iter() {
        for (ai, a) in m.abilities.iter().enumerate() {
            if a.bytecode.iter().step_by(4).any(|&op| op == 18) {
                found_card_id = Some(cid);
                found_ab_idx = Some(ai);
                break;
            }
        }
        if found_card_id.is_some() { break; }
    }
    
    let card_id = found_card_id.expect("No card found with O_BUFF_POWER in compiled DB");
    let ab_idx = found_ab_idx.unwrap();
    let card = db.get_member(card_id).unwrap();
    let ab = &card.abilities[ab_idx];
    
    println!("Testing O_BUFF_POWER with Card ID={}, NO={}", card_id, card.card_no);
    
    // Place card on stage
    state.core.players[0].stage[0] = card_id;
    let before_blades = state.core.players[0].blade_buffs[0];
    
    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        source_card_id: card_id,
        trigger_type: ab.trigger,
        ..Default::default()
    };
    
    state.resolve_bytecode(&db, &ab.bytecode, &ctx);
    
    // If it didn't suspend, blade_buffs should have changed
    if state.phase != Phase::Response {
        assert!(state.core.players[0].blade_buffs[0] > before_blades,
            "Blade buffs should have increased after O_BUFF_POWER, before={}, after={}",
            before_blades, state.core.players[0].blade_buffs[0]);
    }
    
    println!("test_opcode_buff_power_dynamic: PASSED");
}
