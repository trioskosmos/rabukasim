#[cfg(test)]
mod tests {
    use crate::core::logic::filter::map_filter_string_to_attr;
    use crate::core::logic::{AbilityContext, TriggerType};
    use crate::test_helpers::{create_test_state, load_real_db, TestUtils};

    #[test]
    fn test_card_162_all_cards_match_repro() {
        let db = load_real_db();
        let mut state = create_test_state();
        state.debug.debug_mode = true;

        let p_idx = 0;
        let card_id = 162;
        let filter_attr = map_filter_string_to_attr("HEART_PINK, TYPE_MEMBER");
        let heart_member_id = db
            .members
            .values()
            .find(|member| {
                state.card_matches_filter(&db, member.card_id, filter_attr)
                    && member.abilities.is_empty()
            })
            .map(|member| member.card_id)
            .expect("Need a real member that matches HEART_PINK + TYPE_MEMBER");
        let live_card_id = db
            .lives
            .values()
            .find(|live| !state.card_matches_filter(&db, live.card_id, filter_attr))
            .map(|live| live.card_id)
            .expect("Need a real live card that does not match HEART_PINK + TYPE_MEMBER");

        // Bytecode for Card 162 (v2 fix):
        // [58, 3, 1, 0, 7405572, 309, 4, 110, 3, 0, 48, 1, 0, 0, 4, 1, 0, 0, 0, 0]
        // 00: MOVE_TO_DISCARD(3)
        // 05: CHECK_DISCARDED_CARDS(all=true, filter=110)
        // 10: ADD_HEARTS(1)
        // 15: RETURN

        // Scenario 1: All 3 are members with [Heart 01].
        state.set_deck(
            p_idx,
            &[
                heart_member_id,
                heart_member_id,
                heart_member_id,
                heart_member_id,
                heart_member_id,
            ],
        );

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

        state.players[p_idx].discard_ids_this_turn.clear();

        println!("--- Triggering OnPlay for Card 162 (All Match) ---");
        state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);

        let all_match_hearts = state.players[p_idx].heart_buffs[slot].get_color_count(0);
        println!("All-match hearts: {}", all_match_hearts);

        // Scenario 2: Only 2 out of 3 match
        let mut state2 = create_test_state();
        state2.debug.debug_mode = true;
        state2.players[p_idx].discard_ids_this_turn.clear();
        // Search for a non-member card key in logic_db.
        // Usually Live cards start from higher indices or specific ranges.
        state2.set_deck(
            p_idx,
            &[
                heart_member_id,
                heart_member_id,
                live_card_id,
                heart_member_id,
                heart_member_id,
            ],
        );
        state2.players[p_idx].hand.push(card_id);
        state2.players[p_idx].stage[slot] = card_id;

        println!("--- Triggering OnPlay for Card 162 (Partial Match) ---");
        state2.trigger_abilities(&db, TriggerType::OnPlay, &ctx);

        let partial_match_hearts = state2.players[p_idx].heart_buffs[slot].get_color_count(0);
        println!("Partial-match hearts: {}", partial_match_hearts);
    }
}
