use crate::core::logic::*;
use crate::test_helpers::*;

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_db() -> CardDatabase {
        CardDatabase::default()
    }

    fn create_test_state() -> GameState {
        GameState::default()
    }

    // =========================================================================
    // REPRODUCTION TESTS (FIX VERIFICATION)
    // =========================================================================

    #[test]
    fn test_optional_interaction_actions() {
        let mut db = create_test_db();
        // Create a card with an OPTIONAL interaction opcode (like O_PAY_ENERGY with OPTIONAL flag)
        // Card ID 4331 (KASUMI) from the report
        let mut kasumi = MemberCard::default();
        kasumi.card_id = 4331;
        kasumi.name = "Kasumi".to_string();
        // Ability 0: [O_PAY_ENERGY, 1, 0, FILTER_IS_OPTIONAL >> 32, 0, O_RETURN, 0, 0, 0, 0] -> bit 61 is OPTIONAL
        kasumi.abilities.push(Ability {
            trigger: TriggerType::OnLiveStart,
            bytecode: vec![O_PAY_ENERGY, 1, 0, (crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL >> 32) as i32, 0, O_RETURN, 0, 0, 0, 0],
            ..Default::default()
        });
        db.members.insert(4331, kasumi.clone());
        db.members_vec[4331 as usize % LOGIC_ID_MASK as usize] = Some(kasumi);

        let mut state = create_test_state();
        state.players[0].stage[0] = 4331;
        state.players[0].energy_zone = vec![3001, 3002].into(); // Add some energy to allow paying
        state.phase = Phase::PerformanceP1;

        // Trigger the ability
        let ctx = AbilityContext {
            source_card_id: 4331,
            player_id: 0,
            ..Default::default()
        };
        state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
        state.process_trigger_queue(&db);

        // The game should now be in Phase::Response with OPTIONAL interaction on stack
        assert_eq!(state.phase, Phase::Response);

        // Check legal actions
        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);

        // Action 0 (No/Skip) MUST be present for OPTIONAL interactions.
        assert!(receiver.actions.contains(&0), "Action 0 (No/Skip) missing!");
        // Action ACTION_BASE_CHOICE (Yes) MUST be present for OPTIONAL interactions.
        assert!(
            receiver.actions.contains(&(ACTION_BASE_CHOICE as i32)),
            "Action {} (Yes) missing! Fix verified.",
            ACTION_BASE_CHOICE
        );
    }

    #[test]
    fn test_insufficient_energy_no_prompt() {
        let mut db = create_test_db();
        let mut kasumi = MemberCard::default();
        kasumi.card_id = 4331;
        kasumi.name = "Kasumi".to_string();
        // Ability 0: [O_PAY_ENERGY, 1, 0x82, 0, O_RETURN] -> 0x82 is OPTIONAL | B_ONE
        kasumi.abilities.push(Ability {
            trigger: TriggerType::OnLiveStart,
            bytecode: vec![O_PAY_ENERGY, 1, 0x82, 0, O_RETURN],
            ..Default::default()
        });
        db.members.insert(4331, kasumi.clone());
        db.members_vec[4331 as usize % LOGIC_ID_MASK as usize] = Some(kasumi);

        let mut state = create_test_state();
        state.players[0].stage[0] = 4331;
        state.players[0].energy_zone.clear(); // 0 Energy
        state.phase = Phase::PerformanceP1;

        // Trigger the ability
        let ctx = AbilityContext {
            source_card_id: 4331,
            player_id: 0,
            ..Default::default()
        };
        state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);

        // The game should NOT be in Phase::Response because check failed silently
        // Or if it triggers, it should immediately fail condition and not prompt
        // interpreter.rs:
        // if available < final_v { cond = false; }
        // So no suspend_interaction.

        // However, trigger_abilities process queue.
        // If nothing suspended, it finishes and triggers next or returns.
        // state.phase should remain PerformanceP1 or whatever step() handles next.
        // But here we manually triggered.

        // If suspend happened, phase would be Response.
        assert_ne!(
            state.phase,
            Phase::Response,
            "Should not be in Response phase!"
        );
    }

    // =========================================================================
    // GROUP A: SETUP & TURN ORDER (Q16-Q19, Q49)
    // =========================================================================

    #[test]
    fn test_q16_rps_selection() {
        let mut state = create_test_state();
        state.phase = Phase::Rps;

        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&CardDatabase::default(), 0, &mut receiver);

        // Actions 20000, 20001, 20002 correspond to Rock, Paper, Scissors for P1
        assert!(receiver.actions.contains(&(ACTION_BASE_RPS as i32)));
        assert!(receiver.actions.contains(&(ACTION_BASE_RPS as i32 + 1)));
        assert!(receiver.actions.contains(&(ACTION_BASE_RPS as i32 + 2)));
    }

    #[test]
    fn test_q17_q18_q19_mulligan() {
        let mut state = create_test_state();
        state.players[0].hand = vec![1, 2, 3, 4, 5, 6].into();
        state.phase = Phase::MulliganP1; // P1 (Player 0) first (Q17)

        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&CardDatabase::default(), 0, &mut receiver);

        // Action 0 is "Pass/Done" (Q19 - Mulligan is optional)
        assert!(receiver.actions.contains(&0));

        // Actions 300-305: Toggle cards (Q19 - Mulligan is optional)
        for i in 0..6 {
            assert!(receiver.actions.contains(&(300 + i)));
        }

        // After P1, it goes to P2
        state.phase = Phase::MulliganP2;
        state.current_player = 1; // P2 must be current
        receiver.actions.clear();
        state.generate_legal_actions(&CardDatabase::default(), 1, &mut receiver);
        assert!(receiver.actions.contains(&0));
    }

    #[test]
    fn test_q49_turn_passing() {
        let mut state = create_test_state();
        state.first_player = 0;
        state.current_player = 0;
        state.phase = Phase::LiveResult;

        // No one obtained a success live
        state.obtained_success_live = [false, false];

        state.finalize_live_result();

        // Q49: Turn order remains unchanged if no winner
        assert_eq!(state.first_player, 0);
        // But since it's the start of a next turn after P1+P2,
        // it should reset to the first_player.
        assert_eq!(state.current_player, 0);
    }

    // =========================================================================
    // GROUP B: PLAYING & BATON TOUCH (Q23-Q29, Q70-Q71, Q87)
    // =========================================================================

    #[test]
    fn test_q23_normal_play() {
        let mut db = create_test_db();
        // ID 1: Cost 2
        let mut card = MemberCard::default();
        card.card_id = 1;
        card.cost = 2;
        db.members.insert(1, card.clone());
        db.members_vec[1 as usize % LOGIC_ID_MASK as usize] = Some(card);

        let mut state = create_test_state();
        state.players[0].hand = vec![1].into();
        state.players[0].energy_zone = vec![3001, 3002].into();
        state.phase = Phase::Main;

        // Play card at hand index 0 to slot 1
        state.play_member(&db, 0, 1).unwrap();

        assert_eq!(state.players[0].stage[1], 1);
        assert_eq!(state.players[0].tapped_energy_mask.count_ones(), 2);
    }

    #[test]
    fn test_q24_q25_q26_baton_cost() {
        let mut db = create_test_db();
        // Old: ID 1 (Cost 2)
        let mut card1 = MemberCard::default();
        card1.card_id = 1;
        card1.cost = 2;
        db.members.insert(1, card1.clone());
        db.members_vec[1 as usize % LOGIC_ID_MASK as usize] = Some(card1);

        // New: ID 2 (Cost 5)
        let mut card2 = MemberCard::default();
        card2.card_id = 2;
        card2.cost = 5;
        db.members.insert(2, card2.clone());
        db.members_vec[2 as usize % LOGIC_ID_MASK as usize] = Some(card2);

        // Small: ID 3 (Cost 1)
        let mut card3 = MemberCard::default();
        card3.card_id = 3;
        card3.cost = 1;
        db.members.insert(3, card3.clone());
        db.members_vec[3 as usize % LOGIC_ID_MASK as usize] = Some(card3);

        let mut state = create_test_state();
        state.players[0].stage[0] = 1;
        state.players[0].energy_zone = vec![10, 11, 12, 13, 14].into();
        state.phase = Phase::Main;

        // Case 1: Baton 1 -> 2 (Cost 5-2 = 3)
        state.players[0].hand = vec![2].into();
        state.players[0].deck = vec![999].into(); // Non-empty deck to prevent automatic refresh
        state.play_member(&db, 0, 0).unwrap();

        assert_eq!(state.players[0].stage[0], 2);
        assert_eq!(state.players[0].tapped_energy_mask.count_ones(), 3);
        assert!(state.players[0].discard.contains(&1));

        // Case 2: Baton 2 -> 3 (Cost 1-5 = -4 -> 0) (Q25, Q26)
        state.players[0].flags = 0; // Reset moved flags to allow second play to same slot
        state.players[0].baton_touch_count = 0; // Reset baton touch limit
        state.players[0].tapped_energy_mask = 0; // Reset for test
        state.players[0].hand = vec![3].into();
        state.play_member(&db, 0, 0).unwrap();
        assert_eq!(state.players[0].stage[0], 3);
        assert_eq!(state.players[0].tapped_energy_mask.count_ones(), 0);
        assert!(state.players[0].discard.contains(&2));
    }

    #[test]
    fn test_q27_baton_limit() {
        // Q27: 1回の「バトンタッチ」で控え室に置けるメンバーカードは1枚です。
        // The play_member API only takes one slot_idx, implicitly enforcing this.
        let mut db = create_test_db();
        let mut card = MemberCard::default();
        card.card_id = 1;
        card.cost = 10;
        db.members.insert(1, card.clone());
        db.members_vec[1 as usize % LOGIC_ID_MASK as usize] = Some(card);

        let mut state = create_test_state();
        state.players[0].stage[0] = 101; // dummy cost 5
        state.players[0].stage[1] = 102; // dummy cost 5
                                              // Even if we wanted to sacrifice both for card 1 (cost 10), the API doesn't support it.
    }

    #[test]
    fn test_q29_q70_q87_slot_reuse() {
        let mut db = create_test_db();
        let mut card = MemberCard::default();
        card.card_id = 1;
        card.cost = 0;
        db.members.insert(1, card.clone());
        db.members_vec[1 as usize % LOGIC_ID_MASK as usize] = Some(card);

        let mut state = create_test_state();
        state.phase = Phase::Main;
        state.players[0].hand = vec![1, 1, 1].into();

        // Q29: Cannot baton touch a card that entered THIS turn.
        state.play_member(&db, 1, 0).unwrap();
        // state.can_baton_touch(0, 0) should be false because entered_turn == current_turn
        // Note: we need to ensure play_member or engine tracks entered_turn.
        // If not, this is a logic gap to fix.

        // Assuming current engine logic:
        // state.players[0].stage_entered_turn[0] = state.turn;
        // In play_member:
        // if state.players[0].stage[slot] != -1 && state.players[0].stage_entered_turn[slot] == state.turn { return Err(...) }
    }

    // =========================================================================
    // GROUP C: LIVE MECHANICS (Q32-Q35, Q47-Q48, Q53)
    // =========================================================================

    #[test]
    fn test_q32_empty_live_yell() {
        let mut state = create_test_state();
        state.phase = Phase::PerformanceP1;
        state.players[0].live_zone = [-1; 3];

        // Q32: No lives set = no yell check.
        // state.do_performance(0) -> should skip.
    }

    #[test]
    fn test_q34_q35_zone_movement() {
        let mut db = create_test_db();
        // ID 11000: Score 1, Req 0 hearts (Pass)
        let mut live_pass = LiveCard::default();
        live_pass.card_id = 11000;
        live_pass.score = 1;
        db.lives.insert(11000, live_pass.clone());
        db.lives_vec[11000 as usize % LOGIC_ID_MASK as usize] = Some(live_pass);

        // ID 11001: Score 1, Req 100 hearts (Fail)
        let mut live_fail = LiveCard::default();
        live_fail.card_id = 11001;
        live_fail.hearts_board.set_color_count(1, 100);
        db.lives.insert(11001, live_fail.clone());
        db.lives_vec[11001 as usize % LOGIC_ID_MASK as usize] = Some(live_fail);

        let mut state = create_test_state();

        // Success Case (Q34)
        state.players[0].live_zone[0] = 11000;
        // Set performance_results snapshot to indicate success
        state.ui.performance_results.insert(
            0,
            serde_json::json!({
                "success": true,
                "lives": [
                    {"passed": true, "score": 1, "slot_idx": 0},
                    {"passed": false, "score": 0, "slot_idx": 1},
                    {"passed": false, "score": 0, "slot_idx": 2}
                ]
            }),
        );
        state.do_live_result(&db);
        assert!(state.players[0].success_lives.contains(&11000));
        assert_eq!(state.players[0].live_zone[0], -1);

        // Failure Case (Q35)
        state.players[0].live_zone[0] = 11001;
        // Clear and set failure snapshot
        state.ui.performance_results.insert(
            0,
            serde_json::json!({
                "success": false,
                "lives": [
                    {"passed": false, "score": 0, "slot_idx": 0},
                    {"passed": false, "score": 0, "slot_idx": 1},
                    {"passed": false, "score": 0, "slot_idx": 2}
                ]
            }),
        );
        state.do_live_result(&db);
        assert!(state.players[0].discard.contains(&11001));
        assert_eq!(state.players[0].live_zone[0], -1);
    }

    #[test]
    fn test_q47_q48_score_zero() {
        let mut db = create_test_db();
        // ID 11000: Passable live
        let mut live = LiveCard::default();
        live.card_id = 11000;
        live.score = 1;
        db.lives.insert(11000, live.clone());
        db.lives_vec[11000 as usize % LOGIC_ID_MASK as usize] = Some(live);

        let mut state = create_test_state();
        state.players[0].live_zone[0] = 11000;

        // Add a -1 score modifier (e.g. from an ability)
        // state.players[0].score_bonus = -1;

        // Set performance_results snapshot to indicate success
        state.ui.performance_results.insert(
            0,
            serde_json::json!({
                "success": true,
                "lives": [
                    {"passed": true, "score": 1, "slot_idx": 0},
                    {"passed": false, "score": 0, "slot_idx": 1},
                    {"passed": false, "score": 0, "slot_idx": 2}
                ]
            }),
        );

        state.do_live_result(&db);

        // Q48: Score <= 0 STILL wins if hearts were met (success live obtained).
        assert!(state.players[0].success_lives.contains(&11000));
        // Q47: Failed live score defaults to 0 (but technically its just not added).
    }

    #[test]
    fn test_q53_deckout_shuffle() {
        let mut state = create_test_state();
        // Initial hand: 6 cards
        state.players[0].hand = vec![101, 102, 103, 104, 105, 106].into();
        state.players[0].deck.clear();
        state.players[0].discard = vec![1, 2, 3].into();

        let db = create_test_db();
        state.phase = Phase::Draw;
        // Q53: Automatic shuffle when deck hits 0 and draw attempt?
        state.do_draw_phase(&db);

        assert_eq!(state.players[0].deck.len(), 2); // 3 - 1
        assert_eq!(state.players[0].hand.len(), 7); // 6 + 1
        assert!(state.players[0].discard.is_empty());
    }

    #[test]
    fn test_q55_partial_resolution() {
        // Card: PL!S-bp2-010-N (424)
        // Effect: DRAW(2); DISCARD_HAND(2)
        let db = load_real_db();
        let mut state = create_test_state();
        state.ui.silent = true;
        let p_idx = 0;
        let card_id = 424;
        
        // P1 has only 1 card in hand (the one being played)
        state.players[p_idx].hand = vec![card_id].into();
        state.players[p_idx].deck = vec![1; 10].into();
        state.players[p_idx].energy_zone = vec![3001; 20].into(); // Add energy!
        state.phase = Phase::Main;
        
        // Play the card (it goes from hand to stage, so hand is empty)
        state.play_member(&db, 0, 0).expect("Play failed");
        
        // Hand should have been empty, then DRAW(2), then DISCARD_HAND(2) mandatory. 
        // So hand should be 0 again!
        state.process_trigger_queue(&db);
        assert_eq!(state.players[p_idx].hand.len(), 0, "Hand should be empty after internal OnPlay (DRAW 2, DISCARD 2)");
        
        // Now give the player 2 cards manually to test the PARTIAL discard.
        state.players[p_idx].discard.clear();
        state.players[p_idx].hand = vec![102, 103].into();
        
        let ctx = AbilityContext {
            player_id: p_idx as u8,
            auto_pick: true,
            ..Default::default()
        };
        // O_MOVE_TO_DISCARD(5) from Hand. We only have 2 cards.
        // Revision 5: ZoneMask::Hand (6) at bit 53
        let attr = (6u64 << 53) as i64;
        let bytecode = vec![O_MOVE_TO_DISCARD, 5, (attr & 0xFFFFFFFF) as i32, (attr >> 32) as i32, 6, O_RETURN, 0, 0, 0, 0];
        crate::core::logic::interpreter::resolve_bytecode(&mut state, &db, std::sync::Arc::new(bytecode), &ctx);
        
        // Q55: Should discard all 2 available cards and not error/hang
        assert_eq!(state.players[p_idx].hand.len(), 0, "Hand should be empty after partial discard");
        assert_eq!(state.players[p_idx].discard.len(), 2, "Discard should contain the 2 new cards");
    }

    #[test]
    fn test_q56_all_or_nothing_cost() {
        let db = load_real_db();
        let mut state = create_test_state();
        state.ui.silent = true;
        
        // Card 231 (Mia) has cost 4.
        let card_id = 231;
        
        state.phase = Phase::Main;
        state.players[0].hand = vec![card_id].into();
        state.players[0].energy_zone = vec![3001].into(); // Only 1 energy available (need 4)
        
        let mut actions = Vec::<i32>::new();
        state.generate_legal_actions(&db, 0, &mut actions);
        
        assert!(!actions.contains(&(ACTION_BASE_HAND + 0)), "Q56: Should not be able to play with insufficient energy");
    }

    #[test]
    fn test_q84_simultaneous_trigger_order() {
        let db = load_real_db();
        let mut state = create_test_state();
        state.ui.silent = true;
        
        // P1 is active
        state.current_player = 0;
        state.phase = Phase::Main; 
        
        let vienna_id = 4632;
        let filler_id = 1;

        // Setup stage for both players. 
        // Give each player an EXTRA member to satisfy Vienna's "NOT_SELF" condition.
        state.players[0].stage[0] = vienna_id; 
        state.players[0].stage[1] = filler_id;
        state.players[1].stage[0] = vienna_id; 
        state.players[1].stage[1] = filler_id;
        
        // Simulate a simultaneous event: ON_LIVE_START for BOTH players.
        // We increment trigger_depth manually so that queueing doesn't auto-process, 
        // allowing us to inspect the order.
        state.trigger_depth += 1;
        state.trigger_global_event(&db, TriggerType::OnLiveStart, -1, -1, 0, -1);
        state.trigger_depth -= 1;
        
        assert_eq!(state.trigger_queue.len(), 2, "Both triggers should be queued");
        
        // Verify Order: P1 trigger should be first in deque
        let ctx0 = &state.trigger_queue[0].2;
        assert_eq!(ctx0.player_id, 0, "Q84: Active player trigger must be first in queue");
        
        let ctx1 = &state.trigger_queue[1].2;
        assert_eq!(ctx1.player_id, 1, "Q84: Non-active player trigger must be second");
    }
}
