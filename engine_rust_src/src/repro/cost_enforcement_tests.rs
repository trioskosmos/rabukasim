//! Cost Enforcement Tests - Verify that ACTIVATED abilities actually require costs
//!
//! These tests ensure that:
//! 1. Abilities with costs cannot be activated without paying the cost
//! 2. The cost inference system properly adds cost frames to consolidated_abilities.json
//! 3. Ruby card 423 (and similar cards) now requires self-sacrifice before recovering live

use crate::core::logic::CardDatabase;
use crate::test_helpers::{create_test_db, create_test_state, load_real_db, clear_real_db_cache};

/// Test that Ruby card 423 requires self-sacrifice cost to activate
/// Before fix: Ability could be activated for free (just RECOVER_LIVE)
/// After fix: Ability requires MOVE_TO_DISCARD (self-sacrifice) before effect
#[test]
fn test_ruby_423_requires_self_sacrifice() {
    clear_real_db_cache();
    let db = load_real_db();
    let mut state = create_test_state();
    
    // Setup: Player 0 has Ruby on stage slot 0, with a live card in discard
    let p_idx = 0;
    state.players[p_idx].stage[0] = 423; // Ruby card ID
    state.players[p_idx].discard.push(100); // Some live card
    
    // Get Ruby's ability
    let ruby_card = db.get_member(423).expect("Ruby card should exist");
    let ability = ruby_card.abilities.get(0).expect("Ruby should have an ability");
    
    // DEBUG: Print what we actually have
    eprintln!("DEBUG: Ruby card_no = {}", ruby_card.card_no);
    eprintln!("DEBUG: Ability frame_program = {:?}", ability.frame_program.as_ref().map(|fp| fp.frames.len()));
    if let Some(fp) = &ability.frame_program {
        for (i, frame) in fp.frames.iter().enumerate() {
            eprintln!("DEBUG: Frame {}: opcode = {}", i, frame.opcode());
        }
    }
    eprintln!("DEBUG: Ability costs count = {}", ability.costs.len());
    
    // Verify the ability is ACTIVATED
    assert_eq!(ability.trigger, crate::core::enums::TriggerType::Activated, 
               "Ruby's ability should be ACTIVATED");
    
    // Check that the ability has cost frames (either in costs or frame_program)
    let has_cost = !ability.costs.is_empty() || 
                   ability.frame_program.as_ref().map_or(false, |fp| {
                       fp.frames.iter().any(|f| {
                           let op = f.opcode();
                           op == crate::core::logic::constants::O_MOVE_TO_DISCARD ||
                           op == crate::core::logic::constants::O_SET_TAPPED ||
                           op == crate::core::logic::constants::O_PAY_ENERGY
                       })
                   });
    
    // This should fail before the fix - Ruby's ability had no cost
    assert!(has_cost, 
            "Ruby card 423 ACTIVATED ability should have a cost (self-sacrifice). \
             This ensures the cost inference system is working.");
}

/// Test that abilities without cost frames are flagged during compilation
#[test]
fn test_activated_abilities_must_have_costs() {
    let db = CardDatabase::default();
    
    // Collect all ACTIVATED abilities that are missing costs
    let mut missing_costs: Vec<(i32, String)> = Vec::new();
    
    for (card_id, member) in db.members.iter() {
        for (idx, ability) in member.abilities.iter().enumerate() {
            if ability.trigger != crate::core::enums::TriggerType::Activated {
                continue;
            }
            
            // Check for cost frames
            let has_cost = !ability.costs.is_empty() ||
                           ability.frame_program.as_ref().map_or(false, |fp| {
                               fp.frames.iter().any(|f| {
                                   let op = f.opcode();
                                   op == crate::core::logic::constants::O_MOVE_TO_DISCARD ||
                                   op == crate::core::logic::constants::O_SET_TAPPED ||
                                   op == crate::core::logic::constants::O_PAY_ENERGY ||
                                   op == crate::core::logic::constants::O_TAP_MEMBER
                               })
                           });
            
            if !has_cost {
                missing_costs.push((*card_id, format!("ability {}", idx)));
            }
        }
    }
    
    // We expect 0 missing costs after the fix
    // If this fails, it means the cost inference didn't work for some cards
    assert!(missing_costs.is_empty(), 
            "Found {} ACTIVATED abilities without cost frames: {:?}. \
             All ACTIVATED abilities must have costs enforced. \
             Run the cost inference pipeline to fix.", 
            missing_costs.len(), missing_costs);
}

/// Test that cost frames are properly ordered (cost before effect)
#[test]
fn test_cost_frames_come_before_effects() {
    let db = CardDatabase::default();
    
    for (card_id, member) in db.members.iter() {
        for ability in member.abilities.iter() {
            if ability.trigger != crate::core::enums::TriggerType::Activated {
                continue;
            }
            
            if let Some(fp) = &ability.frame_program {
                let frames = &fp.frames;
                
                // Find first cost frame and first non-cost effect frame
                let first_cost_idx = frames.iter().position(|f| {
                    let op = f.opcode();
                    op == crate::core::logic::constants::O_MOVE_TO_DISCARD ||
                    op == crate::core::logic::constants::O_SET_TAPPED ||
                    op == crate::core::logic::constants::O_PAY_ENERGY
                });
                
                let first_effect_idx = frames.iter().position(|f| {
                    let op = f.opcode();
                    op != crate::core::logic::constants::O_RETURN &&
                    op != crate::core::logic::constants::O_MOVE_TO_DISCARD &&
                    op != crate::core::logic::constants::O_SET_TAPPED &&
                    op != crate::core::logic::constants::O_PAY_ENERGY
                });
                
                // If both exist, cost must come before effect
                if let (Some(cost_idx), Some(effect_idx)) = (first_cost_idx, first_effect_idx) {
                    assert!(cost_idx < effect_idx,
                            "Card {}: Cost frame must come before effect frame. \
                             Cost at index {}, effect at index {}",
                            card_id, cost_idx, effect_idx);
                }
            }
        }
    }
}

/// Regression test for Ruby 423 specifically - verify the exact frame sequence
#[test]
fn test_ruby_423_frame_sequence() {
    let db = create_test_db();
    
    let ruby = db.get_member(423).expect("Ruby card should exist");
    let ability = ruby.abilities.get(0).expect("Ruby should have an ability");
    
    let fp = ability.frame_program.as_ref()
        .expect("Ruby ability should have frame_program");
    
    let ops: Vec<i32> = fp.frames.iter().map(|f| f.opcode()).collect();
    
    // Expected sequence after fix:
    // 1. MOVE_TO_DISCARD (cost - self-sacrifice)
    // 2. RECOVER_LIVE (effect)
    // 3. RETURN
    
    assert!(!ops.is_empty(), "Ruby ability should have frames");
    
    // Check that MOVE_TO_DISCARD appears before RECOVER_LIVE
    let discard_idx = ops.iter().position(|&op| op == crate::core::logic::constants::O_MOVE_TO_DISCARD);
    let recover_idx = ops.iter().position(|&op| op == crate::core::logic::constants::O_RECOVER_LIVE);
    
    assert!(discard_idx.is_some(), 
            "Ruby 423 should have MOVE_TO_DISCARD cost frame");
    assert!(recover_idx.is_some(), 
            "Ruby 423 should have RECOVER_LIVE effect frame");
    
    assert!(discard_idx.unwrap() < recover_idx.unwrap(),
            "Cost (MOVE_TO_DISCARD) must come before effect (RECOVER_LIVE)");
}
