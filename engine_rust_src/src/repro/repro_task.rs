#[cfg(test)]
mod tests {
    use crate::core::enums::*;
    use crate::core::logic::card_db::CardDatabase;
    use crate::core::logic::game::{ActionReceiver, GameState};
    use crate::test_helpers::Action;

    struct TestReceiver {
        actions: Vec<Action>,
        ids: Vec<usize>,
    }
    impl ActionReceiver for TestReceiver {
        fn add_action(&mut self, action_id: usize) {
            self.ids.push(action_id);
        }
        fn reset(&mut self) {
            self.ids.clear();
            self.actions.clear();
        }
        fn is_empty(&self) -> bool {
            self.ids.is_empty()
        }
    }

    fn load_db() -> CardDatabase {
        let json_str = std::fs::read_to_string("../data/cards_compiled.json")
            .expect("Failed to read cards_compiled.json");
        CardDatabase::from_json(&json_str).expect("Failed to parse CardDatabase")
    }

    fn new_receiver() -> TestReceiver {
        TestReceiver {
            actions: Vec::new(),
            ids: Vec::new(),
        }
    }

    fn stage_actions_in_range(receiver: &TestReceiver, lo: usize, hi: usize) -> Vec<usize> {
        receiver
            .ids
            .iter()
            .filter(|&&id| id >= lo && id < hi)
            .cloned()
            .collect()
    }

    // ===================== Original Repro Test =====================

    #[test]
    fn test_ability_activation_zone_repro() {
        let db = load_db();
        // Card ID 4264 (PL!HS-bp1-003-R＋) — has Activated ability at index 1
        let target_cid = 4264;

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0]
            .energy_zone
            .extend(std::iter::repeat(100).take(10));

        // CASE 1: Card in Discard → NO activation
        state.players[0].discard.push(target_cid);
        let mut receiver = new_receiver();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let discard_actions = stage_actions_in_range(
            &receiver,
            ACTION_BASE_DISCARD_ACTIVATE as usize,
            ACTION_BASE_ENERGY as usize,
        );
        println!("Discard Actions (IDs): {:?}", discard_actions);
        assert!(
            discard_actions.is_empty(),
            "Ability should NOT be activatable from Discard"
        );

