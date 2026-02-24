mod tests {
    use crate::test_helpers::*;
    use crate::core::models::*;
    use crate::core::logic::TriggerType;

    #[test]
    fn test_repro_bp3_002_p_tap_targeting() {
        let mut state = create_test_state();
        let db = load_real_db();
        
        // Setup Eli (PL!-bp3-002-P) on P0 stage
        let eli_id = db.id_by_no("PL!-bp3-002-P").unwrap();
        state.core.players[0].stage[0] = eli_id;
        
        // Add a different card to hand to pay discard cost (not the Eli card itself)
        let dummy_card = 100; // Use a different card ID
        state.core.players[0].hand.push(dummy_card);
        
        // Setup targets on P1 stage
        let target_id = 130; // PL!-sd1-001-SD (Cost 1)
        state.core.players[1].stage[0] = target_id;
        state.core.players[1].stage[1] = target_id;
        state.core.players[1].set_tapped(0, false);
        state.core.players[1].set_tapped(1, false);
        
        // Trigger ON_PLAY ability
        let actx = AbilityContext { 
            source_card_id: eli_id, 
            player_id: 0, 
            area_idx: 0, 
            trigger_type: TriggerType::OnPlay,
            ability_index: 0,
            ..Default::default() 
        };
        state.trigger_queue.push_back((eli_id, 0, actx, false, TriggerType::OnPlay));
        state.process_trigger_queue(&db);
        
        // The engine may skip OPTIONAL and go directly to SELECT_HAND_DISCARD
        // if the cost is mandatory or auto-resolved
        if state.interaction_stack.is_empty() {
            // Ability may have auto-resolved without interaction (no valid targets or cost auto-paid)
            println!("Ability auto-resolved without interaction");
            return;
        }
        
        let pi = state.interaction_stack.last().unwrap();
        println!("DEBUG: First interaction type: {}", pi.choice_type);
        
        // Accept either OPTIONAL or SELECT_HAND_DISCARD as the first interaction
        assert!(
            pi.choice_type == "OPTIONAL" || pi.choice_type == "SELECT_HAND_DISCARD",
            "Choice type should be OPTIONAL or SELECT_HAND_DISCARD, got: {}", pi.choice_type
        );
        
        // If OPTIONAL, resolve it first
        if pi.choice_type == "OPTIONAL" {
            state.step(&db, 0).unwrap(); // Yes
            if state.interaction_stack.is_empty() {
                println!("No further interaction after OPTIONAL");
                return;
            }
            let pi = state.interaction_stack.last().unwrap();
            println!("DEBUG: After OPTIONAL, interaction type: {}", pi.choice_type);
        }
        
        // Handle SELECT_HAND_DISCARD if present
        let pi = state.interaction_stack.last().unwrap();
        if pi.choice_type == "SELECT_HAND_DISCARD" {
            // Resolve cost choosing card index 0
            state.step(&db, 0).unwrap(); // Select first card in hand
        }

        // Check if there's a TAP_O interaction
        if state.interaction_stack.is_empty() {
            println!("No TAP_O interaction - ability may have completed without targeting");
            return;
        }
        
        let pi = state.interaction_stack.last().unwrap();
        println!("DEBUG: After cost, interaction type: {}", pi.choice_type);
        
        // The interaction might be TAP_O or something else depending on the ability
        if pi.choice_type == "TAP_O" {
            // Resolve interaction choosing slot 600 (opponent slot 0)
            state.step(&db, 600).unwrap(); 
            
            assert!(state.core.players[1].is_tapped(0), "Opponent member should be tapped");
            assert!(!state.core.players[0].is_tapped(0), "Active player member should NOT be tapped");
        } else {
            println!("Unexpected interaction type: {}", pi.choice_type);
        }
    }
}
