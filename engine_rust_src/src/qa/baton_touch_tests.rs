use crate::core::logic::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn qa_test_q193_q194_double_baton_touch() {
        // Q193 & Q194 verify double baton touch interactions.
        let mut db = crate::core::logic::CardDatabase::from_json("{}").unwrap();
        let mut cid_bp4_004 = 1;
        let mut cid_n1 = 2;
        let mut cid_n2 = 3;

        {
            let mut m = crate::core::logic::MemberCard::default();
            m.card_id = cid_bp4_004;
            m.card_no = "PL!SP-bp4-004-R＋".to_string();
            m.name = "Sumire".to_string();
            m.cost = 0;
            m.abilities.push(crate::core::logic::Ability {
                trigger: crate::core::enums::TriggerType::Constant,
                bytecode: vec![
                    crate::core::generated_constants::O_BATON_TOUCH_MOD,
                    2,
                    0,
                    0,
                    0,
                ],
                ..Default::default()
            });
            db.members.insert(m.card_id, m);
        }
        {
            let mut m = crate::core::logic::MemberCard::default();
            m.card_id = cid_n1;
            m.card_no = "PL!N-bp4-001-C".to_string();
            m.name = "Norm 1".to_string();
            db.members.insert(m.card_id, m);
        }
        {
            let mut m = crate::core::logic::MemberCard::default();
            m.card_id = cid_n2;
            m.card_no = "PL!N-bp4-002-C".to_string();
            m.name = "Norm 2".to_string();
            db.members.insert(m.card_id, m);
        }

        let mut state = crate::core::logic::GameState::default();
        state.core.players[0].hand = vec![cid_bp4_004, cid_n1, cid_n2].into();
        state.core.players[0].energy_zone = vec![0, 0, 0, 0, 0, 0, 0, 0, 0, 0].into();

        // Play the normal members to slot 0 and 1
        state.core.players[0].hand.remove(1); // Remove n1
        state.core.players[0].stage[0] = cid_n1;
        state.core.players[0].set_moved(0, true);

        state.core.players[0].hand.remove(1); // Remove n2 (now at index 1)
        state.core.players[0].stage[1] = cid_n2;
        state.core.players[0].set_moved(1, true);

        state.core.phase = crate::core::logic::Phase::Main;

        // Turn 1: Try double baton touch (Q194: Should fail because they were played this turn)
        let mut mask = vec![false; 20000];
        state.get_legal_actions_into(&db, 0, &mut mask);
        let aid_0_combo_1 = crate::core::generated_constants::ACTION_BASE_HAND + 3; // slot 0 + 1
        assert!(!mask[aid_0_combo_1 as usize], "Q194: Cannot double baton touch cards played this turn");

        // End turn -> new turn
        state.core.players[0].untap_all(false); // Resets moved flags!
        state.core.players[0].baton_touch_count = 0;
        assert!(!state.core.players[0].is_moved(0));
        assert!(!state.core.players[0].is_moved(1));

        // Turn 2: Try double baton touch again (Q193: Both slot combinations should be valid)
        mask = vec![false; 20000];
        state.get_legal_actions_into(&db, 0, &mut mask);

        let combo_idx_0_to_1 = 0 * 2 + 1; // primary 0, secondary 1
        let combo_idx_1_to_0 = 1 * 2 + 0; // primary 1, secondary 0
        let aid_0_combo_1 = crate::core::generated_constants::ACTION_BASE_HAND + 3 + combo_idx_0_to_1;
        let aid_1_combo_0 = crate::core::generated_constants::ACTION_BASE_HAND + 3 + combo_idx_1_to_0;

        assert!(mask[aid_0_combo_1 as usize], "Q193: Option to play into slot 0 and secondary target slot 1 must be available");
        assert!(mask[aid_1_combo_0 as usize], "Q193: Option to play into slot 1 and secondary target slot 0 must be available");

        // Let's perform one
        use crate::core::logic::MainPhaseController;
        state.handle_main(&db, aid_0_combo_1).expect("Play double baton member");

        assert_eq!(state.core.players[0].stage[0], cid_bp4_004);
        assert_eq!(state.core.players[0].stage[1], -1); // 2nd member left
        assert!(state.core.players[0].discard.contains(&cid_n1));
        assert!(state.core.players[0].discard.contains(&cid_n2));
        assert_eq!(state.core.players[0].baton_touch_count, 2);
    }
}
