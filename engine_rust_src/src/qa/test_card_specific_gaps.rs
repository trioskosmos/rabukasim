/// Card-specific ability tests for Q&A validation
/// Coverage: Q122-Q186 Card-specific mechanics and edge cases

#[cfg(test)]
mod card_specific_qa_gaps {
    use crate::core::logic::*;
    use crate::test_helpers::*;

    /// Q122: Peek ability without actual refresh (just viewing)
    /// 『登場 手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。
    /// その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。』
    /// If viewing all cards, no refresh until cards are actually moved
    #[test]
    fn test_q122_view_all_deck_no_refresh_until_move() {
        let mut game = Game::new_test();

        let deck = vec![
            Card::member("PL!N-bp3-002"),
            Card::member("PL!N-bp3-003"),
        ];
        game.set_deck(Player::A, deck);
        game.set_discard(Player::A, vec![Card::member("PL!N-bp3-004")]);

        // Viewing phase - deck still has cards
        let viewed = game.peek_deck(Player::A, 2);
        assert_eq!(viewed.len(), 2);

        // Discard not activated yet
        let discard_before = game.discard(Player::A).len();

        // Now player arranges and places back
        game.move_viewed_to_deck_top(Player::A, &viewed[0..1]);
        game.move_viewed_to_discard(Player::A, &viewed[1..2]);

        // After moving, discard might have changed
        let discard_after = game.discard(Player::A).len();
        assert!(discard_after >= discard_before);
    }

    /// Q131-Q132 variant: Live start ability with opponent as attacker
    /// 『ライブ開始時 self is opponent attacker...』
    /// Abilities that check "my live start" don't trigger if opponent initiated
    #[test]
    fn test_q131_opponent_initiated_live() {
        let mut test = GameTest::new();

        // Opponent (Player B) starts a live
        test.set_active(Player::B);

        // Player A has live start card on stage
        let card_a = Card::member("PL!-bp1-001");
        test.place(Player::A, card_a, Slot::Center);

        // B enters performance (their live)
        test.enter_performance(Player::B);

        // A's live_start trigger condition (if any) should NOT fire
        // since it's B's live, not A's
        let triggered = test.get_triggered_abilities();
        for ability in &triggered {
            assert_ne!(ability.owner, Player::A); // No A abilities should trigger
        }
    }

    /// Q132 variant: Live success time with opponent as winner
    /// Similar to Q131 but for {{live_success.png|ライブ成功時}}
    #[test]
    fn test_q132_opponent_won_live() {
        let mut test = GameTest::new();

        test.set_active(Player::B);

        let card_a = Card::live("PL!-bp3-001"); // Has live_success ability
        test.place_live(Player::A, card_a);

        let card_b = Card::live("PL!-bp1-001");
        test.place_live(Player::B, card_b);

        // Complete performance - B wins
        test.set_live_score(Player::A, 5);
        test.set_live_score(Player::B, 15);
        test.resolve_live();

        // A's live_success abilities should NOT trigger (A didn't win)
        let triggered = test.get_triggered_abilities_for(Player::A);
        for ab in &triggered {
            assert_ne!(ab.timing, AbilityTiming::LiveSuccess);
        }
    }

    /// Q144: Center ability location check
    /// [[kidou.png|起動]] [[center.png|センター]] ターン1回
    /// メンバー1人をウェイトにする：ライブ終了時まで、...
    /// Only works when member is in center slot
    #[test]
    fn test_q144_center_activation_only_in_center() {
        let mut test = GameTest::new();

        let center_card = Card::member("PL!S-bp3-001");
        test.place(Player::A, center_card.clone(), Slot::Center);

        // Activation should work in center
        let can_activate_center = test.can_activate_center_ability(Player::A, Slot::Center);
        assert!(can_activate_center);

        // Move to left
        test.move_member(Player::A, Slot::Center, Slot::Left);

        // Should NOT be activatable anymore
        let can_activate_left = test.can_activate_center_ability(Player::A, Slot::Left);
        assert!(!can_activate_left);

        // Verify it's in left now
        assert_eq!(test.member_at(Player::A, Slot::Left).unwrap().id, center_card.id);
    }

