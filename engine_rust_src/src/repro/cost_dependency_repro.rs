use crate::core::logic::card_db::LOGIC_ID_MASK;
// use crate::test_helpers::{Action, TestUtils, create_test_db, create_test_state, p_state};

#[cfg(test)]
mod tests {
    use crate::core::logic::*;
    use crate::test_helpers::create_test_state;

    fn create_test_db() -> CardDatabase {
        let mut db = CardDatabase::default();
        let card = MemberCard {
            card_id: 257,
            abilities: vec![
                 Ability {
                     // Optional cost ability
                     trigger: TriggerType::Activated,
                     // Cost: Discard 1 (Type 6, Val 1). Effect: Look 5 (Type 41, Val 5)
                     // Bytecode: [6, 1, 0, 0, 41, 5, 0, 0, 0, 0, 0, 0]
                     // Actually, let's use check logic from test below:
                     // It expects O_MOVE_TO_DISCARD then O_JUMP_F.
                     bytecode: vec![
                         O_MOVE_TO_DISCARD, 1, 2, 6, // Cost (Optional, Hand)
                         O_JUMP_F, 12, 0, 0,         // If skipped, jump to Return (IP 12)
                         O_LOOK_AND_CHOOSE, 5, 0, 6, // Effect
                         O_RETURN, 0, 0, 0
                     ],
                     ..Default::default()
                 }
            ],
            ..Default::default()
        };
        db.members.insert(257, card.clone());
        if db.members_vec.len() <= 257 {
             db.members_vec.resize(258, None);
        }
        db.members_vec[(257 as usize) & LOGIC_ID_MASK as usize] = Some(card);
        db
    }

    #[test]
    fn test_cost_dependency_optional_skip() {
        let db = create_test_db();
        let mut state = create_test_state();

        // Setup hand
        state.core.players[0].hand.push(999); // One card to discard
        state.core.players[0].deck.extend(vec![1, 2, 3, 4, 5]); // Deck to look at

        // Initial state check
        assert_eq!(state.core.players[0].hand.len(), 1);

        // Place card on stage
        state.core.players[0].stage[0] = 257;

        // Activate the ability (slot 0, ability 0, no choice yet)
        state.activate_ability_with_choice(&db, 0, 0, -1, 0).unwrap();

        // Should be in Response phase now, asking for discard
        assert_eq!(state.phase, Phase::Response, "Should be in Response phase for cost selection");
        assert_eq!(state.interaction_stack.last().map(|i| i.effect_opcode).unwrap_or(0), O_MOVE_TO_DISCARD as i16, "Should be pending O_MOVE_TO_DISCARD");

        // Check if skip action (0) is legal
        let legal = state.get_legal_actions(&db);
        assert!(legal[0], "Action ID 0 (Skip/Done) should be legal for optional cost");

        println!("DEBUG: Performing Skip (Action 0)");
        state.step(&db, 0).expect("Step action 0 failed");

        // After skip, O_MOVE_TO_DISCARD sets cond=false, O_JUMP_F jumps to O_RETURN.

        // Check State
        assert_eq!(state.core.players[0].hand.len(), 1, "Hand card should NOT be discarded on skip");

        // Effect should be skipped
        assert_ne!(state.phase, Phase::Response, "Should NOT be in Response for Look and Choose after skipping cost");
        assert_eq!(state.phase, Phase::Main, "Should return to Main phase after skipping optional cost");

        println!("SUCCESS: Cost dependency correctly enforced (Effect skipped on optional cost bypass)");
    }
}
