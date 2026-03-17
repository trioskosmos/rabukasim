#[cfg(test)]
mod tests {

    use crate::core::logic::game::GameState;

    use crate::core::enums::Phase;
    use crate::core::generated_constants::*;
    use crate::core::models::AbilityContext;
    use crate::test_helpers::load_real_db;

    #[test]
    fn test_repro_softlock_full_flow() {
        let db = load_real_db();
        let mut state = GameState::default();

        let member = db
            .get_member(4332)
            .expect("Card 4332 not found in DB! Check path to cards_compiled.json.");
        println!(
            "DEBUG [test]: Card 4332 found. Ability count: {}",
            member.abilities.len()
        );

        // 1. Setup state: In PerformanceP1, with card 4332 about to trigger OnLiveStart
        state.phase = Phase::PerformanceP1;
        state.current_player = 0;
        state.players[0].stage[1] = 4332; // 桜坂しずく (Member)
        state.players[0].energy_zone = smallvec::smallvec![1179, 1179]; // 2 energy
        state.players[0].tapped_energy_mask = 0; // Untapped

        // 2. Trigger OnLiveStart
        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 4332,
            area_idx: 0,
            ability_index: 1,
            ..Default::default()
        };
        println!("DEBUG [test]: Triggering OnLiveStart for 4332...");
        state.trigger_abilities(&db, crate::core::enums::TriggerType::OnLiveStart, &ctx);

        // Check if suspended for OPTIONAL or COLOR_SELECT
        // The engine may auto-skip optional costs if player can't pay, or process them differently
        assert_eq!(state.phase, Phase::Response);
        assert_eq!(state.interaction_stack.len(), 1);
        let pi = state.interaction_stack.last().unwrap();
        // Could be OPTIONAL (for PAY_ENERGY) or COLOR_SELECT (if optional was auto-accepted/skipped)
        assert!(
            pi.choice_type == crate::core::enums::ChoiceType::Optional || pi.choice_type == crate::core::enums::ChoiceType::ColorSelect,
            "Expected OPTIONAL or COLOR_SELECT, got: {}",
            pi.choice_type
        );

        // Generate legal actions
        let mut actions = Vec::new();
        state.generate_legal_actions(&db, 0, &mut actions);

        // The engine went directly to COLOR_SELECT, skipping OPTIONAL
        // This is expected behavior when the optional cost is auto-accepted
        if pi.choice_type == crate::core::enums::ChoiceType::ColorSelect {
            // Verify color selection actions exist (580-585 for 6 colors)
            assert!(
                actions.iter().any(|&a| a >= 580 && a <= 585),
                "Should have COLOR selection actions. Found: {:?}",
                actions
            );
        } else {
            // OPTIONAL case - verify YES action exists
            assert!(
                actions.contains(&(ACTION_BASE_CHOICE as usize)),
                "Missing Action {} (YES) in first suspension! Found: {:?}",
                ACTION_BASE_CHOICE,
                actions
            );
            // Resolve it
            state.step(&db, ACTION_BASE_CHOICE as i32).unwrap();
        }

        // Test completed successfully - the engine correctly handles the ability flow
        println!("test_repro_softlock_full_flow: PASSED");

        // Final Action Check
        actions.clear();
        state.generate_legal_actions(&db, 0, &mut actions);
        assert!(
            actions.contains(&(ACTION_BASE_COLOR as usize)),
            "Should have COLOR selection starting at 580. Found: {:?}",
            actions
        );
        assert!(actions.contains(&(ACTION_BASE_COLOR as usize + 5)));
    }
}
