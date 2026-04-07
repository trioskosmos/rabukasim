// use crate::test_helpers::{Action, TestUtils, create_test_db, create_test_state, p_state};
#[cfg(test)]
mod tests {
    use crate::core::logic::card_db::LOGIC_ID_MASK;
    use crate::core::logic::*;

    fn setup_test_state() -> (GameState, CardDatabase) {
        let mut state = GameState::default();
        let mut db = CardDatabase::default();

        // Register dummy IDs used in deck/energy
        let mut m1 = MemberCard::default();
        m1.card_id = 1;
        m1.name = "Dummy Member 1".to_string();
        db.members.insert(1, m1.clone());
        db.members_vec[(1 & LOGIC_ID_MASK) as usize] = Some(m1);

        let mut m20001 = MemberCard::default();
        m20001.card_id = 20001;
        m20001.name = "Dummy Energy 20001".to_string();
        db.members.insert(20001, m20001.clone());
        db.members_vec[(20001 & LOGIC_ID_MASK) as usize] = Some(m20001);

        let deck0 = vec![1; 60];
        let deck1 = vec![1; 60];
        let energy0 = vec![20001; 60];
        let energy1 = vec![20001; 60];

        state.initialize_game(deck0, deck1, energy0, energy1, vec![], vec![]);
        state.ui.silent = true;
        (state, db)
    }

    #[test]
    fn test_live_success_with_reduction() {
        let (mut state, mut db) = setup_test_state();
        let p_idx = 0;

        // 1. Setup a Live Card that requires 2 Pink Hearts (Heart=1)
        // ID 10001 (Start Dash!!) fits or we can make a mock.
        // Let's make a mock to be sure.
        let mut live_card = LiveCard::default();
        live_card.card_id = 60001;
        live_card.name = "Test Live".to_string();
        live_card.score = 1;
        live_card.required_hearts = [2, 0, 0, 0, 0, 0, 0]; // 2 Pink
        db.lives.insert(60001, live_card.clone());
        db.lives_vec.resize(65536, None);
        db.lives_vec[(60001 & LOGIC_ID_MASK) as usize] = Some(live_card);

        // 2. Put it in Live Zone
        state.players[p_idx].live_zone[0] = 60001;
        // Mark as "revealed" so performance phase checks it
        state.players[p_idx].set_revealed(0, true);

        // 3. Give player 1 Pink Heart (Insufficient naturally)
        // We'll trust get_total_hearts logic, but we can just override reductions.
        // Let's say we have 0 hearts provided by members/yell.

        // 4. Apply Reduction of 2 Pink Hearts
        // "Heart 1" is Pink (Index 0).
        // Reduction encoding: 4 bits per color.
        // We want -2 to Pink.
        state.players[p_idx]
            .heart_req_reductions
            .set_color_count(0, 2);

        // 5. Run Live Result Phase
        state.phase = Phase::LiveResult;
        state.turn = 1;
        state.current_player = 0;

        // Set performance_results snapshot to indicate success
        // This is required because do_live_result trusts the snapshot from check_performance_requirements
        state.ui.performance_results.insert(
            p_idx as u8,
            serde_json::json!({
                "success": true,
                "lives": [
                    {"passed": true, "score": 1, "slot_idx": 0},
                    {"passed": false, "score": 0, "slot_idx": 1},
                    {"passed": false, "score": 0, "slot_idx": 2}
                ]
            }),
        );

        crate::core::logic::performance::do_live_result(&mut state, &db);

        // 6. Assertions
        // If bug exists: Card is in discard (not success lives), or still in live zone (if choices pending? No, if 1 candidate auto-move).
        // If reduced, valid_candidates = 1 (our card). Auto-move to success.

        assert!(
            state.players[p_idx].success_lives.contains(&60001),
            "Live card 60001 should be in Success Lives. Found in Zone: {:?}, Discard: {:?}",
            state.players[p_idx].live_zone,
            state.players[p_idx].discard
        );

        assert_eq!(
            state.players[p_idx].live_zone[0], -1,
            "Live zone should be empty"
        );
    }
    #[test]
    fn test_kimi_no_kokoro_prevention() {
        use crate::test_helpers::load_real_db;

        let db = load_real_db();
        let kimi_no_kokoro_id = 431;
        let mut state = GameState::default();

        state.initialize_game(
            vec![101; 48],
            vec![101; 48],
            vec![1, 2, 3, 4, 5, 6],
            vec![1, 2, 3, 4, 5, 6],
            vec![],
            vec![],
        );
        state.ui.silent = true;
        state.players[0].live_zone[0] = kimi_no_kokoro_id;
        state.players[0].set_revealed(0, true);
        state.players[0].hand.push(1);
        state.players[0].hand.push(2);

        for color_idx in 0..7 {
            state.players[0].heart_buffs[0].set_color_count(color_idx, 1);
            state.players[0].heart_buffs[1].set_color_count(color_idx, 1);
            state.players[0].heart_buffs[2].set_color_count(color_idx, 1);
        }

        state.ui.performance_results.insert(
            0,
            serde_json::json!({
                "success": true,
                "lives": [
                    {
                        "score": 10,
                        "passed": true,
                        "slot_idx": 0
                    }
                ]
            }),
        );
        state.phase = Phase::LiveResult;
        state.current_player = 0;

        state.step(&db, 0).unwrap();

        assert_eq!(state.phase, Phase::Response, "Should pause for the on-live-success discard choice");
        assert_eq!(
            state.interaction_stack.last().map(|i| i.choice_type).unwrap_or(ChoiceType::None),
            ChoiceType::SelectHandDiscard
        );
        assert_eq!(
            state.interaction_stack.last().map(|i| i.card_id).unwrap_or(0),
            kimi_no_kokoro_id
        );

        for _ in 0..4 {
            if state.phase != Phase::Response {
                break;
            }

            let mut actions: Vec<i32> = Vec::new();
            state.generate_legal_actions(&db, 0, &mut actions);
            let action = if actions.contains(&crate::core::logic::ACTION_BASE_HAND_SELECT) {
                crate::core::logic::ACTION_BASE_HAND_SELECT as i32
            } else {
                *actions
                    .iter()
                    .filter(|action| **action >= crate::core::logic::ACTION_BASE_CHOICE)
                    .min()
                    .expect("expected a follow-up response action for Kimi no Kokoro") as i32
            };

            state.step(&db, action).unwrap();
        }

        for _ in 0..3 {
            if state.phase == Phase::LiveResult {
                state.step(&db, 0).unwrap();
            } else {
                break;
            }
        }

        assert_eq!(state.players[0].live_zone[0], -1, "Live card should be removed from the live zone");
        assert!(
            state.players[0].discard.contains(&(kimi_no_kokoro_id as i32)),
            "Live card should end in discard after prevention"
        );
        assert!(
            !state.players[0].success_lives.contains(&(kimi_no_kokoro_id as i32)),
            "PreventSetToSuccessPile should keep Kimi no Kokoro out of the success pile"
        );
    }

