#[cfg(test)]
mod tests {
    use crate::core::logic::{GameState, AbilityContext, TriggerType, Phase};
    use crate::core::enums::*;
    use crate::test_helpers::{create_test_state, load_real_db, TestUtils};
    use crate::core::generated_constants::*;

    #[test]
    fn test_softlock_mandatory_discard_no_matches() {
        let db = load_real_db();
        let mut state = create_test_state();

        // Setup: Player 0 has 1 card in hand (ID 1000 - some random card)
        // We will trigger a mandatory MOVE_TO_DISCARD with a filter that ID 1000 does NOT match.
        // e.g. Filter for Cost > 99 (assuming card 1000 has lower cost)

        let p_idx = 0;
        let card_id = 3001; // "OPP_CHOOSE_TEST" from test_helpers
        state.set_hand(p_idx, &[card_id]);
        let initial_hand_len = state.core.players[p_idx].hand.len();
        let initial_discard_len = state.core.players[p_idx].discard.len();

        // Filter: Cost (Bit 24=1) > 99 (Value shifted 25)
        let filter_cost_gt_99: u64 = ((99u64) << FILTER_COST_SHIFT) | FILTER_COST_ENABLE;

        // Opcode: O_MOVE_TO_DISCARD
        // V = 1 (Count)
        // A = Filter
        // S = 6 (Source: Hand)

        let ctx = AbilityContext {
            player_id: p_idx as u8,
            source_card_id: -1,
            ..Default::default()
        };

        let bytecode = vec![
            O_MOVE_TO_DISCARD, 1, (filter_cost_gt_99 & 0xFFFFFFFF) as i32, (filter_cost_gt_99 >> 32) as i32, 6,
            O_RETURN, 0, 0, 0, 0
        ];

        state.resolve_bytecode(&db, &bytecode, &ctx);

        // Correct behavior:
        // 1. suspend_interaction is called.
        // 2. generate_legal_actions finds no matching cards in hand.
        // 3. Since no legal actions (or only action 0), suspend_interaction returns false (skips suspension).
        // 4. handle_move_to_discard proceeds to auto-discard logic.
        // 5. With our fix, auto-discard logic respects filter, finds nothing, and discards nothing.
        // 6. Execution finishes, returning to Phase::Main.

        assert_eq!(state.phase, Phase::Main, "Interaction should be skipped due to no valid targets");

        // Verify no cards were discarded
        assert_eq!(state.core.players[p_idx].hand.len(), initial_hand_len, "Hand should remain same size");
        assert_eq!(state.core.players[p_idx].discard.len(), initial_discard_len, "Discard should remain same size");
    }
}
