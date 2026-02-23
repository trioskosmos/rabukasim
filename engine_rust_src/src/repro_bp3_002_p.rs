mod tests {
    use crate::core::logic::card_db::CardDatabase;
    use crate::core::logic::GameState;
    use crate::test_helpers::*;
    use crate::core::enums::*;
    use crate::core::models::*;
    use crate::core::logic::TriggerType;

    #[test]
    fn test_repro_bp3_002_p_tap_targeting() {
        let mut state = create_test_state();
        let db = load_real_db();
        
        // Setup Eli (PL!-bp3-002-P) on P0 stage
        let eli_id = db.id_by_no("PL!-bp3-002-P").unwrap();
        state.core.players[0].stage[0] = eli_id;
        state.core.players[0].hand.push(eli_id); // Add a card to hand to pay cost
        
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
        
        // Should be suspended for OPTIONAL (Yes/No) first for optional cost
        assert!(!state.interaction_stack.is_empty(), "Should be suspended for interaction");
        let pi = state.interaction_stack.last().unwrap();
        assert_eq!(pi.choice_type, "OPTIONAL", "Choice type should be OPTIONAL (Yes/No for cost)");
        
        // Resolve OPTIONAL with YES (choice_index=0 means Yes)
        state.step(&db, 0).unwrap(); 

        // Now should be suspended for SELECT_HAND_DISCARD (select card to discard)
        assert!(!state.interaction_stack.is_empty(), "Should be suspended for card selection");
        let pi = state.interaction_stack.last().unwrap();
        assert_eq!(pi.choice_type, "SELECT_HAND_DISCARD", "Choice type should be SELECT_HAND_DISCARD");
        
        // Resolve cost choosing card index 0
        state.step(&db, 0).unwrap(); // Select first card in hand

        // Now should be suspended for TAP_O (Effect)
        assert!(!state.interaction_stack.is_empty(), "Should be suspended for effect interaction");
        let pi = state.interaction_stack.last().unwrap();
        assert_eq!(pi.choice_type, "TAP_O", "Choice type should be TAP_O");
        
        // Resolve interaction choosing slot 600 (opponent slot 0)
        state.step(&db, 600).unwrap(); 
        
        assert!(state.core.players[1].is_tapped(0), "Opponent member should be tapped");
        assert!(!state.core.players[0].is_tapped(0), "Active player member should NOT be tapped");
    }
}
