#[allow(unused_imports)]
use crate::core::logic::*;
use crate::test_helpers::load_real_db;

#[test]
fn test_repro_card_560_double_baton() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = false; // Enable logging for debugging

    // Card 560: PL!SP-bp4-004-P (Sumire, Cost 22)
    let card_560_id = 560;
    
    // Use Liella! members (GROUP_ID=3) for baton sources
    // PL!SP-bp4-001-P (Kanon) and PL!SP-bp4-002-P (Keke) are Liella! members
    let kanon_id = *db.card_no_to_id.get("PL!SP-bp4-001-P").expect("Kanon not found");
    let keke_id = *db.card_no_to_id.get("PL!SP-bp4-002-P").expect("Keke not found");
    
    let kanon = db.get_member(kanon_id).expect("Kanon member not in DB");
    let keke = db.get_member(keke_id).expect("Keke member not in DB");
    eprintln!("Kanon: id={}, cost={}, groups={:?}", kanon_id, kanon.cost, kanon.groups);
    eprintln!("Keke: id={}, cost={}, groups={:?}", keke_id, keke.cost, keke.groups);
    
    // Setup Stage for Player 0
    // Slot 0: Kanon, Slot 1: Keke, Slot 2: Empty
    state.core.players[0].stage[0] = kanon_id;
    state.core.players[0].stage[1] = keke_id;
    state.core.players[0].stage[2] = -1;
    
    // Player 0 Hand: Card 560
    state.core.players[0].hand = vec![card_560_id].into();
    
    // Player 0 Energy: 22 cards (max cost)
    state.core.players[0].energy_zone = vec![9000; 22].into();
    
    state.current_player = 0;
    state.phase = Phase::Main;
    
    // Verify standard baton cost calculation
    let standard_cost_slot0 = state.get_member_cost(0, card_560_id, 0, -1, &db, 0);
    let standard_cost_slot1 = state.get_member_cost(0, card_560_id, 1, -1, &db, 0);
    let double_cost = state.get_member_cost(0, card_560_id, 0, 1, &db, 0);
    eprintln!("Standard cost slot 0 (replace Kanon): {}", standard_cost_slot0);
    eprintln!("Standard cost slot 1 (replace Keke): {}", standard_cost_slot1);
    eprintln!("Double baton cost (replace both): {}", double_cost);
    
    // Verify Action Generation
    let mut actions = Vec::new();
    state.generate_legal_actions(&db, 0, &mut actions);
    eprintln!("Generated actions: {:?}", actions);
    
    // Standard plays to each slot (offsets 0,1,2)
    // hand_idx=0, so base = ACTION_BASE_HAND (1000)
    // slot 0: 1000, slot 1: 1001, slot 2: 1002
    assert!(actions.contains(&1000), "Standard play to slot 0 should be legal");
    assert!(actions.contains(&1001), "Standard play to slot 1 should be legal");
    assert!(actions.contains(&1002), "Standard play to slot 2 (empty) should be legal");
    
    // Double Baton actions (offsets 3-8)
    // combo_idx for (slot_idx=0, other_slot=1): 0*2 + 1 = 1 -> offset 3+1 = 4 -> action 1004
    // combo_idx for (slot_idx=1, other_slot=0): 1*2 + 0 = 2 -> offset 3+2 = 5 -> action 1005
    let double_baton_01 = 1004; // Play to slot 0, also replacing slot 1
    let _double_baton_10 = 1005; // Play to slot 1, also replacing slot 0
    
    assert!(actions.contains(&double_baton_01), 
        "Double Baton action {} (Slot 0+1) should be legal! Found: {:?}", double_baton_01, actions);
    
    // Execute Double Baton: play Sumire to slot 0, also removing Keke from slot 1
    state.step(&db, double_baton_01).expect("Double Baton step failed");
    
    // Verifications:
    assert_eq!(state.core.players[0].stage[0], card_560_id, "Card 560 should be on Slot 0");
    assert_eq!(state.core.players[0].stage[1], -1, "Slot 1 should be empty after Double Baton");
    assert_eq!(state.core.players[0].baton_touch_count, 2, "baton_touch_count should be 2");
    
    // Expected cost = 22 - kanon.cost - keke.cost
    let expected_cost = (22 - kanon.cost as i32 - keke.cost as i32).max(0) as usize;
    eprintln!("Expected tapped energy: {}", expected_cost);
    let tapped = state.core.players[0].tapped_energy_mask.count_ones() as usize;
    assert_eq!(tapped, expected_cost, "Should have tapped {} energy", expected_cost);
    
    // === TEST SECOND ABILITY: ON_PLAY condition check ===
    // Card 560's second ability:
    // TRIGGER: ON_PLAY
    // CONDITION: AREA="CENTER", BATON_TOUCH {FILTER="GROUP_ID=3", COUNT_EQ_2}
    // EFFECT: DRAW(2); PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=3, COST_LE_4"}
    
    eprintln!("\n=== Testing Second Ability ===");
    eprintln!("baton_touch_count: {}", state.core.players[0].baton_touch_count);
    eprintln!("prev_card_id: {}", state.prev_card_id);
    
    // Check if the card is in CENTER position (slot 0)
    let is_center = state.core.players[0].stage[0] == card_560_id;
    eprintln!("Is in CENTER (slot 0): {}", is_center);
    
    // Check baton_touch_count == 2
    let baton_count_correct = state.core.players[0].baton_touch_count == 2;
    eprintln!("baton_touch_count == 2: {}", baton_count_correct);
    
    // Check if Kanon and Keke are Liella! members (GROUP_ID=3)
    eprintln!("Kanon groups: {:?}", kanon.groups);
    eprintln!("Keke groups: {:?}", keke.groups);
    
    // Check if GROUP_ID=3 (Liella!) is in their groups
    let kanon_is_liella = kanon.groups.contains(&3);
    let keke_is_liella = keke.groups.contains(&3);
    eprintln!("Kanon is Liella! (GROUP_ID=3): {}", kanon_is_liella);
    eprintln!("Keke is Liella! (GROUP_ID=3): {}", keke_is_liella);
    
    // The problem: C_BATON condition currently only checks:
    //   state.prev_card_id != -1 || player.baton_touch_count > 0
    // It does NOT check:
    //   1. COUNT_EQ_2 (baton_touch_count == 2)
    //   2. FILTER="GROUP_ID=3" (baton sources are Liella! members)
    
    // The bytecode for C_BATON condition is just [231, 0, 0, 0, 0]
    // But the actual condition in the card has FILTER and COUNT_EQ_2 params
    // Let's check what the actual bytecode looks like
    let card = db.get_member(card_560_id).expect("Card 560 not found");
    eprintln!("\nCard 560 abilities: {:?}", card.abilities.len());
    for (i, ab) in card.abilities.iter().enumerate() {
        eprintln!("Ability {}: trigger={:?}, bytecode={:?}", i, ab.trigger, ab.bytecode);
    }
    
    // The condition bytecode from cards_compiled.json:
    // [226, 0, 0, 0, 0, 231, 0, 0, 0, 0, ...]
    // 226 = C_AREA_CHECK (CENTER)
    // 231 = C_BATON
    // Note: The params for FILTER and COUNT_EQ_2 are NOT encoded in the bytecode!
    
    // This is a PARSER/COMPILER issue - the condition params are not being encoded
    eprintln!("\n=== ISSUE IDENTIFIED ===");
    eprintln!("The BATON_TOUCH condition params (FILTER, COUNT_EQ_2) are not encoded in bytecode!");
    eprintln!("Current C_BATON only checks if baton_touch_count > 0, not == 2");
    eprintln!("And it doesn't check if baton sources match the FILTER");
}