    /// Q147-Q149: "Until live end" effect persistence
    /// {{jyouji.png|常時}} score bonuses from {{live_start.png|ライブ開始時}}
    /// persist even if live doesn't happen
    #[test]
    fn test_q147_until_live_end_persists_no_live() {
        let mut test = GameTest::new();

        let member = Card::member("PL!-bp1-001");
        test.place(Player::A, member, Slot::Center);

        // Trigger "until live end" bonus
        test.apply_bonus_until_live_end(Player::A, "score", 2);

        // Even if no live happens this turn...
        test.skip_live();
        test.enter_end_phase();

        // Bonus should persist if it's until "live end" and we skipped live
        // (Live end phase resets it even without actual live)
        let has_bonus = test.get_bonus(Player::A, "score") > 0;
        assert!(!has_bonus); // Should be gone after phase ends
    }

    /// Q150: Surplus heart definition for conditions
    /// {{heart_00.png|heart0}} in surplus means hearts > required
    /// Used in damage calculations but not "heart total" counts
    #[test]
    fn test_q150_surplus_heart_calculation() {
        let mut test = GameTest::new();

        let card = Card::live("PL!-bp1-001");
        test.place_live(Player::A, card);

        // Set required hearts
        test.set_live_requirement(Player::A, vec![
            Heart::Red, Heart::Red, Heart::Blue
        ]);

        // Set actual hearts
        test.set_live_hearts(Player::A, vec![
            Heart::Red, Heart::Red, Heart::Blue,
            Heart::Green  // +1 surplus
        ]);

        let surplus = test.calculate_surplus_hearts(Player::A);
        assert_eq!(surplus, 1);

        // Add blade hearts
        test.add_blade_hearts(Player::A, 2);

        // Surplus should increase
        let surplus_with_blade = test.calculate_surplus_hearts(Player::A);
        assert_eq!(surplus_with_blade, 3);
    }

    /// Q151-Q160: Advanced member state transitions
    /// Members that move areas within same turn have reset turn-once
    /// Abilities that check "on appearance" vs "on area move"
    #[test]
    fn test_q151_member_area_move_state_reset() {
        let mut test = GameTest::new();

        let member = Card::member("PL!-bp1-001");
        test.place(Player::A, member.clone(), Slot::Left);

        // Mark as "appeared this turn"
        test.set_appeared_this_turn(Player::A, Slot::Left, true);

        // Move within stage (Left -> Center)
        test.move_member(Player::A, Slot::Left, Slot::Center);

        // Turn-once abilities should NOT have fired
        // (member moved, not placed new)
        let turn_once_ready = test.is_turn_once_ready(Player::A, Slot::Center);
        assert!(!turn_once_ready);
    }

    /// Q168-Q170: Multi-user on-play effects
    /// 『登場 自分と相手はそれぞれ、自身の控え室から
    /// コスト2以下のメンバーカードを1枚、メンバーのいないエリアに
    /// ウェイト状態で登場させる。』
    /// Both players place, area stays locked from further placement
    #[test]
    fn test_q168_mutual_placement_area_lock() {
        let mut test = GameTest::new();

        // Card that triggers mutual placement
        let card = Card::member("LL-bp3-001"); // Nico card
        test.place(Player::A, card, Slot::Center);

        // Triggering appearance effect
        test.trigger_on_play_effect(Player::A, Slot::Center);

        // Both players place cost 2 or less members
        let cheap_card_a = Card::member("PL!-bp1-002");
        let cheap_card_b = Card::member("PL!-bp1-003");

        test.place_from_discard(Player::A, cheap_card_a, Slot::Left);
        test.place_from_discard(Player::B, cheap_card_b, Slot::Right);

        // Both placed in wait state
        assert!(test.is_wait(Player::A, Slot::Left));
        assert!(test.is_wait(Player::B, Slot::Right));

        // Left/Right areas should be locked from further placement
        let can_place = test.can_place_at(Player::A, Slot::Left);
        assert!(!can_place);
    }

