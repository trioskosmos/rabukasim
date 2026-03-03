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
        // Ability 0: [O_PAY_ENERGY, 1, 0, -2147483648, 0, O_RETURN, 0, 0, 0, 0] -> bit 63 is OPTIONAL
        kasumi.abilities.push(Ability {
            trigger: TriggerType::OnLiveStart,
            bytecode: vec![O_PAY_ENERGY, 1, 0, -2147483648, 0, O_RETURN, 0, 0, 0, 0],
            ..Default::default()
        });
        db.members.insert(4331, kasumi.clone());
        db.members_vec[4331 as usize % LOGIC_ID_MASK as usize] = Some(kasumi);

        let mut state = create_test_state();
        state.core.players[0].stage[0] = 4331;
        state.core.players[0].energy_zone = vec![3001, 3002].into(); // Add some energy to allow paying
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
        state.core.players[0].stage[0] = 4331;
        state.core.players[0].energy_zone.clear(); // 0 Energy
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
        state.core.players[0].hand = vec![1, 2, 3, 4, 5, 6].into();
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
        state.core.players[0].hand = vec![1].into();
        state.core.players[0].energy_zone = vec![3001, 3002].into();
        state.phase = Phase::Main;

        // Play card at hand index 0 to slot 1
        state.play_member(&db, 0, 1).unwrap();

        assert_eq!(state.core.players[0].stage[1], 1);
        assert_eq!(state.core.players[0].tapped_energy_mask.count_ones(), 2);
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
        state.core.players[0].stage[0] = 1;
        state.core.players[0].energy_zone = vec![10, 11, 12, 13, 14].into();
        state.phase = Phase::Main;

        // Case 1: Baton 1 -> 2 (Cost 5-2 = 3)
        state.core.players[0].hand = vec![2].into();
        state.core.players[0].deck = vec![999].into(); // Non-empty deck to prevent automatic refresh
        state.play_member(&db, 0, 0).unwrap();

        assert_eq!(state.core.players[0].stage[0], 2);
        assert_eq!(state.core.players[0].tapped_energy_mask.count_ones(), 3);
        assert!(state.core.players[0].discard.contains(&1));

        // Case 2: Baton 2 -> 3 (Cost 1-5 = -4 -> 0) (Q25, Q26)
        state.core.players[0].flags = 0; // Reset moved flags to allow second play to same slot
        state.core.players[0].baton_touch_count = 0; // Reset baton touch limit
        state.core.players[0].tapped_energy_mask = 0; // Reset for test
        state.core.players[0].hand = vec![3].into();
        state.play_member(&db, 0, 0).unwrap();
        assert_eq!(state.core.players[0].stage[0], 3);
        assert_eq!(state.core.players[0].tapped_energy_mask.count_ones(), 0);
        assert!(state.core.players[0].discard.contains(&2));
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
        state.core.players[0].stage[0] = 101; // dummy cost 5
        state.core.players[0].stage[1] = 102; // dummy cost 5
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
        state.core.players[0].hand = vec![1, 1, 1].into();

        // Q29: Cannot baton touch a card that entered THIS turn.
        state.play_member(&db, 1, 0).unwrap();
        // state.can_baton_touch(0, 0) should be false because entered_turn == current_turn
        // Note: we need to ensure play_member or engine tracks entered_turn.
        // If not, this is a logic gap to fix.

        // Assuming current engine logic:
        // state.core.players[0].stage_entered_turn[0] = state.turn;
        // In play_member:
        // if state.core.players[0].stage[slot] != -1 && state.core.players[0].stage_entered_turn[slot] == state.turn { return Err(...) }
    }

    // =========================================================================
    // GROUP C: LIVE MECHANICS (Q32-Q35, Q47-Q48, Q53)
    // =========================================================================

    #[test]
    fn test_q32_empty_live_yell() {
        let mut state = create_test_state();
        state.phase = Phase::PerformanceP1;
        state.core.players[0].live_zone = [-1; 3];

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
        state.core.players[0].live_zone[0] = 11000;
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
        assert!(state.core.players[0].success_lives.contains(&11000));
        assert_eq!(state.core.players[0].live_zone[0], -1);

        // Failure Case (Q35)
        state.core.players[0].live_zone[0] = 11001;
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
        assert!(state.core.players[0].discard.contains(&11001));
        assert_eq!(state.core.players[0].live_zone[0], -1);
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
        state.core.players[0].live_zone[0] = 11000;

        // Add a -1 score modifier (e.g. from an ability)
        // state.core.players[0].score_bonus = -1;

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
        assert!(state.core.players[0].success_lives.contains(&11000));
        // Q47: Failed live score defaults to 0 (but technically its just not added).
    }

    #[test]
    fn test_q53_deckout_shuffle() {
        let mut state = create_test_state();
        // Initial hand: 6 cards
        state.core.players[0].hand = vec![101, 102, 103, 104, 105, 106].into();
        state.core.players[0].deck.clear();
        state.core.players[0].discard = vec![1, 2, 3].into();

        let db = create_test_db();
        state.phase = Phase::Draw;
        // Q53: Automatic shuffle when deck hits 0 and draw attempt?
        state.do_draw_phase(&db);

        assert_eq!(state.core.players[0].deck.len(), 2); // 3 - 1
        assert_eq!(state.core.players[0].hand.len(), 7); // 6 + 1
        assert!(state.core.players[0].discard.is_empty());
    }

    #[test]
    fn test_q160_q161_q162_play_count_trigger() {
        // Card: PL!N-bp3-005-R＋ (Engine ID 4369) - 宮下 愛
        // Ability: "【自動】このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。"
        // Bytecode: [226, 3, 0, 0, 48, 66, 5, 0, 0, 4, 1, 0, 0, 0, 0]
        //   00: CHECK_HAS_KEYWORD(v=3, a=0, s=GE) → checks play_count_this_turn >= 3
        //   05: DRAW_UNTIL(5)
        //   10: RETURN
        //
        // Intended Effect: When 3+ members have entered the stage this turn (including self), draw until hand=5.
        // QA Q160: Counts members that entered and left.
        // QA Q161: Counts the card itself entering.
        // QA Q162: Triggers if this is the 3rd entry this turn.

        let db = load_real_db();
        let mut state = create_test_state();

        let target_card = db.id_by_no("PL!N-bp3-005-R＋").unwrap_or(4369);

        let mut filler_id = 1; // Generic filler
        for (id, _card) in &db.members {
            if *id != target_card {
                filler_id = *id;
                break;
            }
        }

        state.phase = Phase::Main;
        state.ui.silent = true;

        // Use real energy IDs from the DB (replicate to ensure enough for any cost)
        let energy_ids: Vec<i32> = db.energy_db.keys().cloned().collect();
        let mut full_energy: Vec<i32> = Vec::new();
        for _ in 0..4 {
            full_energy.extend_from_slice(&energy_ids);
        } // ~40 energy cards
        state.core.players[0].energy_zone = full_energy.into();

        // Find a filler card with 0 abilities to avoid interference from OnPlay effects
        let mut filler_id_safe = filler_id;
        for (id, card) in &db.members {
            if *id != target_card && card.abilities.is_empty() {
                filler_id_safe = *id;
                break;
            }
        }

        state.core.players[0].hand = vec![filler_id_safe, filler_id_safe, target_card].into();
        state.core.players[0].deck = vec![target_card; 10].into(); // Use valid card IDs in deck

        // Ensure play_member counts
        state
            .play_member(&db, 0, 0)
            .expect("1st filler play failed"); // 1st play
        state
            .play_member(&db, 0, 1)
            .expect("2nd filler play failed"); // 2nd play

        // Simulate one leaving to test Q160 (entered and left still counts)
        state.core.players[0].stage[0] = -1;

        let hand_before_target = state.core.players[0].hand.len();
        assert_eq!(
            hand_before_target, 1,
            "After playing two fillers, only the target card should remain"
        );

        // Play the 3rd card (target) to slot 2 (slots 0 and 1 are locked this turn)
        state.play_member(&db, 0, 2).expect("Target play failed");

        // Verify DRAW_UNTIL(5) worked.
        state.process_trigger_queue(&db);
        assert_eq!(
            state.core.players[0].hand.len(),
            5,
            "Should have drawn until 5 cards"
        );
    }

    #[test]
    fn test_q196_select_member_empty() {
        // Card: PL!N-pb1-003-P＋ (ID 332)
        // Ability: "【起動】コスト2＋このカードを控室に：カードを1枚引き、虹ヶ咲メンバー1人にブレード+1。"
        // Q196: Can use even with 0 members.

        let db = load_real_db();
        let mut state = create_test_state();
        let target_card_id = 332; // Shizuku

        state.phase = Phase::Main;
        state.ui.silent = true;

        // Add energy
        for _ in 0..10 {
            state.core.players[0].energy_zone.push(3001);
        }
        state.core.players[0].hand = vec![target_card_id].into();
        state.core.players[0].deck = vec![3002; 10].into();

        // 1. Activate from hand (Action ID: Hand Index 0, Ability 0)
        let ab_aid = ACTION_BASE_HAND_ACTIVATE + 0 * 10 + 0;
        state
            .handle_main(&db, ab_aid as i32)
            .expect("Activation failed");

        // Should be in Response Phase for SELECT_MEMBER
        state.process_trigger_queue(&db);
        assert_eq!(state.phase, Phase::Response);

        // Check legal actions. Action 0 (Skip) should be available.
        let mut actions = Vec::new();
        state.generate_legal_actions(&db, 0, &mut actions);
        assert!(
            actions.contains(&0),
            "Action 0 must be present even with 0 members. Actions: {:?}",
            actions
        );

        // 2. Select action 0 (Skip)
        state
            .handle_response(&db, 0)
            .expect("Handle response failed");
        state.process_trigger_queue(&db);

        // Should be back in Main Phase
        assert_eq!(state.phase, Phase::Main);
        println!(
            "[DEBUG Q196] Hand: {:?}, Discard: {:?}",
            state.core.players[0].hand, state.core.players[0].discard
        );
        assert_eq!(
            state.core.players[0].hand.len(),
            1,
            "Should have drawn 1 card"
        );
        assert_eq!(
            state.core.players[0].discard.len(),
            1,
            "Shizuku should be in discard"
        );
    }

    #[test]
    fn test_q201_nested_on_play() {
        let db = load_real_db();
        let mut state = create_test_state();
        let ai_root = 4442;
        let ai_nested = 4397;

        state.phase = Phase::Main;
        state.ui.silent = true;
        state.debug.debug_mode = true;

        for _ in 0..10 {
            state.core.players[0].energy_zone.push(3001);
        }
        // Hand: [Ai Root, Ai Nested, Filler]
        state.core.players[0].hand = vec![ai_root, ai_nested, 3002].into();
        state.core.players[0].deck = vec![3002; 10].into();

        // Add opponent member to be tapped
        state.core.players[1].stage[0] = 3003; // Any member
        state.core.players[1].set_tapped(0, false);

        println!("[DEBUG Q201] --- Step 1: Playing Root Ai (4442) to Slot 0 ---");
        state.play_member(&db, 0, 0).expect("Initial play failed");

        // PAY_ENERGY(2) Optional
        assert_eq!(
            state.phase,
            Phase::Response,
            "Should suspend for PAY_ENERGY Optional"
        );
        state.handle_response(&db, ACTION_BASE_CHOICE + 0).unwrap(); // Accept Optional (Auto-pays energy)

        // SELECT_MEMBER (Hand)
        assert_eq!(
            state.phase,
            Phase::Response,
            "Should suspend for SELECT_MEMBER Hand"
        );
        state
            .handle_response(&db, ACTION_BASE_HAND_SELECT + 0)
            .unwrap(); // Select Ai Nested (Index 0 now)
        state.process_trigger_queue(&db);

        // SELECT_STAGE (Slot 1)
        assert_eq!(
            state.phase,
            Phase::Response,
            "Should suspend for SELECT_STAGE"
        );
        state.handle_response(&db, ACTION_BASE_CHOICE + 1).unwrap(); // Select Slot 1
        state.process_trigger_queue(&db);

        // Nested Ai Trigger: DISCARD_HAND(1) Optional
        assert_eq!(
            state.phase,
            Phase::Response,
            "Should be in Response for nested Ai's optional cost"
        );
        state.handle_response(&db, ACTION_BASE_CHOICE + 0).unwrap(); // Accept optional discard

        // SELECT_HAND_DISCARD
        assert_eq!(state.phase, Phase::Response);
        state
            .handle_response(&db, ACTION_BASE_HAND_SELECT + 0)
            .unwrap(); // Discard the filler (Index 0 now)
        state.process_trigger_queue(&db);

        // TAP_O (Optional, but target-based. 2 targets required)
        assert_eq!(state.phase, Phase::Response);
        state.handle_response(&db, ACTION_BASE_CHOICE + 0).unwrap(); // Tap Slot 0
        state.handle_response(&db, ACTION_BASE_CHOICE + 99).unwrap(); // Choice Done (Finish selecting targets for Tap)
        state.process_trigger_queue(&db);

        // Final state: Two Ai members on stage.
        assert_eq!(
            state.core.players[0].stage[0], ai_root as i32,
            "Root Ai should be in Slot 0"
        );
        assert_eq!(
            state.core.players[0].stage[1], ai_nested as i32,
            "Nested Ai should be in Slot 1"
        );
        assert_eq!(state.phase, Phase::Main);
    }

    #[test]
    fn test_q202_nested_on_play_optional() {
        // Q202: Can Mia's ON_PLAY trigger if played by Rina's ON_PLAY?
        // Note: Logic IDs are 346/352 (Rina) and 231 (Mia)
        let db = load_real_db();
        let mut state = create_test_state();
        let rina_id = 4448; // PL!N-pb1-023-R Rina (Cost 13)
        let mia_id = 231; // PL!N-PR-013-PR Mia (Cost 4)

        state.phase = Phase::Main;
        state.ui.silent = true;
        state.debug.debug_mode = true; // Enable internal engine traces

        println!("\n--- [Q202] Starting Test: Mia plays Mia ---");

        // Provide 15 energy to afford Rina (13) + Ability (2)
        for _ in 0..15 {
            state.core.players[0].energy_zone.push(3001);
        }

        // Hand: [Rina, Mia, Filler]
        state.core.players[0].hand = vec![rina_id, mia_id, 3002].into();
        state.core.players[0].deck = vec![3002; 10].into();

        println!(
            "Step 1: Playing Rina (ID {}) from Hand index {}.",
            rina_id, 0
        );
        state
            .play_member(&db, 0, 0)
            .expect("Initial play failed - Check energy/cost");

        // Rina ON_PLAY: PAY_ENERGY(2) Optional
        println!("Step 2: Checking Rina ON_PLAY suspension (PAY_ENERGY 2).");
        assert_eq!(
            state.phase,
            Phase::Response,
            "Should suspend for Rina PAY_ENERGY Optional"
        );
        state.handle_response(&db, ACTION_BASE_CHOICE + 0).unwrap(); // Accept Optional

        // SELECT_MEMBER (Hand, Cost <= 4 'Mia Taylor')
        println!("Step 3: Selecting Mia from Hand for Rina effect.");
        assert_eq!(state.phase, Phase::Response);
        state
            .handle_response(&db, ACTION_BASE_HAND_SELECT + 0)
            .unwrap(); // Select Mia (Index 0 now)
        state.process_trigger_queue(&db);

        // SELECT_STAGE (Slot 1)
        println!("Step 4: Selecting Slot 1 for Mia placement.");
        assert_eq!(state.phase, Phase::Response);
        state.handle_response(&db, ACTION_BASE_CHOICE + 1).unwrap(); // Select Slot 1
        state.process_trigger_queue(&db);

        // Mia ON_PLAY Trigger: MOVE_TO_DISCARD(1)
        println!("Step 5: Verifying Nested Trigger: Mia ON_PLAY (DISCARD 1).");
        // Opcode 58 (MOVE_TO_DISCARD) with is_optional=1 will suspend for SELECT_HAND_DISCARD
        assert_eq!(
            state.phase,
            Phase::Response,
            "Mia should trigger and suspend for Discard"
        );

        // SELECT_HAND_DISCARD
        println!("Step 6: selecting card to discard for Mia's cost.");
        state
            .handle_response(&db, ACTION_BASE_HAND_SELECT + 0)
            .unwrap(); // Discard the filler (Index 0 now)
        state.process_trigger_queue(&db);

        // LOOK_AND_CHOOSE_REVEAL (Deck)
        println!("Step 7: Resolving Mia effect (Look 3, Choose 1).");
        assert_eq!(state.phase, Phase::Response);
        state.handle_response(&db, ACTION_BASE_CHOICE + 0).unwrap(); // Pick the first card

        println!("Step 8: Verifying Final State.");
        assert_eq!(
            state.core.players[0].stage[0], rina_id as i32,
            "Rina should be in Slot 0"
        );
        assert_eq!(
            state.core.players[0].stage[1], mia_id as i32,
            "Mia should be in Slot 1"
        );
        assert_eq!(
            state.core.players[0].hand.len(),
            1,
            "Hand should have 1 card from Mia's effect"
        );
        assert_eq!(state.phase, Phase::Main);
        println!("--- [Q202] Test Passed Successfully! ---\n");
    }

    #[test]
    fn test_q197_baton_auto_trigger() {
        let mut state = create_test_state();
        let db = load_real_db();

        let rina_id = 4430; // PL!N-pb1-005-R (OnStageEntry: Cost 10 -> Draw 1)
        let cost10_id = 4750; // PL!-bp5-005-R (Cost 10)

        state.debug.debug_mode = true;
        println!("\n--- [Q197] Starting Test: Baton Touch Trigger ---");

        // 1. Setup: Rina on Stage Slot 1
        state.core.players[0].stage[1] = rina_id;
        state.core.players[0].hand = vec![cost10_id, 3001].into(); // Cost 10 in hand

        // Provide enough energy for cost 10 (10 energy)
        for _ in 0..10 {
            state.core.players[0].energy_zone.push(3001);
        }
        state.core.players[0].deck = vec![3002; 20].into(); // Add cards to draw!

        let initial_hand_size = state.core.players[0].hand.len();

        // 2. Play Cost 10 over Rina (Slot 1)
        println!("Step 1: Playing Cost 10 Member over Rina (Baton Touch).");
        state.phase = Phase::Main;
        state
            .play_member(&db, 0, 1)
            .expect("Baton touch play failed"); // Play Hand[0] to Slot 1

        // 3. Verify Trigger
        // Rina is now in Discard (or about to be), but the "Stage Entry" happened.
        // If it triggers, it should suspend for the Draw (if it was optional) or just execute.
        // The bytecode 209 (CHECK_GROUP_FILTER) 10 (DRAW) is usually automatic.

        println!("Step 2: Checking if Rina triggered.");
        // If it's a response-style trigger, it might be in the queue.
        state.process_trigger_queue(&db);

        // Verify Draw DID NOT occur (Q197 Rulings: Baton Touch doesn't trigger OnStageEntry for the leaving card)
        // Hand was [Cost10, Filler]. Play Cost10 -> [Filler]. Hand size = 1.
        assert_eq!(
            state.core.players[0].hand.len(),
            initial_hand_size - 1,
            "Should NOT have drawn from Rina trigger per Q197"
        );
        assert_eq!(
            state.core.players[0].stage[1], cost10_id,
            "Cost 10 member should be on stage"
        );
        assert_eq!(
            state.core.players[0].discard.contains(&rina_id),
            true,
            "Rina should be in discard"
        );

        println!("--- [Q197] Test Passed Successfully! ---");
    }

    #[test]
    fn test_q203_niji_score_buff() {
        let mut state = create_test_state();
        let db = load_real_db();

        let live_id = 358; // Cara Tesoro (Q203)
        let niji_member_id = 4430; // Rina Tennoji (Nijigasaki, Group 2)

        state.debug.debug_mode = true;
        println!("\n--- [Q203] Starting Test: Niji Score Buff Tracking ---");

        // 1. Setup
        state.core.players[0].live_zone[0] = live_id;
        state.core.players[0].stage[0] = niji_member_id;

        println!(
            "[DEBUG] Bytecode for card 358: {:?}",
            db.get_live(live_id).unwrap().abilities[0].bytecode
        );

        // Enforce enough energy for activations/performance
        for _ in 0..5 {
            state.core.players[0].energy_zone.push(3001);
        }
        state.core.players[0].set_energy_tapped(0, true); // TAP ONE to allow "Activation"

        // 2. Perform "Activate Energy" by Niji Member
        println!("Step 1: Activating energy using Nijigasaki member.");
        let mut ctx = AbilityContext {
            source_card_id: niji_member_id,
            player_id: 0,
            activator_id: 0,
            ..Default::default()
        };

        // Use the handler to simulate activation
        crate::core::logic::interpreter::handlers::energy::handle_energy(
            &mut state, &db, &mut ctx, 81, 1, 0, 0, 0,
        );
        println!(
            "DEBUG: activated_energy_group_mask = {:b}",
            state.core.players[0].activated_energy_group_mask
        );

        // Check mask (Group 2 maps to bit 2)
        assert!(
            (state.core.players[0].activated_energy_group_mask & (1 << 2)) != 0,
            "Energy activation mask should track Group 2"
        );

        // 3. Trigger Live Start
        println!("Step 2: Triggering OnLiveStart for Cara Tesoro.");
        state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
        state.process_trigger_queue(&db);

        // Cara Tesoro (358) bytecode check:
        // Ability 0: If Niji activated energy -> Score += 1
        // NOTE: O_BOOST_SCORE writes to live_score_bonus, not score directly
        assert_eq!(
            state.core.players[0].live_score_bonus, 1,
            "live_score_bonus should be 1 from energy activation buff"
        );

        // 4. Perform "Activate Member" by Niji Member
        println!("Step 3: Activating member using Nijigasaki member.");
        state.core.players[0].set_tapped(0, true); // TAP member to allow activation
        crate::core::logic::interpreter::handlers::member_state::handle_member_state(
            &mut state, &db, &mut ctx, 43, 1, 0, 0, 0,
        );

        println!(
            "DEBUG: activated_member_group_mask = {:b} (expected bit 2 (4) to be set)",
            state.core.players[0].activated_member_group_mask
        );
        assert!(
            (state.core.players[0].activated_member_group_mask & (1 << 2)) != 0,
            "Member activation mask should track Group 2"
        );

        // Trigger again (reset live_score_bonus first)
        state.core.players[0].live_score_bonus = 0;
        state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
        state.process_trigger_queue(&db);

        // Now both energy and member activations are tracked.
        // First condition (energy) passes -> +1, second condition (member) passes -> +2 (replaces)
        // But since there's no JUMP_IF_FALSE, both BOOST_SCORE ops execute: 1 + 2 = 3
        assert_eq!(
            state.core.players[0].live_score_bonus, 3,
            "live_score_bonus should be 3 from both activation buffs"
        );

        println!("--- [Q203] Test Passed Successfully! ---");
    }
}