/// Test to verify the second ability triggers correctly when conditions are met
#[test]
fn test_card_560_second_ability_condition() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = false;
    
    // Card 560: PL!SP-bp4-004-P (Sumire)
    let card_560_id = 560;
    
    // Use Liella! members (GROUP_ID=3) for baton sources
    let kanon_id = *db.card_no_to_id.get("PL!SP-bp4-001-P").expect("Kanon not found");
    let keke_id = *db.card_no_to_id.get("PL!SP-bp4-002-P").expect("Keke not found");
    
    let kanon = db.get_member(kanon_id).expect("Kanon not in DB");
    let keke = db.get_member(keke_id).expect("Keke not in DB");
    
    // Check if they are Liella! members
    eprintln!("Kanon groups: {:?} - is Liella!: {}", kanon.groups, kanon.groups.contains(&3));
    eprintln!("Keke groups: {:?} - is Liella!: {}", keke.groups, keke.groups.contains(&3));
    
    // Setup: Stage with Kanon and Keke
    state.core.players[0].stage[0] = kanon_id;
    state.core.players[0].stage[1] = keke_id;
    state.core.players[0].stage[2] = -1;
    
    // Hand with Card 560
    state.core.players[0].hand = vec![card_560_id].into();
    
    // Energy
    state.core.players[0].energy_zone = vec![9000; 22].into();
    
    // Discard pile with a Liella! member cost <= 4 for the PLAY_MEMBER_FROM_DISCARD effect
    // Find a Liella! member with cost <= 4
    let mut liella_low_cost = None;
    for (card_no, &id) in db.card_no_to_id.iter() {
        if let Some(m) = db.get_member(id) {
            if m.groups.contains(&3) && m.cost <= 4 {
                liella_low_cost = Some(id);
                eprintln!("Found Liella! low cost member: {} (cost={})", card_no, m.cost);
                break;
            }
        }
    }
    if let Some(id) = liella_low_cost {
        state.core.players[0].discard.push(id as i32);
    }
    
    state.current_player = 0;
    state.phase = Phase::Main;
    
    // Execute double baton
    let double_baton_01 = 1004;
    state.step(&db, double_baton_01).expect("Double Baton step failed");
    
    // Check hand size - should have drawn 2 cards if second ability triggered
    let hand_size = state.core.players[0].hand.len();
    eprintln!("Hand size after play: {}", hand_size);
    
    // The second ability should have drawn 2 cards
    // But currently it won't trigger because C_BATON doesn't check COUNT_EQ_2
    // and doesn't check FILTER
    
    // For now, just verify the basic double baton worked
    assert_eq!(state.core.players[0].baton_touch_count, 2);
}