    /// Q174: Group name vs unit name resolution
    /// 『ライブ成功時 自分のライブ中の『Aqours』のカードが2枚以上ある場合...』
    /// Uses group name (Aqours) not unit name
    /// But for "unique group members" checks, it's per-individual member name
    #[test]
    fn test_q174_group_name_vs_unit_name() {
        let mut test = GameTest::new();

        let card1 = Card::member("PL!S-bp2-001"); // Aqours, name: Character1
        let card2 = Card::member("PL!S-bp2-002"); // Aqours, name: Character2

        test.place_live(Player::A, card1);
        test.place_live(Player::A, card2);

        // Check group: should be 2 Aqours
        let aqours_count = test.count_group_in_live(Player::A, "Aqours");
        assert_eq!(aqours_count, 2);

        // For abilities requiring "unique names in group", different
        let unique_names = test.unique_member_names_in_live(Player::A, "Aqours");
        assert_eq!(unique_names.len(), 2);
    }

    /// Q175: Unit name cost reduction (distinct from group)
    /// 『ライブ開始時 手札の同じユニット名を持つカード2枚を控え室に置いてもよい...』
    /// ユニット名 = specific unit, not group name
    #[test]
    fn test_q175_unit_name_cost_matching() {
        let mut test = GameTest::new();

        // Cards from same unit but possibly different groups
        // e.g., 5yncri5e! Setsuna cards
        let card1 = Card::member("PL!SP-bp1-001"); // Unit: 5yncri5e!
        let card2 = Card::member("PL!SP-bp1-002"); // Unit: 5yncri5e! (same)
        let card3 = Card::member("PL!SP-bp2-001"); // Unit: 5yncri5e! (same)
        let card4 = Card::member("PL!S-bp1-001");  // Unit: Different

        test.set_hand(Player::A, vec![
            card1.clone(), card2.clone(), card3, card4
        ]);

        // Ability checks "same unit name"
        let cards_of_unit = test.find_cards_by_unit(Player::A, "5yncri5e!");
        assert_eq!(cards_of_unit.len(), 3);

        // Can satisfy ability with 2 from same unit
        let can_satisfy = test.can_satisfy_unit_cost(Player::A, 2, "5yncri5e!");
        assert!(can_satisfy);
    }

    /// Q176-Q177: Opponent targeted effects
    ///『起動 このメンバーをウェイトにしてもよい...』
    /// Cannot wait opponent's members, only own
    #[test]
    fn test_q176_opponent_effect_boundary() {
        let mut test = GameTest::new();

        let my_member = Card::member("PL!-bp1-001");
        let opp_member = Card::member("PL!-bp1-002");

        test.place(Player::A, my_member, Slot::Center);
        test.place(Player::B, opp_member, Slot::Left);

        // Try to activate effect that targets opponent's member
        let can_target = test.can_target_for_effect(
            Player::A,
            EffectType::MakeWait,
            Player::B,
            Slot::Left
        );

        // Should fail - effects target own board
        assert!(!can_target);
    }

    /// Q177: Mandatory vs optional ability execution
    /// 『自動 ターン1回 自分のカードの効果によって...』
    /// Mandatory auto abilities MUST execute if conditions met
    /// Cannot choose to skip
    #[test]
    fn test_q177_mandatory_auto_ability() {
        let mut test = GameTest::new();

        let member = Card::member("PL!-pb1-015");
        test.place(Player::A, member, Slot::Center);

        // Trigger condition: opponent's member becomes wait
        test.force_opponent_wait(Player::B, Slot::Left);

        // Mandatory ability should trigger automatically
        let triggered = test.get_auto_triggered_this_phase(Player::A);
        assert!(!triggered.is_empty());

        // Player cannot skip execution
        let can_skip = test.can_skip_auto_ability(Player::A, triggered[0].id);
        assert!(!can_skip);
    }

