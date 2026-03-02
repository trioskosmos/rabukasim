use crate::core::logic::*;
use crate::core::generated_constants::ACTION_BASE_CHOICE;
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
    // Satisfy SUM_HEART_TOTAL_GE=8 condition for card 558
    state.core.players[0].heart_buffs[0].add_to_color(2, 8); // 8 Yellow hearts on slot 0
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
    // The ability has an optional TAP_MEMBER cost followed by LOOK_AND_CHOOSE
    // The engine may process this differently - check what we actually have
    assert_eq!(state.phase, Phase::Response, "Should have entered Response phase for ability. Got: {:?}", state.phase);

    // Check the interaction type - it could be OPTIONAL or LOOK_AND_CHOOSE depending on engine flow
    let interaction = state.interaction_stack.last().unwrap();
    println!("DEBUG: Interaction type: {}", interaction.choice_type);

    // The interaction should be either OPTIONAL (for tap) or LOOK_AND_CHOOSE (if optional was auto-skipped)
    assert!(
        interaction.choice_type == "OPTIONAL" || interaction.choice_type == "LOOK_AND_CHOOSE",
        "Interaction should be OPTIONAL or LOOK_AND_CHOOSE, got: {}",
        interaction.choice_type
    );

    // 4. Choose "Yes" (WAIT) -> ACTION_BASE_CHOICE + 0
    println!("--- ACTION: Choosing YES (WAIT) ---");
    let res = state.step(&db, ACTION_BASE_CHOICE + 0);  // Use ACTION_BASE_CHOICE + 0 for Yes in OPTIONAL
    if let Err(e) = res {
        panic!("Step 3 (Choice Yes) failed: {}", e);
    }

    state.dump();

    // 5. Verify the card is TAPPED (WAIT state)
    assert!(state.core.players[0].is_tapped(0), "Card should be tapped after choosing YES to wait");

    // 6. Handle LOOK_AND_CHOOSE
    println!("DEBUG: Current Interaction: {}", state.interaction_stack.last().unwrap().choice_type);
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, "LOOK_AND_CHOOSE");

    // LOOK_AND_CHOOSE requires selecting from looked_cards or skipping
    // ACTION_BASE_CHOICE + 0 = select first option, or we may need to skip if no valid choices
    // Keep stepping until we complete the interaction
    while state.phase == Phase::Response && !state.interaction_stack.is_empty() {
        let pi = state.interaction_stack.last().unwrap();
        println!("DEBUG: Resolving interaction: {}", pi.choice_type);

        // For LOOK_AND_CHOOSE, try to select the first available option
        // or skip if that doesn't work
        match state.step(&db, ACTION_BASE_CHOICE + 0) {
            Ok(_) => {},
            Err(_) => {
                // Try skip action if selection fails (Pass = 999)
                let _ = state.step(&db, 999);
            }
        }
    }

    println!("--- AFTER LOOK_AND_CHOOSE ---");
    state.dump();

    // 7. Verify the flow completed
    assert_eq!(state.phase, Phase::Main, "Should be in Main phase after ability completes");

    println!("SUCCESS: Ability flow verified for PL!SP-bp4-002-P");
}
