#[cfg(test)]
mod tests {
    use crate::core::logic::*;
    use crate::core::enums::*;
    use crate::test_helpers::*;

    #[test]
    fn test_optional_interaction_actions_real_card() {
        let db = load_real_db();
        let mut state = create_test_state();

        // Card 122 (Kotori) has an optional LiveStart ability:
        // "Put 1 hand to discard? Yes/No"
        state.core.players[0].stage[0] = 122;
        state.core.players[0].hand = vec![121].into(); // Needs 1 card to pay
        state.phase = Phase::PerformanceP1;

        // Trigger the ability
        let ctx = AbilityContext { player_id: 0, source_card_id: 122, area_idx: 0, ..Default::default() };
        state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
        state.process_trigger_queue(&db);

        // The game should now be in Phase::Response with OPTIONAL interaction on stack
        assert_eq!(state.phase, Phase::Response, "Should be in Response phase for optional choice");

        // Check legal actions
        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);

        println!("Legal actions: {:?}", receiver.actions);

        // Action 0 (Skip/No) and Action 1 (Yes) MUST be present.
        assert!(receiver.actions.contains(&0), "Action 0 (No/Skip) missing!");
        assert!(receiver.actions.contains(&1), "Action 1 (Yes) missing! This is the soft-lock.");
    }
}
