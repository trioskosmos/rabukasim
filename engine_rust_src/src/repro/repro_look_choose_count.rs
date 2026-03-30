#[cfg(test)]
mod tests {
    use crate::core::generated_constants::ACTION_BASE_HAND_SELECT;
    use crate::core::logic::*;
    use crate::test_helpers::*;

    fn find_real_matching_members(db: &CardDatabase, count: usize) -> Vec<i32> {
        db.members
            .iter()
            .filter(|(id, member)| {
                **id != 12707 && (member.hearts[1] > 0 || member.hearts[3] > 0 || member.hearts[4] > 0)
            })
            .map(|(id, _)| *id)
            .take(count)
            .collect()
    }

    #[test]
    fn test_look_and_choose_uses_real_card_choose_count() {
        clear_real_db_cache();
        let db = load_real_db();
        let mut state = create_test_state();
        state.ui.silent = true;

        let target_id = 12707;
        let matching_cards = find_real_matching_members(&db, 7);
        assert!(
            matching_cards.len() >= 7,
            "Need at least 7 real matching members in the database to exercise the card"
        );

        state.players[0].hand = vec![target_id, 9, 10].into();
        state.players[0].deck = matching_cards.into();
        state.players[0].energy_zone = (0..20).map(|i| 20001 + i).collect();
        state.phase = Phase::Main;
        state.current_player = 0;

        let play_action = Action::PlayMember {
            hand_idx: 0,
            slot_idx: 0,
        }
        .id();
        state.step(&db, play_action).expect("play should succeed");

        assert_eq!(state.phase, Phase::Response);
        let first_prompt = state
            .interaction_stack
            .last()
            .expect("expected discard prompt first");
        assert_eq!(first_prompt.choice_type, ChoiceType::SelectHandDiscard);

        let mut actions = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut actions);
        let discard_action = actions
            .actions
            .iter()
            .copied()
            .find(|action| *action >= ACTION_BASE_HAND_SELECT)
            .expect("expected at least one hand-discard action");
        state
            .step(&db, discard_action as i32)
            .expect("discard choice should resolve");
        state.process_trigger_queue(&db);

        let second_prompt = state
            .interaction_stack
            .last()
            .expect("expected look-and-choose prompt");
        assert_eq!(second_prompt.choice_type, ChoiceType::LookAndChoose);
        assert_eq!(
            second_prompt.ctx.v_remaining, 3,
            "The real card's LOOK_AND_CHOOSE should allow choosing up to 3 cards"
        );
        assert_eq!(
            state.players[0].looked_cards.len(),
            7,
            "The card should reveal 7 cards before choosing"
        );
    }
}
