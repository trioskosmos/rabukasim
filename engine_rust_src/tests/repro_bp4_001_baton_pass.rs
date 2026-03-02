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
    let kanon_id = 557;  // Liella!
    let honoka_id = 143; // Non-Liella!

    // Setup: Honoka is on stage in slot 1 (Center)
    state.core.players[p1].stage[0] = -1;
    state.core.players[p1].stage[1] = honoka_id;
    state.core.players[p1].stage[2] = -1;

    // Setup energy (7+ required)
    for i in 0..7 {
        state.core.players[p1].energy_zone.push(1000 + i);
    }
    state.core.players[p1].energy_deck.push(9999);

    // Add a dummy deck card to prevent automatic deck refresh
    state.core.players[p1].deck.push(1);

    // Put Kanon in hand (index 0)
    state.core.players[p1].hand.push(kanon_id);

    // Execute baton pass: Play Kanon to slot 1, replacing Honoka
    let result = state.play_member(&db, 0, 1);

    // Manually process the trigger queue to resolve OnPlay abilities
    state.process_trigger_queue(&db);

    assert!(result.is_ok(), "Play should succeed");
    assert_eq!(state.core.players[p1].stage[1], kanon_id, "Kanon should be on stage slot 1");
    assert_eq!(state.core.players[p1].discard.len(), 1, "Honoka should be in discard");

    // The key assertion: Energy should have been charged (+1)
    assert_eq!(state.core.players[p1].energy_zone.len(), 8,
        "ALL_MEMBERS condition should pass after baton pass removes Honoka, charging 1 energy");
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

    state.resolve_bytecode_cref(&db, bytecode, &ctx);

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

    state.resolve_bytecode_cref(&db, bytecode, &ctx);

    // Should fail - mixed groups on stage
    assert_eq!(state.core.players[p1].energy_zone.len(), 7,
        "Should NOT have charged energy when mixed groups are on stage");
}
