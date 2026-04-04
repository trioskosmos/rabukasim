#[cfg(test)]
mod tests {
    use crate::core::logic::{AbilityContext, CardDatabase, FrameProgram, MemberCard, TriggerType};
    use crate::test_helpers::{create_test_state, TestUtils};

    #[test]
    fn test_move_to_discard_deck_top_slot_1_repro() {
        let mut db = CardDatabase::default();
        
        // Card 126: Move 5 from DeckTop to Discard. If Live card among them, Draw 1.
        let mut card126 = MemberCard::default();
        card126.card_id = 126;
        let mut ab = crate::core::logic::models::Ability::default();
        ab.trigger = TriggerType::OnPlay;
        ab.frame_program = Some(FrameProgram::from_instruction_words(&[
            58, 5, 1, 0, 65540, 309, 1, 8, 0, 48, 10, 1, 0, 0, 4, 1, 0, 0, 0, 0,
        ]));
        card126.abilities.push(ab);
        db.members.insert(126, card126);

        let mut state = create_test_state();
        state.debug.debug_mode = true;

        let p_idx = 0;
        // Ensure deck has enough cards
        state.set_deck(p_idx, &[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
        let initial_discard_len = state.players[p_idx].discard.len();

        // Play card to Slot 1 (not 0)
        let slot = 1;
        state.players[p_idx].stage[slot] = 126;

        let ctx = AbilityContext {
            source_card_id: 126,
            player_id: p_idx as u8,
            area_idx: slot as i16,
            target_slot: slot as i16,
            ..Default::default()
        };

        // Trigger OnPlay abilities
        println!("--- Triggering OnPlay for Card 126 ---");
        state.resolve_ability(&db, &db.members[&126].abilities[0], &ctx);
        state.dump_verbose();

        // If the bug exists, the state will have a suspension and the discard count won't increase by 5
        assert!(
            state.interaction_stack.is_empty(),
            "Game should NOT be suspended for MOVE_TO_DISCARD from deck top"
        );
        assert_eq!(
            state.players[p_idx].discard.len(),
            initial_discard_len + 5,
            "Should have discarded 5 cards"
        );
    }
}
