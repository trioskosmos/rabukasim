#[cfg(test)]
mod tests {
    use crate::test_helpers::{create_test_state, load_real_db, TestUtils};
    use crate::core::logic::{TriggerType, AbilityContext};

    #[test]
    fn test_move_to_discard_deck_top_slot_1_repro() {
        use crate::test_helpers::generate_card_report;
        let db = load_real_db();
        let mut state = create_test_state();
        state.debug.debug_mode = true;

        let p_idx = 0;
        // CID 126 is PL!-sd1-007-SD: [OnPlay] MOVE_TO_DISCARD(5) FROM=DECK_TOP ...
        let card_id = 126;
        generate_card_report(card_id);

        // Ensure deck has enough cards
        state.set_deck(p_idx, &[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
        let initial_discard_len = state.core.players[p_idx].discard.len();

        // Play card to Slot 1 (not 0)
        let slot = 1;
        state.core.players[p_idx].stage[slot] = card_id;

        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            area_idx: slot as i16,
            target_slot: slot as i16, // This sets ctx.target_slot
            ..Default::default()
        };

        // Trigger OnPlay abilities
        println!("--- Triggering OnPlay for Card {} ---", card_id);
        state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
        state.dump_verbose();

        // If the bug exists, the state will have a suspension and the discard count won't increase by 5
        assert!(state.interaction_stack.is_empty(), "Game should NOT be suspended for MOVE_TO_DISCARD from deck top");
        assert_eq!(state.core.players[p_idx].discard.len(), initial_discard_len + 5, "Should have discarded 5 cards");
    }
}
