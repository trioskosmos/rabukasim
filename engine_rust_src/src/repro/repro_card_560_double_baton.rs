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
    
    // Look up real IDs from the database
    let eli_id = *db.card_no_to_id.get("PL!-sd1-002-SD").expect("Eli not found");
    let rin_id = *db.card_no_to_id.get("PL!-sd1-005-SD").expect("Rin not found");
    
    let eli = db.get_member(eli_id).expect("Eli member not in DB");
    let rin = db.get_member(rin_id).expect("Rin member not in DB");
    eprintln!("Eli: id={}, cost={}", eli_id, eli.cost);
    eprintln!("Rin: id={}, cost={}", rin_id, rin.cost);
    
    // Setup Stage for Player 0
    // Slot 0: Eli, Slot 1: Rin, Slot 2: Empty
    state.core.players[0].stage[0] = eli_id;
    state.core.players[0].stage[1] = rin_id;
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
    eprintln!("Standard cost slot 0 (replace Eli): {}", standard_cost_slot0);
    eprintln!("Standard cost slot 1 (replace Rin): {}", standard_cost_slot1);
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
    
    // Execute Double Baton: play Sumire to slot 0, also removing Rin from slot 1
    state.step(&db, double_baton_01).expect("Double Baton step failed");
    
    // Verifications:
    assert_eq!(state.core.players[0].stage[0], card_560_id, "Card 560 should be on Slot 0");
    assert_eq!(state.core.players[0].stage[1], -1, "Slot 1 should be empty after Double Baton");
    assert_eq!(state.core.players[0].baton_touch_count, 2, "baton_touch_count should be 2");
    
    // Expected cost = 22 - eli.cost - rin.cost = 22 - 2 - 2 = 18
    let expected_cost = (22 - eli.cost as i32 - rin.cost as i32).max(0) as usize;
    eprintln!("Expected tapped energy: {}", expected_cost);
    let tapped = state.core.players[0].tapped_energy_mask.count_ones() as usize;
    assert_eq!(tapped, expected_cost, "Should have tapped {} energy", expected_cost);
}
