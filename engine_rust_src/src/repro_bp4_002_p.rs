use crate::core::logic::*;
// Redundant import removed
use crate::test_helpers::{load_real_db, create_test_state, TestUtils};

#[test]
fn test_repro_bp4_002_p_wait_flow() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = false;
    
    // Card ID for PL!SP-bp4-002-P is 558
    let card_id = 558;
    
    // 1. Setup State: P0 has the card in hand
    state.core.players[0].hand = vec![card_id].into();
    state.core.players[0].deck = vec![101, 102, 103, 104].into(); 
    
    // Give enough energy just in case
    state.core.players[0].energy_zone = vec![40001, 40002, 40003, 40004, 40005].into();
    
    // 2. Play the card to slot 0
    state.phase = Phase::Main;
    state.current_player = 0;
    
    println!("--- INIT STATE ---");
    state.dump();
    
    // Action ID for PLAY card 0 to slot 0 is 1000
    println!("--- ACTION: Playing Card {} to Slot 0 ---", card_id);
    let res = state.step(&db, 1000);
    if let Err(e) = res {
        panic!("Step 1 (Play) failed: {}", e);
    }
    
    println!("--- STATE AFTER PLAY ---");
    state.dump();
    println!("Rule Log: {:?}", state.ui.rule_log);
    println!("Trigger Queue Depth: {}", state.trigger_queue.len());
    println!("Interaction Stack Depth: {}", state.interaction_stack.len());
    
    assert_eq!(state.core.players[0].stage[0], card_id, "Card should be on stage slot 0");
    
    // 3. The card triggers ON_PLAY ability.
    assert_eq!(state.phase, Phase::Response, "Should have entered Response phase for optional TAP_MEMBER. Got: {:?}", state.phase);
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, "OPTIONAL", "Interaction should be OPTIONAL (Wait or not)");
    
    // 4. Choose "Yes" (WAIT) -> choice_index 0
    println!("--- ACTION: Choosing YES (WAIT) ---");
    let res = state.step(&db, 8000);
    if let Err(e) = res {
        panic!("Step 3 (Choice Yes) failed: {}", e);
    }
    
    state.dump();
    
    // 5. Verify the card is TAPPED (WAIT state)
    assert!(state.core.players[0].is_tapped(0), "Card in slot 0 should be tapped after choosing to WAIT");
    
    // 6. Verify it proceeds to LOOK_AND_CHOOSE
    println!("--- AFTER WAIT CHOICE ---");
    assert_eq!(state.phase, Phase::Response, "Should still be in Response phase for LOOK_AND_CHOOSE");
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, "LOOK_AND_CHOOSE", "Interaction should be LOOK_AND_CHOOSE");
    
    println!("SUCCESS: WAIT mechanic and ability flow verified for PL!SP-bp4-002-P");
}
