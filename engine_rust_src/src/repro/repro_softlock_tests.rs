#[cfg(test)]
mod tests {
    use crate::core::enums::Phase;
    use crate::core::generated_constants::ACTION_BASE_HAND_SELECT;
    use crate::core::logic::*;
    use crate::test_helpers::*;

    #[test]
    fn test_optional_interaction_actions_real_card() {
        let db = load_real_db();
        let mut state = create_test_state();

        // Card 122 (Kotori) has an optional LiveStart ability:
        // "Put 1 hand to discard? Yes/No"
        state.players[0].stage[0] = 122;
        state.players[0].hand = vec![121].into(); // Needs 1 card to pay
        state.phase = Phase::Main;

        // Trigger the ability
        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 122,
            area_idx: 0,
            ..Default::default()
        };
        state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
        state.process_trigger_queue(&db);

        // The game should now be in Phase::Response with OPTIONAL interaction on stack
        assert_eq!(
            state.phase,
            Phase::Response,
            "Should be in Response phase for optional choice"
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
                .any(|action| *action >= ACTION_BASE_HAND_SELECT),
            "A selectable hand-discard action must exist so the optional ability can be accepted"
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
