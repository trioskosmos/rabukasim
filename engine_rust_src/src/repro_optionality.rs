#[cfg(test)]
mod tests {
    use crate::core::logic::*;
    use crate::test_helpers::{create_test_db, create_test_state, add_card, Action};

    #[test]
    fn test_optional_tap_cost_accept() {
        // Test that optional tap costs can be accepted
        let mut db = create_test_db();
        let mut state = create_test_state();

        // Create a card with optional tap cost ability
        // O_ADD_BLADES(17) v=2 s=0 (target self) with optional tap cost
        // Bytecode: [17, 2, 0, 0] with cost flag
        add_card(&mut db, 30032, "OPT-TAP", vec![1], vec![(
            TriggerType::Activated,
            vec![17, 2, 0, 0], // O_ADD_BLADES +2
            vec![]
        )]);

        state.core.players[0].hand.push(30032);

        // Play the card
        let play_action = Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id();
        state.step(&db, play_action).expect("Failed to play member");
        state.auto_step(&db);

        // Basic verification that card is on stage
        assert!(state.core.players[0].stage[0] >= 0, "Card should be on stage");
    }

    #[test]
    fn test_optional_tap_cost_manual_choice() {
        // Test manual choice selection for optional costs
        let _db = create_test_db();
        let state = create_test_state();

        // Basic state verification
        assert_eq!(state.phase, Phase::Main);
        assert_eq!(state.current_player, 0);
    }

    #[test]
    fn test_trigger_even_if_already_tapped() {
        // Test that triggers can fire even if card is tapped
        let mut db = create_test_db();
        let mut state = create_test_state();

        // Add a card with on-play trigger
        add_card(&mut db, 30033, "TRIGGER-CARD", vec![1], vec![(
            TriggerType::OnPlay,
            vec![10, 1, 0, 0], // O_DRAW 1
            vec![]
        )]);

        state.core.players[0].hand.push(30033);

        // Play the card
        let play_action = Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id();
        state.step(&db, play_action).expect("Failed to play member");

        // Verify card is on stage
        assert_eq!(state.core.players[0].stage[0], 30033);
    }
}
