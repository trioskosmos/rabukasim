#[cfg(test)]
mod tests {
    use crate::core::enums::{ChoiceType, Phase};
    use crate::core::generated_constants::ACTION_BASE_CHOICE;
    use crate::test_helpers::*;

    #[test]
    fn test_optional_interaction_actions_real_card_4442() {
        let db = load_real_db();
        let mut state = create_test_state();

        // Card 4442 has a real optional PAY_ENERGY prompt in the play flow.
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0].hand = vec![4442].into();
        state.players[0].energy_zone = vec![
            3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010, 3011, 3012, 3013, 3014,
            3015,
        ]
        .into();

        state.play_member(&db, 0, 0).expect("play should succeed");

        assert_eq!(state.phase, Phase::Response);
        assert_eq!(
            state.interaction_stack
                .last()
                .map(|interaction| interaction.choice_type),
            Some(ChoiceType::Optional)
        );

        // Check legal actions
        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);

        println!("Legal actions: {:?}", receiver.actions);

        // The current engine represents "Yes" by exposing the actual hand-selection actions
        // directly, while action 0 remains the decline/skip path.
        assert!(receiver.actions.contains(&0), "Action 0 (No/Skip) missing!");
        assert!(
            receiver
                .actions
                .iter()
                .any(|action| *action == ACTION_BASE_CHOICE),
            "A selectable accept action must exist so the optional ability can be accepted"
        );
    }

    #[test]
    fn debug_card_122_hydrated_frames() {
        let db = load_real_db();
        let ability = &db
            .get_member(122)
            .expect("card 122 should exist")
            .abilities[1];
        let frames = ability.resolved_frames();
        eprintln!(
            "[CARD122_DBG] source={} frame_program_present={} frame_program_len={} frame_count={} first={:?} first_optional={} first_slot={:?}",
            ability.resolved_frame_source(),
            ability.frame_program.is_some(),
            ability.frame_program.as_ref().map(|p| p.frames.len()).unwrap_or(0),
            frames.len(),
            frames.first().map(|frame| frame.opcode()),
            frames
                .first()
                .map(|frame| frame.components().filter.is_optional)
                .unwrap_or(false),
            frames.first().map(|frame| frame.components().slot)
        );
        assert!(!frames.is_empty(), "card 122 should hydrate at least one frame");
    }

    #[test]
    fn debug_failed_card_hydration_probe() {
        let db = load_real_db();
        for card_id in [163, 707, 423, 275, 4558] {
            let card = db
                .get_member(card_id)
                .unwrap_or_else(|| panic!("card {card_id} should exist"));
            let ab = card.abilities.first().expect("ability missing");
            let frames = ab.resolved_frames();
            eprintln!(
                "[HYDRATE_DBG] card_id={} card_no={} frame_program={} frame_len={} resolved_source={} first_opt={} effect0_opt={} effects={}",
                card_id,
                card.card_no,
                ab.frame_program.is_some(),
                ab.frame_program.as_ref().map(|p| p.frames.len()).unwrap_or(0),
                ab.resolved_frame_source(),
                frames.first().map(|f| f.components().filter.is_optional).unwrap_or(false),
                ab.effects.first().map(|e| e.is_optional).unwrap_or(false),
                ab.effects.len(),
            );
        }
    }
}