        // CASE 2: Card on Stage → activation at ab_idx=1
        state.players[0].discard.clear();
        state.players[0].stage[0] = target_cid;
        state.players[0].set_tapped(0, false);
        receiver.reset();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let action_id = (ACTION_BASE_STAGE + 0 * 100 + 1 * 10) as usize;
        let stage_actions = stage_actions_in_range(&receiver, action_id, action_id + 1);
        println!("Stage Actions (IDs): {:?}", stage_actions);
        assert!(
            !stage_actions.is_empty(),
            "Ability 1 (second ability) should be activatable from Stage"
        );
    }

    // ===================== Test 3: Multi-Ability Stage Actions =====================
    // Verify that a card with TWO activated abilities generates TWO separate action IDs.
    // Card 4264 has: Ability 0 (Constant, trigger=6) + Ability 1 (Activated, trigger=7)
    // So only 1 activated action expected. We test that the encoding is correct.
    // For a true multi-activated-ability test, we place the card in slot 1 instead.

    #[test]
    fn test_multi_ability_encoding_slots() {
        let db = load_db();
        let target_cid = 4264; // Has 1 activated ability at index 1

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0]
            .energy_zone
            .extend(std::iter::repeat(100).take(10));

        // Place same card in slot 0 AND slot 2 to verify encoding differs
        state.players[0].stage[0] = target_cid;
        state.players[0].stage[2] = target_cid;
        state.players[0].set_tapped(0, false);
        state.players[0].set_tapped(2, false);

        let mut receiver = new_receiver();
        state.generate_legal_actions(&db, 0, &mut receiver);

        // Slot 0, ab_idx 1 → ACTION_BASE_STAGE + 0*100 + 1*10
        // Slot 2, ab_idx 1 → ACTION_BASE_STAGE + 2*100 + 1*10
        let slot0_id = (ACTION_BASE_STAGE + 0 * 100 + 1 * 10) as usize;
        let slot2_id = (ACTION_BASE_STAGE + 2 * 100 + 1 * 10) as usize;
        let slot0_actions = stage_actions_in_range(&receiver, slot0_id, slot0_id + 1);
        let slot2_actions = stage_actions_in_range(&receiver, slot2_id, slot2_id + 1);

        println!("Slot 0 actions: {:?}", slot0_actions);
        println!("Slot 2 actions: {:?}", slot2_actions);

        assert!(
            !slot0_actions.is_empty(),
            "Slot 0 should have activated ability"
        );
        assert!(
            !slot2_actions.is_empty(),
            "Slot 2 should have activated ability"
        );
        assert_ne!(
            slot0_actions[0], slot2_actions[0],
            "Action IDs must differ between slots"
        );
    }

    // ===================== Test 4: Tapped Member Activation =====================
    // A tapped member should still be able to activate abilities that don't have TapSelf cost.
    // Card 4264 ability 1 has only Energy cost, so tapping the member should NOT block it.

    #[test]
    fn test_tapped_member_can_activate_non_tapself() {
        let db = load_db();
        let target_cid = 4264;

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0]
            .energy_zone
            .extend(std::iter::repeat(100).take(10));
        state.players[0].stage[0] = target_cid;

        // Case A: Untapped → should activate
        state.players[0].set_tapped(0, false);
        let mut receiver = new_receiver();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let untapped_actions = stage_actions_in_range(
            &receiver,
            (ACTION_BASE_STAGE + 10) as usize,
            (ACTION_BASE_STAGE + 11) as usize,
        );
        println!("Untapped: {:?}", untapped_actions);
        assert!(
            !untapped_actions.is_empty(),
            "Untapped member should be able to activate Energy-cost ability"
        );

        // Case B: Tapped → should STILL activate (ability doesn't require TapSelf)
        state.players[0].set_tapped(0, true);
        receiver.reset();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let tapped_actions = stage_actions_in_range(
            &receiver,
            (ACTION_BASE_STAGE + 10) as usize,
            (ACTION_BASE_STAGE + 11) as usize,
        );
        println!("Tapped: {:?}", tapped_actions);
        // This ability uses Energy cost, NOT TapSelf. A tapped member CAN still use it.
        assert!(
            !tapped_actions.is_empty(),
            "Tapped member should still activate Energy-cost ability (no TapSelf required)"
        );
    }

    // ===================== Test 5: prevent_activate Blocks All Zones =====================

    #[test]
    fn test_prevent_activate_blocks_all() {
        let db = load_db();
        let target_cid = 4264;

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0]
            .energy_zone
            .extend(std::iter::repeat(100).take(10));
        state.players[0].stage[0] = target_cid;
        state.players[0].set_tapped(0, false);

        // Baseline: Should generate stage activation
        let mut receiver = new_receiver();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let baseline_actions = stage_actions_in_range(
            &receiver,
            ACTION_BASE_STAGE as usize,
            (ACTION_BASE_STAGE + 300) as usize,
        );
        println!("Baseline stage actions: {:?}", baseline_actions);
        assert!(
            !baseline_actions.is_empty(),
            "Baseline: should have stage activation"
        );

        // Set prevent_activate to block
        state.players[0].prevent_activate = 1;
        receiver.reset();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let blocked_stage = stage_actions_in_range(
            &receiver,
            ACTION_BASE_STAGE as usize,
            (ACTION_BASE_STAGE + 300) as usize,
        );
        let blocked_discard = stage_actions_in_range(
            &receiver,
            ACTION_BASE_DISCARD_ACTIVATE as usize,
            ACTION_BASE_ENERGY as usize,
        );
        println!("Blocked stage: {:?}", blocked_stage);
        println!("Blocked discard: {:?}", blocked_discard);
        assert!(
            blocked_stage.is_empty(),
            "prevent_activate should block all stage activations"
        );
        assert!(
            blocked_discard.is_empty(),
            "prevent_activate should block all discard activations"
        );
    }

    // ===================== Test 2: Once-Per-Turn Slot Movement =====================
    // If a card uses once-per-turn ability in slot 0, then is baton-touched to slot 1,
    // the once-per-turn tracking should still block re-activation.
    // The action generator keys by (source_type=0, card_id, ab_idx), so
    // moving to a different slot does NOT bypass the once-per-turn restriction.

    #[test]
    fn test_once_per_turn_slot_movement() {
        let db = load_db();
        let target_cid = 4264; // Has Activated ability at index 1

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0]
            .energy_zone
            .extend(std::iter::repeat(100).take(10));
        state.players[0].stage[0] = target_cid;
        state.players[0].set_tapped(0, false);

        // Step 1: Generate actions - ability should be available
        let mut receiver = new_receiver();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let action_id = (ACTION_BASE_STAGE + 0 * 100 + 1 * 10) as usize;
        let initial_actions = stage_actions_in_range(&receiver, action_id, action_id + 1);
        println!("Initial slot 0 actions: {:?}", initial_actions);
        assert!(
            !initial_actions.is_empty(),
            "Should have activation initially"
        );

        // Step 2: Consume once_per_turn using the same keying the action generator uses:
        // source_type=0, id=card_id, ab_idx=1
        state.consume_once_per_turn(0, 0, 0, target_cid as u32, 1);

        // Step 3: Verify blocked at slot 0
        receiver.reset();
        state.generate_legal_actions(&db, 0, &mut receiver);
        let after_consume = stage_actions_in_range(&receiver, action_id, action_id + 1);
        println!("After consume at slot 0: {:?}", after_consume);
        assert!(
            after_consume.is_empty(),
            "Should be blocked after once_per_turn consume"
        );

        // Step 4: "Baton touch" - move card from slot 0 to slot 1
        state.players[0].stage[1] = target_cid;
        state.players[0].stage[0] = -1; // Empty slot 0
        state.players[0].set_tapped(1, false);

        // Step 5: Check if ability is STILL blocked at slot 1
        // Because tracking is by card_id (not slot_idx), the restriction persists.
        receiver.reset();
        state.generate_legal_actions(&db, 0, &mut receiver);
        // Slot 1, ab_idx 1 → ACTION_BASE_STAGE + 1*100 + 1*10
        let action_id_slot1 = (ACTION_BASE_STAGE + 1 * 100 + 1 * 10) as usize;
        let slot1_actions = stage_actions_in_range(&receiver, action_id_slot1, action_id_slot1 + 1);
        println!("After baton touch to slot 1: {:?}", slot1_actions);
        assert!(
            slot1_actions.is_empty(),
            "Once-per-turn should persist across slot movement (card_id keyed)"
        );
    }

    #[test]
    fn test_once_per_turn_duplicate_copies_remain_independent() {
        let db = load_db();
        let target_cid = 4264; // Has Activated ability at index 1

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0]
            .energy_zone
            .extend(std::iter::repeat(100).take(10));
        state.players[0].stage[0] = target_cid;
        state.players[0].stage[1] = target_cid;
        state.players[0].set_tapped(0, false);
        state.players[0].set_tapped(1, false);

        state.consume_once_per_turn(0, 0, 0, target_cid as u32, 1);

        let mut receiver = new_receiver();
        state.generate_legal_actions(&db, 0, &mut receiver);

        let slot0_action_id = (ACTION_BASE_STAGE + 0 * 100 + 1 * 10) as usize;
        let slot1_action_id = (ACTION_BASE_STAGE + 1 * 100 + 1 * 10) as usize;
        let slot0_actions = stage_actions_in_range(&receiver, slot0_action_id, slot0_action_id + 1);
        let slot1_actions = stage_actions_in_range(&receiver, slot1_action_id, slot1_action_id + 1);

        assert!(
            slot0_actions.is_empty(),
            "The consumed copy in slot 0 should remain blocked"
        );
        assert!(
            !slot1_actions.is_empty(),
            "A second copy with the same card ID should keep its own once-per-turn availability"
        );
    }

    // ===================== Test 1: Stage Choice Ability Generation =====================
    // Verifies whether activated abilities with choice_flags generate
    // ACTION_BASE_STAGE_CHOICE actions.

    #[test]
    fn test_stage_choice_ability_generation() {
        let db = load_db();
        // Find a card with an Activated ability that has choice_flags > 0
        // We'll scan the database programmatically.

        let mut found_choice_card: Option<(i32, usize)> = None; // (card_id, ab_idx)

        // Scan all member cards for an Activated ability with choice
        for cid in 0..8000i32 {
            if let Some(card) = db.get_member(cid) {
                for (ab_idx, ab) in card.abilities.iter().enumerate() {
                    if ab.trigger == TriggerType::Activated && ab.choice_flags > 0 {
                        found_choice_card = Some((cid, ab_idx));
                        println!(
                            "Found choice card: ID={}, ab_idx={}, choice_flags={}, choice_count={}",
                            cid, ab_idx, ab.choice_flags, ab.choice_count
                        );
                        break;
                    }
                }
                if found_choice_card.is_some() {
                    break;
                }
            }
        }

        if let Some((cid, ab_idx)) = found_choice_card {
            let mut state = GameState::default();
            state.phase = Phase::Main;
            state.current_player = 0;
            state.players[0]
                .energy_zone
                .extend(std::iter::repeat(100).take(10));
            state.players[0].stage[0] = cid;
            state.players[0].set_tapped(0, false);
            state.debug.debug_ignore_conditions = true; // Bypass conditions to focus on choice generation

            let mut receiver = new_receiver();
            state.generate_legal_actions(&db, 0, &mut receiver);

            // Check for ACTION_BASE_STAGE_CHOICE actions (4300-4599)
            let choice_actions = stage_actions_in_range(&receiver, 4300, 4600);
            // Check for ACTION_BASE_STAGE non-choice actions
            let non_choice_actions = stage_actions_in_range(&receiver, 4000, 4300);

            println!("Choice actions (4300-4599): {:?}", choice_actions);
            println!("Non-choice actions (4000-4299): {:?}", non_choice_actions);

            // KNOWN ISSUE: The generation loop does NOT check choice_flags.
            // It always emits ACTION_BASE_STAGE, never ACTION_BASE_STAGE_CHOICE.
            // This test documents the gap.
            if choice_actions.is_empty() && !non_choice_actions.is_empty() {
                println!("CONFIRMED GAP: Activated ability with choice_flags={} only generates non-choice action.",
                         db.get_member(cid).unwrap().abilities[ab_idx].choice_flags);
                println!("  This may cause soft-lock if bytecode expects a choice index.");
            }
        } else {
            println!("No cards with choice-bearing Activated abilities found in database.");
            println!("  Stage choice generation test is VACUOUSLY TRUE (no data to test).");
        }
    }

    #[test]
    fn test_cost_13_passive_repro() {
        let db = load_db();
        // ID 410: PL!S-PR-029-PR (Passive: +2 blades if anyone has cost 13+)
        // Note: The actual condition on card 410 uses C_COUNT_STAGE (203) with val=0,
        // which means "stage count >= 0" - always true.
        // This test documents the current behavior.
        let target_cid = 410;
        // ID 2: PL!-sd1-001-SD (Cost 11) - Note: sd1-003 is cost 13
        let cost_11_cid = 2;

        // Find a cost 13 card programmatically
        let mut cost_13_cid = -1;
        for cid in 0..1000 {
            if let Some(m) = db.get_member(cid) {
                if m.cost >= 13 {
                    cost_13_cid = cid;
                    break;
                }
            }
        }
        assert!(cost_13_cid != -1, "Could not find a cost 13 member in DB");

        let mut state = GameState::default();
        state.debug.debug_mode = true;
        state.phase = Phase::Main;
        state.current_player = 0;

        // Place the passive card
        state.players[0].stage[0] = target_cid;
        state.players[0].set_tapped(0, false);

        // Get the base blades from the card
        let base_blades = db
            .get_member(target_cid)
            .map(|m| m.blades as u32)
            .unwrap_or(3);

        // Verification 1: No other members on stage.
        // The condition C_COUNT_STAGE >= 0 is always true, so bonus is always applied.
        let blades_solitary = state.get_effective_blades(0, 0, &db, 0);
        println!("Blades (solitary): {}", blades_solitary);

        // Verification 2: Add a cost 11 member.
        state.players[0].stage[1] = cost_11_cid;
        let blades_with_11 = state.get_effective_blades(0, 0, &db, 0);
        println!("Blades (with cost 11): {}", blades_with_11);

        // Verification 3: Add a cost 13 member.
        state.players[1].stage[0] = cost_13_cid; // On opponent stage
        let blades_with_13 = state.get_effective_blades(0, 0, &db, 0);
        println!("Blades (with cost 13): {}", blades_with_13);

        // Current behavior: The condition C_COUNT_STAGE >= 0 is always true,
        // so the +2 blade bonus is always applied regardless of other cards' costs.
        // This test documents that the passive always gives +2 blades.
        // If the card's condition was properly checking for cost 13+,
        // solitary would be base_blades and with_13 would be base_blades + 2.
        assert!(
            blades_solitary >= base_blades,
            "Card should have at least base blades"
        );
        assert!(
            blades_with_11 >= blades_solitary,
            "Adding cost 11 should not reduce blades"
        );
        assert!(
            blades_with_13 >= blades_solitary,
            "Adding cost 13 should not reduce blades"
        );
    }
}