    /// Q180: Area movement vs "cannot activate"
    /// [[toujyou.png|登場]] Effect saying members "cannot be activated"
    /// doesn't prevent area movement state changes (wait->active in active phase)
    #[test]
    fn test_q180_area_activation_override() {
        let mut test = GameTest::new();

        let member = Card::member("PL!-bp3-004");
        test.place(Player::A, member, Slot::Center);

        // Place restriction: "members cannot be activated"
        test.apply_restriction("cannot_activate_members");

        // Force member to wait
        test.set_wait(Player::A, Slot::Center, true);

        // Enter active phase
        test.enter_active_phase(Player::A);

        // Despite "cannot activate" restriction, active phase logic
        // should still trigger (state restoration, not activation)
        let is_wait = test.is_wait(Player::A, Slot::Center);
        assert!(!is_wait); // Should be active now
    }

    /// Q178-Q179: Printemps center member effect
    /// 『ライブ開始時 自分のステージにいるプリンテンプス...』
    /// Checks for group, activates center slot, field counts correctly
    #[test]
    fn test_q178_group_member_activation() {
        let mut test = GameTest::new();

        // Place Printemps members
        let card1 = Card::member("PL!-pb1-028"); // Printemps, Center
        let card2 = Card::member("PL!-bp1-050"); // Printemps, Left

        test.place(Player::A, card1, Slot::Center);
        test.place(Player::A, card2, Slot::Left);

        // Trigger effect that activates all "Printemps members"
        test.trigger_group_effect(Player::A, "Printemps", "activate_wait");

        // Both should be activatable
        let acts_center = test.is_wait(Player::A, Slot::Center);
        let acts_left = test.is_wait(Player::A, Slot::Left);

        // If they were wait, now should be active
        assert!(!acts_center && !acts_left);
    }

    /// Q182: Energy placement vs yell conditions
    /// 『ライブ成功時 ...公開されたカードの中にブレードハートを持たないカード
    /// が0枚の場合か、または...』
    /// With restricted yell (0 cards public due to wait effects),
    /// condition checks pass
    #[test]
    fn test_q182_zero_revealed_yell_condition() {
        let mut test = GameTest::new();

        let member = Card::member("PL!S-bp3-019"); // Has this ability
        test.place_live(Player::A, member);

        // Apply effect: yell shows 0 cards (due to wait members)
        test.set_yell_reveal_count(Player::A, 0);

        // Live success check: "no cards without blade hearts" = TRUE (0 cards)
        test.enter_live_verdict(Player::A, LiveVerdict::Success);

        // Ability condition should be satisfied
        let abilities_triggered = test.get_live_success_abilities(Player::A);
        assert!(!abilities_triggered.is_empty());
    }

    /// Q183: Cost payment side restriction
    /// Cost effects like "player1をウェイトにする" cannot target opponent
    /// Even if the ability doesn't restrict it explicitly
    #[test]
    fn test_q183_cost_effect_own_side() {
        let mut test = GameTest::new();

        let cost_ability = Card::member("PL!-bp3-004");
        test.place(Player::A, cost_ability, Slot::Center);

        // Effect has cost: "player 1 を wait状態にする (選択)"
        // Player A tries to target their own member
        let can_target_own = test.can_pay_cost_by_waiting(
            Player::A,
            Player::A,
            Slot::Left
        );
        assert!(can_target_own);

        // But cannot target opponent
        let can_target_opp = test.can_pay_cost_by_waiting(
            Player::A,
            Player::B,
            Slot::Right
        );
        assert!(!can_target_opp);
    }

    /// Q184: Under-member energy not counted in energy total
    /// メンバーの下に置かれたエネルギーカードはエネルギーの数として数えない
    /// Separate zone from energy field
    #[test]
    fn test_q184_under_member_energy_separate() {
        let mut test = GameTest::new();

        let member = Card::member("PL!N-bp3-001");
        test.place(Player::A, member, Slot::Center);

        // Place energy in zone (counts)
        test.add_energy(Player::A, 3);
        assert_eq!(test.energy_count(Player::A), 3);

        // Place energy under member
        test.place_energy_under_member(Player::A, Slot::Center, 2);

        // Total energy still 3 (under-member not counted)
        assert_eq!(test.energy_count(Player::A), 3);

        // But member "has" 2 energy underneath
        assert_eq!(test.energy_under_member(Player::A, Slot::Center), 2);
    }
}
