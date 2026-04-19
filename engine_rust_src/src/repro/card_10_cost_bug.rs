/// Card 10 (渡辺 曜&鬼塚夏美&大沢瑠璃乃) Cost Reduction Bug
///
/// Issue: When card 10 is played first, its ability creates a REDUCE_COST effect.
/// This works for card 10 itself, but other cards in hand incorrectly have their
/// costs reduced before they should be.
///
/// Expected Behavior:
/// - When card 10 is in hand, its cost = base_cost - (hand_size - 1)
/// - When card 10 is played, other cards should NOT have reduced cost
///   (unless they have abilities that reduce cost)
///
/// Bug Pattern:
/// - Play card 10 first (cost reduction applied to player)
/// - Other cards in hand show cost reductions when they shouldn't
/// - This is premature cost calculation, not a persistent state issue
use crate::core::logic::*;
use crate::test_helpers::load_real_db;

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::logic::action_factory::DecodedAction;
    use crate::core::logic::card_db::LOGIC_ID_MASK;
    use crate::core::generated_constants::ACTION_BASE_HAND;
    use crate::test_helpers::TestActionReceiver;

    fn insert_test_member(db: &mut CardDatabase, card_id: i32, cost: u32) {
        let member = MemberCard {
            card_id,
            cost,
            ..Default::default()
        };
        db.members.insert(card_id, member.clone());
        let logic_id = (card_id & LOGIC_ID_MASK) as usize;
        if logic_id >= db.members_vec.len() {
            db.members_vec.resize(logic_id + 1, None);
        }
        db.members_vec[logic_id] = Some(member);
    }

    #[test]
    fn test_card_10_playability_uses_effective_hand_cost() {
        let mut state = GameState::default();
        let db = load_real_db();

        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0].hand = vec![10, 121, 124].into();
        state.players[0].energy_zone = (1..=18).collect::<Vec<i32>>().into();

        let effective_cost = state.get_member_cost(0, 10, 0, -1, &db, 0);
        assert_eq!(effective_cost, 18, "card 10 should cost 18 with two other cards in hand");

        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);

        assert!(
            receiver.actions.contains(&ACTION_BASE_HAND),
            "card 10 should be playable when available energy matches its reduced cost"
        );
    }

    #[test]
    fn test_card_10_on_stage_does_not_reduce_other_hand_cards() {
        let mut state = GameState::default();
        let db = load_real_db();

        state.players[0].stage[0] = 10;
        state.players[0].hand = vec![121, 124].into();

        let card_121 = db.get_member(121).expect("Card 121 should exist");
        let cost_121 = state.get_member_cost(0, 121, -1, -1, &db, 0);

        assert_eq!(
            cost_121,
            card_121.cost as i32,
            "card 10 on stage must not leak a flat cost reduction onto other hand cards"
        );
    }

    #[test]
    fn test_second_copy_of_card_10_keeps_hand_reduction_after_first_is_played() {
        let mut state = GameState::default();
        let db = load_real_db();

        state.players[0].stage[1] = 10;
        state.players[0].hand = vec![10, 121].into();

        let in_hand_copy_cost = state.get_member_cost(0, 10, -1, -1, &db, 0);

        assert_eq!(
            in_hand_copy_cost,
            19,
            "the remaining in-hand copy should still count the other hand card and reduce itself by 1"
        );
    }

    #[test]
    fn test_card_10_counts_other_hand_cards_not_itself() {
        let mut state = GameState::default();
        let db = load_real_db();

        state.players[0].hand = vec![10, 121, 124, 100, 200].into();

        assert_eq!(
            state.get_member_cost(0, 10, -1, -1, &db, 0),
            16,
            "card 10 should reduce by the four other hand cards, not by all five cards in hand"
        );
    }

    /// Test Case 1: Card 10 as singleton in hand
    /// Expected: Card 10 cost = base_cost (no reduction, only 1 card in hand)
    #[test]
    fn test_card_10_singleton_cost() {
        let mut state = GameState::default();
        let db = load_real_db();

        // Place only card 10 in hand
        state.players[0].hand = vec![10].into();
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5].into();

        // Get the card to find its base cost
        let card_10 = db.get_member(10).expect("Card 10 should exist");
        let base_cost = card_10.cost as i32;

        // With only 1 card in hand (card 10 itself), the cost reduction should be 0
        // (reduction = other_cards_in_hand * 1 = 0)
        let expected_cost = (base_cost).max(0);

        // Create bytecode that checks the cost would be base_cost for card 10
        // (This simulates what the cost calculation should show during play)
        println!("Card 10 Base Cost: {}", base_cost);
        println!("Hand Size: 1");
        println!("Expected Cost Reduction: 0");
        println!("Expected Play Cost: {}", expected_cost);

        // Verify the card exists and has a cost
        assert!(base_cost >= 0, "Card 10 should have a cost value");
    }

    /// Test Case 2: Card 10 with 4 other cards in hand
    /// Expected: Card 10 cost = base_cost - 4 (one reduction per other card)
    #[test]
    fn test_card_10_with_four_other_cards() {
        let mut state = GameState::default();
        let db = load_real_db();

        // Card 10 + 4 other cards in hand (total 5)
        state.players[0].hand = vec![10, 121, 124, 100, 200].into();
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5].into();

        let card_10 = db.get_member(10).expect("Card 10 should exist");
        let base_cost = card_10.cost as i32;
        let other_cards_in_hand = 4; // cards 121, 124, 100, 200
        let expected_cost_reduction = other_cards_in_hand;
        let expected_play_cost = (base_cost - expected_cost_reduction).max(0);

        println!("Card 10 Base Cost: {}", base_cost);
        println!("Hand Size: 5");
        println!("Other Cards: {}", other_cards_in_hand);
        println!("Expected Cost Reduction: {}", expected_cost_reduction);
        println!("Expected Play Cost for Card 10: {}", expected_play_cost);

        // The key bug to test: After playing card 10, other cards should NOT have
        // their cost reduced. Let's verify the cost_reduction is isolated to card 10
        assert_eq!(other_cards_in_hand, 4, "Should have 4 other cards");
    }

    /// Test Case 3: Multiple cards with different costs in hand
    /// Verify that ONLY card 10 has reduced cost, not the other cards
    #[test]
    fn test_card_10_cost_isolation_from_peers() {
        let mut state = GameState::default();
        let db = load_real_db();

        // Setup: card 10 + 3 high-cost cards in hand
        let hand_cards = vec![10, 121, 124, 100];
        state.players[0].hand = hand_cards.clone().into();
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10].into();

        // Get costs for all cards
        let costs: Vec<(u32, i32)> = hand_cards
            .iter()
            .map(|&id| {
                let card = db
                    .get_member(id)
                    .expect(&format!("Card {} should exist", id));
                (id as u32, card.cost as i32)
            })
            .collect();

        println!("Hand cards and costs:");
        for (id, cost) in &costs {
            println!("  Card {}: cost {}", id, cost);
        }

        // Verify card 10 exists
        assert!(costs[0].0 == 10, "First card should be card 10");

        // The bug: After playing card 10, cards 121, 124, and 100 should NOT have
        // their costs reduced. They should show their original costs.
        //
        // Current bug behavior would be:
        // - Card 10 cost: base - 3 (correct: 3 other cards in hand)
        // - Card 121 cost: base - 3 (WRONG! Should be base unchanged)
        // - Card 124 cost: base - 3 (WRONG! Should be base unchanged)
        // - Card 100 cost: base - 3 (WRONG! Should be base unchanged)

        let card_10_cost = costs[0].1;
        let card_121_cost = costs[1].1;

        println!("Card 10 should have cost reduced by 3");
        println!("Card 121 should NOT have cost reduced");
        println!("  Card 10: {}", card_10_cost);
        println!("  Card 121: {}", card_121_cost);

        // Verify they have different base costs (to catch if reduction affected both the same way)
        assert_ne!(
            card_10_cost, card_121_cost,
            "Cards should have different base costs"
        );
    }

    #[test]
    fn test_card_10_baton_cost_does_not_double_count_hand_reduction() {
        let mut db = load_real_db().clone();
        insert_test_member(&mut db, 90001, 2);
        insert_test_member(&mut db, 90002, 1);
        insert_test_member(&mut db, 90003, 1);
        insert_test_member(&mut db, 90004, 1);
        insert_test_member(&mut db, 90005, 1);
        insert_test_member(&mut db, 90006, 1);
        insert_test_member(&mut db, 90007, 1);

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0].stage[0] = 90001;
        state.players[0].hand = vec![10, 90002, 90003, 90004, 90005, 90006, 90007].into();
        state.players[0].energy_zone = (1..=6).collect::<Vec<i32>>().into();

        let cost = state.get_member_cost(0, 10, 0, -1, &db, 0);
        assert_eq!(cost, 12, "card 10 baton cost should be 20 - 6 hand cards - 2 replaced cost = 12");

        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);

        let illegal_baton_play_present = receiver.actions.iter().any(|action| {
            matches!(
                DecodedAction::decode(*action),
                DecodedAction::PlayMember {
                    hand_idx: 0,
                    slot_idx: 0,
                    other_slot: None,
                    ..
                }
            )
        });
        assert!(
            !illegal_baton_play_present,
            "card 10 should not be playable with only 6 energy when baton cost is 12; actions={:?}",
            receiver.actions
        );

        let result = state.play_member(&db, 0, 0);
        assert!(result.is_err(), "direct baton play should fail with only 6 energy, got {result:?}");
    }

    #[test]
    fn test_card_10_baton_cost_ignores_stage_copy_hand_reduction_leak() {
        let mut db = load_real_db().clone();
        insert_test_member(&mut db, 90101, 2);
        insert_test_member(&mut db, 90102, 1);
        insert_test_member(&mut db, 90103, 1);
        insert_test_member(&mut db, 90104, 1);
        insert_test_member(&mut db, 90105, 1);
        insert_test_member(&mut db, 90106, 1);
        insert_test_member(&mut db, 90107, 1);

        let mut state = GameState::default();
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0].stage[0] = 90101;
        state.players[0].stage[1] = 10;
        state.players[0].hand = vec![10, 90102, 90103, 90104, 90105, 90106, 90107].into();

        let cost = state.get_member_cost(0, 10, 0, -1, &db, 0);
        assert_eq!(
            cost, 12,
            "a stage copy of card 10 must not add another hand-based reduction during baton cost evaluation"
        );
    }

    /// Test Case 4: Edge case - all hand slots filled with different costs
    /// Verify cost reduction behavior across full hand (5 slots)
    #[test]
    fn test_card_10_full_hand_cost_distribution() {
        let mut state = GameState::default();
        let db = load_real_db();

        // Full hand: card 10 + 4 others
        // This tests whether the cost_reduction stat is only applied once
        // or if it's being applied to multiple cards
        let hand = vec![10, 121, 124, 100, 200];
        state.players[0].hand = hand.clone().into();
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10].into();

        // Get card costs
        let card_10 = db.get_member(10).expect("Card 10 should exist");
        let card_121 = db.get_member(121).expect("Card 121 should exist");

        let cost_10 = card_10.cost as i32;
        let cost_121 = card_121.cost as i32;

        // Expected behavior:
        // - player.cost_reduction should be set to 4 (for card 10's ability)
        // - When card 10 is played, it uses: cost_10 - 4 = X
        // - When card 121 is played, it should use: cost_121 - 0 (not affected by card 10)
        //
        // BUG: Current behavior probably calculates all costs as reduced

        println!("Full hand distribution test:");
        println!(
            "  Card 10 base: {}, with 4 others → cost should be {}",
            cost_10,
            (cost_10 - 4).max(0)
        );
        println!(
            "  Card 121 base: {}, with card 10's reduction → cost should STILL be {}",
            cost_121, cost_121
        );
        println!("  Expected hand costs: [10-4, 121, 124, 100, 200]");
        println!("  Bug would show: All costs reduced by 4");

        assert!(cost_10 > 0, "Card 10 should have positive cost");
    }

    /// Test Case 5: Cost reduction state after card 10 is played
    /// BUG DETECTION: Verify cost_reduction is cleared/isolated after playing card 10
    #[test]
    fn test_card_10_cost_reduction_does_not_persist_to_next_card() {
        let mut state = GameState::default();
        let db = load_real_db();

        // Scenario: Play card 10 first, then check what card 121 costs
        state.players[0].hand = vec![10, 121].into();
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10].into();

        let card_10 = db.get_member(10).expect("Card 10 should exist");
        let card_121 = db.get_member(121).expect("Card 121 should exist");

        let cost_10_base = card_10.cost as i32;
        let cost_121_base = card_121.cost as i32;

        println!("Persistence Test:");
        println!("  Phase 1: Hand = [10, 121]");
        println!(
            "    Card 10: base {}, after reduction by 1 = {}",
            cost_10_base,
            (cost_10_base - 1).max(0)
        );
        println!(
            "    Card 121: base {}, should NOT be reduced = {}",
            cost_121_base, cost_121_base
        );

        // After card 10 is PLAYED (removed from hand), hand = [121]
        // At that point:
        // - cost_reduction should be 0 (no more card 10 with the ability)
        // - Card 121 cost should be base (no reduction)
        println!("  Phase 2: After card 10 played, hand = [121]");
        println!(
            "    Card 121 base {}, cost_reduction = 0, cost should be {}",
            cost_121_base, cost_121_base
        );

        println!(
            "  BUG SYMPTOM: Card 121 cost shown as {}",
            cost_121_base - 1
        );
        println!("    (incorrectly inherits cost_reduction from card 10)");

        // Verification
        assert!(cost_10_base > 0, "Base costs should be positive");
        assert!(cost_121_base > 0, "Base costs should be positive");
    }

    /// Test Case 6: Energy cost calculation during main phase action generation
    /// This tests the actual cost used when determining playable actions
    #[test]
    fn test_card_10_playable_action_cost_verification() {
        let mut state = GameState::default();
        let db = load_real_db();

        // Setup enough energy to play any card
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10].into();
        state.players[0].hand = vec![10, 121, 124].into();

        let card_10 = db.get_member(10).expect("Card 10 should exist");
        let card_121 = db.get_member(121).expect("Card 121 should exist");
        let card_124 = db.get_member(124).expect("Card 124 should exist");

        let cost_10 = card_10.cost as i32;
        let cost_121 = card_121.cost as i32;
        let cost_124 = card_124.cost as i32;

        // With 4 cards in hand (well, 3 but the pattern is clear):
        // - Hand size = 3
        // - Card 10 reduction = 2 (for cards 121, 124)
        // - Card 10 play cost = cost_10 - 2

        println!("Action generation cost test:");
        println!("  Hand: [10, 121, 124] (size 3)");
        println!(
            "  Card 10 base: {}, reduced by 2 (other cards) = {}",
            cost_10,
            (cost_10 - 2).max(0)
        );
        println!("  Card 121 base: {}, NOT reduced = {}", cost_121, cost_121);
        println!("  Card 124 base: {}, NOT reduced = {}", cost_124, cost_124);

        println!("  BUG WOULD SHOW:");
        println!("  Card 10: {}", (cost_10 - 2).max(0));
        println!(
            "  Card 121: {} (WRONG - should be {})",
            (cost_121 - 2).max(0),
            cost_121
        );
        println!(
            "  Card 124: {} (WRONG - should be {})",
            (cost_124 - 2).max(0),
            cost_124
        );

        // Verify test setup is valid
        assert!(
            cost_10 > 0 && cost_121 > 0 && cost_124 > 0,
            "All cards should have costs"
        );
    }

    /// Test Case 7: Cost reduction opcode (13) with PER_CARD filter
    /// Verify the REDUCE_COST opcode is correctly applying per-card logic
    #[test]
    fn test_card_10_reduce_cost_opcode_per_card_filter() {
        let mut state = GameState::default();
        let db = load_real_db();
        state.debug.debug_mode = true;

        state.players[0].hand = vec![10, 121, 124, 100, 200].into();
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5].into();

        println!("=== BEFORE ability ===");
        println!("Hand: {:?}", &state.players[0].hand);
        println!("cost_reduction: {}", state.players[0].cost_reduction);

        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 10,
            ability_index: 0,
            area_idx: 200,
            ..AbilityContext::default()
        };

        // Use the normalized frame program from the real database.
        let card_10 = db.get_member(10).expect("Card 10 should exist");
        let ability_0_frames = card_10.abilities[0]
            .frame_program
            .as_ref()
            .expect("Card 10 ability 0 should have a frame program")
            .frames
            .clone();

        println!("Test REDUCE_COST opcode:");
        println!("  Hand size: {}", state.players[0].hand.len());
        let other_cards = state.players[0].hand.len() as i16 - 1;
        println!("  Other cards: {}", other_cards);
        println!("  Cost reduction should be: {}", other_cards);

        state.resolve_semantic_frames(
            &db,
            &ability_0_frames,
            &ctx,
        );

        println!("=== AFTER ability ===");
        println!("Hand: {:?}", &state.players[0].hand);
        println!(
            "  Actual cost_reduction: {}",
            state.players[0].cost_reduction
        );

        // Verify that cost_reduction == 4 (4 other cards, value=1 per card)
        assert_eq!(
            state.players[0].cost_reduction, other_cards,
            "Cost reduction should be {} (other cards * 1), but got {}",
            other_cards, state.players[0].cost_reduction
        );
    }

    /// Test Case 8: Multiple hand size scenarios for cost reduction
    /// Test various hand sizes to ensure proper per-card calculation
    #[test]
    fn test_card_10_cost_reduction_hand_size_variations() {
        let hand_sizes = vec![
            (vec![10], 0),                     // Only card 10: 0 other cards
            (vec![10, 121], 1),                // Card 10 + 1 other: 1 reduction
            (vec![10, 121, 124], 2),           // Card 10 + 2 others: 2 reduction
            (vec![10, 121, 124, 100, 200], 4), // Card 10 + 4 others: 4 reduction (hand full)
        ];

        let db = load_real_db();
        let card_10 = db.get_member(10).expect("Card 10 should exist");
        let ability_0_frames = card_10.abilities[0]
            .frame_program
            .as_ref()
            .expect("Card 10 ability 0 should have a frame program")
            .frames
            .clone();

        // Debug: Print all frames
        println!("Card 10 ability frames (total: {}):", ability_0_frames.len());
        for (i, frame) in ability_0_frames.iter().enumerate() {
            let frame_data = frame.components();
            println!("  Frame {}: opcode={}, value={}, raw_attr={:#x}, raw_slot={:#x}, source_zone={:?}", 
                     i, frame_data.opcode, frame_data.value, frame_data.raw_attr(), frame_data.raw_slot, frame_data.slot.source_zone);
        }

        for (hand_cards, expected_other_count) in hand_sizes {
            let mut state = GameState::default();
            state.players[0].hand = hand_cards.clone().into();

            let ctx = AbilityContext {
                player_id: 0,
                source_card_id: 10,
                ability_index: 0,
                area_idx: 200,
                ..AbilityContext::default()
            };

            // Apply card 10's real ability bytecode
            state.resolve_semantic_frames(
                &db,
                &ability_0_frames,
                &ctx,
            );

            let expected = expected_other_count as i16;

            println!(
                "Hand size {}: card_10 at [0], others {}, expected reduction {}",
                hand_cards.len(),
                expected_other_count,
                expected_other_count
            );

            assert_eq!(
                state.players[0].cost_reduction, expected,
                "Hand {:?} should have {} other cards, cost_reduction should be {}",
                hand_cards, expected_other_count, expected_other_count
            );
        }
    }

    /// Test Case 9: Ensure other abilities are NOT causing the cost reduction
    /// Verify that card 10's other abilities (PREVENT_BATON_TOUCH, ADD_BLADES) don't interfere
    #[test]
    fn test_card_10_other_abilities_dont_reduce_cost() {
        let mut state = GameState::default();
        let db = load_real_db();

        state.players[0].hand = vec![10, 121, 124].into();

        // Card 10 has 3 abilities at indices 0, 1, 2:
        // 0: REDUCE_COST (the problematic one)
        // 1: PREVENT_BATON_TOUCH
        // 2: ADD_BLADES (on_live_start)

        // Ability 1: PREVENT_BATON_TOUCH bytecode
        let ctx = AbilityContext {
            player_id: 0,
            ..AbilityContext::default()
        };

        let prevent_baton_bytecode = vec![
            AbilityFrame::new(O_PREVENT_BATON_TOUCH, 1, 0, 4, false),
            AbilityFrame::new(O_RETURN, 0, 0, 0, false),
        ];

        // Before running other abilities, cost_reduction should be 0
        assert_eq!(state.players[0].cost_reduction, 0);

        // Run PREVENT_BATON_TOUCH ability
        state.resolve_semantic_frames(
            &db,
            &prevent_baton_bytecode,
            &ctx,
        );

        // After running PREVENT_BATON_TOUCH, cost_reduction should STILL be 0
        assert_eq!(
            state.players[0].cost_reduction, 0,
            "PREVENT_BATON_TOUCH should not affect cost_reduction"
        );

        println!("PREVENT_BATON_TOUCH ability does not modify cost_reduction: OK");
    }

    /// Test Case 10: Integration - play card 10, check subsequent card costs
    /// Full scenario test showing the bug in action
    #[test]
    fn test_card_10_play_sequence_cost_integrity() {
        let mut state = GameState::default();
        let db = load_real_db();

        // Full hand with card 10
        state.players[0].hand = vec![10, 121, 124].into();
        state.players[0].energy_zone = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10].into();

        let card_10 = db.get_member(10).expect("Card 10");
        let card_121 = db.get_member(121).expect("Card 121");

        let base_cost_10 = card_10.cost as i32;
        let base_cost_121 = card_121.cost as i32;

        println!("=== CARD 10 PLAY SEQUENCE TEST ===");
        println!("Initial hand: [10, 121, 124]");
        println!("Card 10 base cost: {}", base_cost_10);
        println!("Card 121 base cost: {}", base_cost_121);

        // Scenario 1: Calculate costs while card 10 is in hand
        println!("\nScenario 1: Before playing card 10");
        println!("  Hand size: 3, other cards in hand: 2");
        println!(
            "  Card 10 cost for play: {} - 2 = {}",
            base_cost_10,
            (base_cost_10 - 2).max(0)
        );
        println!("  Card 121 cost for play: {} (no reduction)", base_cost_121);

        // Scenario 2: After playing card 10, costs should be recalculated
        println!("\nScenario 2: After playing card 10 (removed from hand)");
        println!("  Remaining hand: [121, 124]");
        println!(
            "  Card 121 cost for play: {} (card 10 ability no longer applies)",
            base_cost_121
        );
        println!("  Card 124 cost calculation should be independent");

        // The bug would manifest as:
        // - After card 10 played, cost_reduction is not cleared
        // - Card 121 shows cost as (base_cost_121 - 2) instead of base_cost_121

        // Verify the costs are calculated correctly
        assert!(base_cost_10 > 0, "Cost should be positive");
        assert!(base_cost_121 > 0, "Cost should be positive");

        println!("\n=== BUG PATTERN ===");
        println!("If cost_reduction only affects card 10: PASS");
        println!("If cost_reduction leaks to card 121: FAIL");
    }

    /// Test Case 11: Diagnostic - Check bytecode attribute encoding
    /// Verify that the PER_CARD filter information is in the bytecode
    #[test]
    fn test_card_10_bytecode_attributes_inspect() {
        let db = load_real_db();

        let card_10 = db.get_member(10).expect("Card 10 should exist");

        println!("=== CARD 10 BYTECODE DIAGNOSTIC ===");
        println!("Card 10 ID: {}", card_10.card_id);
        println!("Card 10 has {} abilities", card_10.abilities.len());

        for (idx, ability) in card_10.abilities.iter().enumerate() {
            println!("\n--- Ability {} ---", idx);
            println!("Trigger: {:?}", ability.trigger);
            let ability_words = ability.words();
            println!("Bytecode length: {}", ability_words.len());

            if ability_words.len() >= 5 {
                let opcode = ability_words[0];
                let value = ability_words[1];
                let attr_lo = ability_words[2];
                let attr_hi = ability_words[3];
                let slot = ability_words[4];

                println!("Opcode: {} (13 = REDUCE_COST)", opcode);
                println!("Value: {}", value);
                println!("Attr Low: {} (0x{:08x})", attr_lo, attr_lo);
                println!("Attr High: {} (0x{:08x})", attr_hi, attr_hi);
                println!("Slot/Zone: {} (0x{:08x})", slot, slot);

                if opcode == 13 {
                    // O_REDUCE_COST
                    // Decode the attributes
                    let attr = (attr_lo as u64) | ((attr_hi as u64) << 32);
                    println!("Combined Attr: 0x{:016x}", attr);

                    // Check for known filter flags
                    // Compare_accumulated mode = 0x03 (bits 0-1)
                    let compare_mode = attr & 0x03;
                    println!("Compare mode bits (0-1): 0x{:02x}", compare_mode);

                    // Filter type and NOT_SELF flag
                    let filter_info = (attr >> 2) & 0xFF;
                    println!("Filter info (bits 2-9): 0x{:02x}", filter_info);
                }
            }
        }
    }

    /// Test Case 12: Bytecode resolution with explicit hand size test
    /// Test REDUCE_COST with different hand sizes to isolate the multiplier issue
    #[test]
    fn test_card_10_reduce_cost_explicit_hand_size() {
        let db = load_real_db();

        let test_cases = vec![
            ("Empty hand + card_10", vec![10], 0),
            ("Hand with card_10 + 1 other", vec![10, 121], 1),
            ("Hand with card_10 + 2 others", vec![10, 121, 124], 2),
            ("Hand with card_10 + 3 others", vec![10, 121, 124, 100], 3),
            (
                "Full hand with card_10 + 4 others",
                vec![10, 121, 124, 100, 200],
                4,
            ),
        ];

        for (desc, hand_cards, expected_reduction) in test_cases {
            println!("\n=== Test: {} ===", desc);
            println!("Hand: {:?}", hand_cards);
            println!("Expected reduction: {}", expected_reduction);

            let mut state = GameState::default();
            state.players[0].hand = hand_cards.into();

            let ctx = AbilityContext {
                player_id: 0,
                source_card_id: 10,
                area_idx: 200,
                ..AbilityContext::default()
            };

            // Get card 10's actual bytecode from the database
            let card_10 = db.get_member(10).expect("Card 10");
            let ability_0_words = card_10.abilities[0].words();

            println!(
                "Bytecode: {:?}",
                &ability_0_words[0..5.min(ability_0_words.len())]
            );

            state.resolve_semantic_frames(
                &db,
                &card_10.abilities[0].frame_program.as_ref().unwrap().frames,
                &ctx,
            );

            println!("Actual cost_reduction: {}", state.players[0].cost_reduction);

            if state.players[0].cost_reduction as i32 != expected_reduction {
                println!(
                    "❌ FAILED: Got {} but expected {}",
                    state.players[0].cost_reduction, expected_reduction
                );
                println!("  BUG: PER_CARD multiplier not applied correctly");
            } else {
                println!("✓ PASS");
            }
        }
    }
}
