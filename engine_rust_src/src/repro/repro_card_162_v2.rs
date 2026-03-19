#[cfg(test)]
mod tests {
    use crate::core::logic::{AbilityContext, TriggerType};
    use crate::test_helpers::{create_test_state, load_real_db, TestUtils};

    #[test]
    fn test_card_162_all_cards_match_repro() {
        let db = load_real_db();
        let mut state = create_test_state();
        state.debug.debug_mode = true;

        let p_idx = 0;
        let card_id = 162;

        // Bytecode for Card 162 (v2 fix):
        // [58, 3, 1, 0, 7405572, 309, 4, 110, 3, 0, 48, 1, 0, 0, 4, 1, 0, 0, 0, 0]
        // 00: MOVE_TO_DISCARD(3)
        // 05: CHECK_DISCARDED_CARDS(all=true, filter=110)
        // 10: ADD_HEARTS(1)
        // 15: RETURN
        
        // Scenario 1: All 3 are members (type=member is bit 1: 0x02)
        // Card 10 is verified to be a member and exists.
        state.set_deck(p_idx, &[10, 10, 10, 10, 10]);
        
        state.players[p_idx].hand.push(card_id);
        let slot = 0;
        state.players[p_idx].stage[slot] = card_id;

        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            area_idx: slot as i16,
            target_slot: slot as i16,
            ..Default::default()
        };

        let initial_hearts = state.players[p_idx].heart_buffs[slot].get_color_count(0); // Pink/Red hearts
        
        println!("--- Triggering OnPlay for Card 162 (All Match) ---");
        state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
        
        assert_eq!(
            state.players[p_idx].heart_buffs[slot].get_color_count(0),
            initial_hearts + 1,
            "Should have gained a heart because all 3 were members"
        );

        // Scenario 2: Only 2 out of 3 match
        let mut state2 = create_test_state();
        state2.debug.debug_mode = true;
        // Search for a non-member card key in logic_db.
        // Usually Live cards start from higher indices or specific ranges.
        // Card 6 is verified to be a Live card.
        state2.set_deck(p_idx, &[10, 10, 6, 10, 10]); 
        state2.players[p_idx].hand.push(card_id);
        state2.players[p_idx].stage[slot] = card_id;
        
        println!("--- Triggering OnPlay for Card 162 (Partial Match) ---");
        state2.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
        
        assert_eq!(
            state2.players[p_idx].heart_buffs[slot].get_color_count(0),
            initial_hearts,
            "Should NOT have gained a heart because only 2 were members"
        );
    }
}
