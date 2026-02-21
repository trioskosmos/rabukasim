use crate::core::logic::*;
use crate::test_helpers::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_card_528_movement_fix() {
        let db = load_real_db();
        let mut state = create_test_state();
        
        // Card 528 (PL!SP-bp2-002-P) 
        state.core.players[0].stage[0] = 528;
        // Deck needs cards with cost 11 or more for O_LOOK_AND_CHOOSE to find targets
        // ID 563 (PL!SP-bp4-007-P) has cost 11.
        state.core.players[0].deck = vec![563, 563, 563].into();
        state.phase = Phase::Main;
        
        let ctx = AbilityContext { player_id: 0, source_card_id: 528, area_idx: 0, ..Default::default() };
        state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
        state.process_trigger_queue(&db);
        
        // Should be at O_LOOK_AND_CHOOSE suspension
        assert_eq!(state.phase, Phase::Response);
        assert_eq!(state.interaction_stack.last().unwrap().effect_opcode, 41);
        
        let chosen_card_id = state.core.players[0].looked_cards[0];
        assert_eq!(chosen_card_id, 563);
        
        // Submit choice (Action ID 8000 + index 0)
        state.step(&db, ACTION_BASE_CHOICE + 0).expect("Step failed"); 
        
        // Verify destination: Hand (6)
        assert!(state.core.players[0].hand.contains(&chosen_card_id), "Card 563 should be in hand!");
        assert!(!state.core.players[0].discard.contains(&chosen_card_id), "Card 563 should NOT be in discard!");
    }

    #[test]
    fn test_pay_energy_high_cost_softlock_fix() {
        let db = load_real_db();
        let mut state = create_test_state();
        
        // Generic member IDs for energy
        state.core.players[0].energy_zone = vec![9, 10, 11].into(); 
        state.core.players[0].tapped_energy_mask = 0;
        
        let mut ctx = AbilityContext { player_id: 0, ..Default::default() };
        ctx.v_remaining = 2; 
        
        state.phase = Phase::Response;
        state.interaction_stack.push(PendingInteraction {
            ctx: ctx.clone(),
            card_id: -1, // TEST: FIXED - activate_ability_with_choice now handles -1
            ability_index: -1,
            effect_opcode: 64, // O_PAY_ENERGY
            choice_type: "PAY_ENERGY".to_string(),
            v_remaining: 2,
            actions: Vec::new(),
            ..Default::default()
        });

        // 1. Check legal actions
        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);
        
        assert!(receiver.actions.contains(&6000), "Action ID 6000 (Energy 0) missing!");
        assert!(receiver.actions.contains(&6001), "Action ID 6001 (Energy 1) missing!");
        assert!(receiver.actions.contains(&6002), "Action ID 6002 (Energy 2) missing!");
        
        // 2. Pay 1st energy
        state.step(&db, 6000).expect("Step 1 failed");
        
        assert_eq!(state.phase, Phase::Response);
        assert_eq!(state.interaction_stack.last().unwrap().v_remaining, 1);
        assert!(state.core.players[0].is_energy_tapped(0));
        
        // 3. Pay 2nd energy
        state.step(&db, 6001).expect("Step 2 failed");
        
        assert!(state.core.players[0].is_energy_tapped(0));
        assert!(state.core.players[0].is_energy_tapped(1));
    }

    #[test]
    fn test_card_275_sequential_interaction_resumption() {
        let mut state = GameState::default();
        let card_id = 275; // Setsuna
        let next_setsuna = 275; // Another copy of Cost 2 Setsuna

        state.core.players[0].hand = vec![next_setsuna].into();
        state.core.players[0].stage[0] = card_id;
        state.phase = Phase::Main;
        state.debug.debug_mode = true;

        use crate::test_helpers::load_real_db;
        let db = load_real_db();
        
        // Give player energy
        state.core.players[0].energy_zone = vec![999, 999, 999, 999, 999].into();

        // 1. Initial execution - should suspend for hand choice
        state.activate_ability(&db, 0, 0).expect("Activation failed");
        
        assert_eq!(state.phase, Phase::Response);
        assert_eq!(state.interaction_stack.len(), 1);
        assert_eq!(state.interaction_stack[0].choice_type, "SELECT_HAND_PLAY");

        // 2. Resume - player chooses hand index 0 (card 227)
        // O_PLAY_MEMBER_FROM_HAND uses ACTION_BASE_HAND (1000)
        state.activate_ability_with_choice(&db, 1000, 0, 0, -1).expect("Resumption failed");

        // 3. Verification
        assert_eq!(state.core.players[0].stage[0], next_setsuna, "New Setsuna should be on stage");
        assert_eq!(state.core.players[0].hand.len(), 0, "Card should be removed from hand");
        assert_eq!(state.phase, Phase::Main, "Should HAVE returned to Main phase after RETURN");
        assert!(state.interaction_stack.is_empty(), "Interaction stack should be cleared");
    }
}
