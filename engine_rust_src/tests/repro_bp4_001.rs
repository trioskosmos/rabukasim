use engine_rust::core::logic::{GameState, resolve_bytecode, CardDatabase, AbilityContext};
use engine_rust::core::enums::{Phase};

#[test]
fn test_card_557_logic_repro() {
    let mut state = GameState::default();
    state.debug.debug_mode = true;
    let json_content = std::fs::read_to_string("../data/cards_compiled.json").expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    
    let p1 = 0;
    // PL!SP-bp4-001-P is ID 557
    let card_id = 557; 
    
    // 1. Setup Stage with Liella! (Group ID 3)
    // We'll put Kanon (557) in Slot 0. She is Liella!.
    state.players[p1].stage[0] = card_id;
    state.players[p1].stage[1] = -1;
    state.players[p1].stage[2] = -1;
    
    // 2. Setup Energy (7 cards)
    for i in 0..7 {
        state.players[p1].energy_zone.push(1000 + i); 
    }
    
    // 3. Ensure Energy Deck is not empty
    state.players[p1].energy_deck.push(9999);
    
    // 4. Context for OnPlay
    let ctx = AbilityContext {
        player_id: p1 as u8,
        source_card_id: card_id,
        area_idx: 0,
        ..Default::default()
    };
    
    // 5. Get ability 0 bytecode
    let member = db.get_member(card_id).expect("Card 557 not found");
    let bytecode = &member.abilities[0].bytecode;
    
    println!("Bytecode: {:?}", bytecode);
    
    // 6. Execute
    resolve_bytecode(&mut state, &db, bytecode, &ctx);
    
    // 7. Verification
    // Success: Energy zone should have 8 cards, and the last one should be tapped (wait state).
    assert_eq!(state.players[p1].energy_zone.len(), 8, "Should have charged 1 energy");
    assert!(state.players[p1].is_energy_tapped(7), "New energy should be in WAIT (tapped) state");
    
    println!("Test passed: Energy charged and tapped.");
}

#[test]
fn test_card_557_logic_fail_if_not_only_liella() {
    let mut state = GameState::default();
    state.debug.debug_mode = true;
    let json_content = std::fs::read_to_string("../data/cards_compiled.json").expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    
    let p1 = 0;
    let card_id = 557; 
    
    // Kanon (557) is Liella!. (Group ID 3)
    // Card 143 is Honoka (Muse - Group ID 1)
    state.players[p1].stage[0] = card_id;
    state.players[p1].stage[1] = 143; 
    
    for i in 0..7 {
        state.players[p1].energy_zone.push(1000 + i); 
    }
    state.players[p1].energy_deck.push(9999);
    
    let ctx = AbilityContext {
        player_id: p1 as u8,
        source_card_id: card_id,
        area_idx: 0,
        ..Default::default()
    };
    
    let member = db.get_member(card_id).unwrap();
    let bytecode = &member.abilities[0].bytecode;
    
    resolve_bytecode(&mut state, &db, bytecode, &ctx);
    
    // Should NOT have charged energy because ALL_MEMBERS condition failed
    assert_eq!(state.players[p1].energy_zone.len(), 7, "Should NOT have charged energy (mixed groups)");
}
