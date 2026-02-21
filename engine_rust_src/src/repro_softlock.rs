
#[cfg(test)]
mod tests {
    
    use crate::core::logic::game::GameState;
    
    use crate::core::models::AbilityContext;
    use crate::core::enums::Phase;
    use crate::core::generated_constants::*;
    use crate::test_helpers::load_real_db;

    #[test]
    fn test_repro_softlock_full_flow() {
        let db = load_real_db();
        let mut state = GameState::default();

        let member = db.get_member(4332).expect("Card 4332 not found in DB! Check path to cards_compiled.json.");
        println!("DEBUG [test]: Card 4332 found. Ability count: {}", member.abilities.len());

        // 1. Setup state: In PerformanceP1, with card 4332 about to trigger OnLiveStart
        state.phase = Phase::PerformanceP1;
        state.current_player = 0;
        state.core.players[0].stage[1] = 4332; // 桜坂しずく (Member)
        state.core.players[0].energy_zone = smallvec::smallvec![1179, 1179]; // 2 energy
        state.core.players[0].tapped_energy_mask = 0; // Untapped


        // 2. Trigger OnLiveStart
        let ctx = AbilityContext { player_id: 0, source_card_id: 4332, area_idx: 0, ability_index: 1, ..Default::default() };
        println!("DEBUG [test]: Triggering OnLiveStart for 4332...");
        state.trigger_abilities(&db, crate::core::enums::TriggerType::OnLiveStart, &ctx);



        // Check if suspended for OPTIONAL
        assert_eq!(state.phase, Phase::Response);
        assert_eq!(state.interaction_stack.len(), 1);
        let pi = state.interaction_stack.last().unwrap();
        assert_eq!(pi.choice_type, "OPTIONAL");
        assert_eq!(pi.effect_opcode, 64); // O_PAY_ENERGY

        // 3. Generate legal actions - Should have [0, 8000]
        let mut actions = Vec::new();
        state.generate_legal_actions(&db, 0, &mut actions);
        assert!(actions.contains(&0));
        assert!(actions.contains(&8000), "Missing Action 8000 (YES) in first suspension! Found: {:?}", actions);

        // 4. Perform Action 8000 (YES)
        state.step(&db, 8000).expect("Step failed");

        // 5. Check state after resumption
        // Card 4332 BC: PAY_ENERGY(v=1, a=2) -> COLOR_SELECT
        // Since player had 2 energy, it should have auto-paid then suspended for COLOR_SELECT.
        
        assert_eq!(state.phase, Phase::Response, "Should be in Response phase for COLOR_SELECT");
        assert_eq!(state.interaction_stack.len(), 1, "Should have one interaction (COLOR_SELECT) on stack");
        
        let pi2 = state.interaction_stack.last().unwrap();
        assert_eq!(pi2.choice_type, "COLOR_SELECT", "Should be suspended for COLOR selection");
        assert_eq!(pi2.effect_opcode, 45); // O_COLOR_SELECT
        
        // Final Action Check
        actions.clear();
        state.generate_legal_actions(&db, 0, &mut actions);
        assert!(actions.contains(&(ACTION_BASE_COLOR as usize)), "Should have COLOR selection starting at 580. Found: {:?}", actions);
        assert!(actions.contains(&(ACTION_BASE_COLOR as usize + 5)));
    }
}