    #[test]
    fn test_baton_touch_restriction() {
        use crate::test_helpers::load_real_db;

        let (mut state, _) = setup_test_state();
        let db = load_real_db();
        let p_idx = 0;

        // Card ID 10: LL-bp2-001-R+ — has a real CONSTANT ability with O_PREVENT_BATON_TOUCH
        // No mocked bytecode needed: the real compiled data provides the restriction.
        state.players[p_idx].stage[0] = 10;

        // Give player another member in hand (use a real card from the DB)
        let other_member_id = 9; // LL-bp1-001-R+ (cost 20)
        state.players[p_idx].hand.clear();
        state.players[p_idx].hand_added_turn.clear();
        state.players[p_idx].hand.push(other_member_id);
        // Card 9 costs 20 energy — give player enough untapped energy
        state.players[p_idx].energy_zone = (0..25).map(|i| (20001 + i) as i32).collect();
        // Populate deck to prevent auto-refresh
        for i in 200..210 {
            state.players[p_idx].deck.push(i);
        }

        state.phase = Phase::Main;
        state.current_player = 0;

        // Verify Legal Actions
        struct Receiver {
            actions: Vec<usize>,
        }
        impl crate::core::logic::game::ActionReceiver for Receiver {
            fn add_action(&mut self, action_id: usize) {
                self.actions.push(action_id);
            }
            fn reset(&mut self) {
                self.actions.clear();
            }
            fn is_empty(&self) -> bool {
                self.actions.is_empty()
            }
        }

        let mut recv = Receiver { actions: vec![] };
        state.generate_legal_actions(&db, p_idx, &mut recv);

        // PlayMember actions are ACTION_BASE_HAND + hand_idx * 3 + slot_idx
        // hand_idx = 0, slot_idx = 0 -> action base+0
        // Since slot 0 is restricted by PREVENT_BATON_TOUCH, baton to slot 0 should NOT be present
        let aid0 = (ACTION_BASE_HAND + 0) as usize;
        let aid1 = (ACTION_BASE_HAND + 1) as usize;
        let aid2 = (ACTION_BASE_HAND + 2) as usize;

        assert!(
            !recv.actions.contains(&aid0),
            "Action {} (Baton Touch on restricted slot) should not be legal. Actions: {:?}",
            aid0,
            recv.actions
        );
        // But playing to empty slots (1 and 2) should be fine
        assert!(
            recv.actions.contains(&aid1),
            "Action {} (Play to empty slot 1) should be legal",
            aid1
        );
        assert!(
            recv.actions.contains(&aid2),
            "Action {} (Play to empty slot 2) should be legal",
            aid2
        );

        // Verify attempt to play fails
        let res = state.play_member(&db, 0, 0);
        assert!(
            res.is_err(),
            "Playing member on restricted slot should return an error"
        );
        let err_msg = res.err().unwrap();
        println!("DEBUG: Actual error message: {}", err_msg);
        assert!(
            err_msg.to_lowercase().contains("baton touch")
                && err_msg.to_lowercase().contains("not allowed"),
            "Error message should mention Baton Touch restriction. Actual: '{}'",
            err_msg
        );
    }
}
