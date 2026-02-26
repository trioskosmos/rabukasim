/// Reproduction test for PL!SP-bp4-001-P (Card 557)
/// Issue: ALL_MEMBERS condition doesn't activate correctly when baton passed from non-Liella!
/// 
/// Expected behavior:
/// - When Kanon (Liella!) baton passes a non-Liella! member, the stage should only have Liella! members
/// - The ALL_MEMBERS {FILTER="GROUP_ID=3"} condition should pass
/// - Energy charge effect should activate

use engine_rust::core::logic::{GameState, CardDatabase, AbilityContext};

/// Test the actual game flow with baton pass
#[test]
fn test_card_557_baton_pass_from_non_liella() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json").expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    let mut state = GameState::default();
    state.debug.debug_mode = true;
    
    let p1 = 0;
    
    // Card IDs
    let kanon_id = 557;  // PL!SP-bp4-001-P (Liella! - Group 3)
    let honoka_id = 143; // Non-Liella! (Muse - Group 1) - need to verify
    
    // Verify group IDs
    let kanon = db.get_member(kanon_id).expect("Kanon not found");
    let honoka = db.get_member(honoka_id).expect("Honoka not found");
    
    println!("Kanon groups: {:?}", kanon.groups);
    println!("Honoka groups: {:?}", honoka.groups);
    
    // Setup: Honoka is on stage in slot 0
    state.core.players[p1].stage[0] = honoka_id;
    state.core.players[p1].stage[1] = -1;
    state.core.players[p1].stage[2] = -1;
    
    // Setup energy (7+ required)
    for i in 0..7 {
        state.core.players[p1].energy_zone.push(1000 + i);
    }
    state.core.players[p1].energy_deck.push(9999);
    
    // Put Kanon in hand
    state.core.players[p1].hand.push(kanon_id);
    
    // Execute baton pass: Play Kanon to slot 0, replacing Honoka
    // This should:
    // 1. Remove Honoka from stage (to discard)
    // 2. Place Kanon on stage
    // 3. Trigger OnPlay for Kanon
    // 4. Check ALL_MEMBERS condition - should pass since only Kanon (Liella!) is on stage
    
    let result = state.play_member(&db, 0, 0); // hand_idx=0, slot_idx=0
    
    println!("Play result: {:?}", result);
    println!("Stage after play: {:?}", state.core.players[p1].stage);
    println!("Discard after play: {:?}", state.core.players[p1].discard);
    println!("Energy zone count: {}", state.core.players[p1].energy_zone.len());
    println!("Baton touch count: {}", state.core.players[p1].baton_touch_count);
    
    // Verify baton pass happened
    assert!(result.is_ok(), "Play should succeed");
    assert_eq!(state.core.players[p1].stage[0], kanon_id, "Kanon should be on stage");
    assert!(state.core.players[p1].discard.contains(&honoka_id), "Honoka should be in discard");
    
    // The key assertion: Energy should have been charged
    // because after baton pass, only Liella! (Kanon) is on stage
    assert_eq!(state.core.players[p1].energy_zone.len(), 8, 
        "Should have charged 1 energy - ALL_MEMBERS condition should pass after baton pass from non-Liella!");
}

/// Test direct bytecode execution to isolate the condition check
#[test]
fn test_card_557_condition_check_direct() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json").expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    let mut state = GameState::default();
    state.debug.debug_mode = true;
    
    let p1 = 0;
    let kanon_id = 557;
    
    // Setup: Only Kanon on stage (simulating post-baton-pass state)
    state.core.players[p1].stage[0] = kanon_id;
    state.core.players[p1].stage[1] = -1;
    state.core.players[p1].stage[2] = -1;
    
    // Setup energy
    for i in 0..7 {
        state.core.players[p1].energy_zone.push(1000 + i);
    }
    state.core.players[p1].energy_deck.push(9999);
    
    // Get bytecode
    let member = db.get_member(kanon_id).unwrap();
    let bytecode = &member.abilities[0].bytecode;
    println!("Bytecode: {:?}", bytecode);
    
    // Execute
    let ctx = AbilityContext {
        player_id: p1 as u8,
        source_card_id: kanon_id,
        area_idx: 0,
        ..Default::default()
    };
    
    state.resolve_bytecode(&db, bytecode, &ctx);
    
    // Should succeed - only Liella! on stage
    assert_eq!(state.core.players[p1].energy_zone.len(), 8, 
        "Should have charged energy when only Liella! is on stage");
}

/// Test that condition fails when mixed groups are on stage
#[test]
fn test_card_557_condition_fails_with_mixed_groups() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json").expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    let mut state = GameState::default();
    state.debug.debug_mode = true;
    
    let p1 = 0;
    let kanon_id = 557;  // Liella!
    let honoka_id = 143; // Muse (non-Liella!)
    
    // Setup: Both Kanon and Honoka on stage
    state.core.players[p1].stage[0] = kanon_id;
    state.core.players[p1].stage[1] = honoka_id;
    state.core.players[p1].stage[2] = -1;
    
    // Setup energy
    for i in 0..7 {
        state.core.players[p1].energy_zone.push(1000 + i);
    }
    state.core.players[p1].energy_deck.push(9999);
    
    // Get bytecode
    let member = db.get_member(kanon_id).unwrap();
    let bytecode = &member.abilities[0].bytecode;
    
    // Execute
    let ctx = AbilityContext {
        player_id: p1 as u8,
        source_card_id: kanon_id,
        area_idx: 0,
        ..Default::default()
    };
    
    state.resolve_bytecode(&db, bytecode, &ctx);
    
    // Should fail - mixed groups on stage
    assert_eq!(state.core.players[p1].energy_zone.len(), 7, 
        "Should NOT have charged energy when mixed groups are on stage");
}
