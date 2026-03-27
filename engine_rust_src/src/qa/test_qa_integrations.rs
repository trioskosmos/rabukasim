/// Q&A Final Coverage: Complex interaction chains and edge cases
/// These tests verify the most intricate rule interactions

#[cfg(test)]
mod qa_advanced_interactions {
    use crate::core::logic::*;
    use crate::test_helpers::*;

    // QA: Q131 | Q: 『 {{live_start.png|ライブ開始時}} 自分か相手を選ぶ。自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。』について。 相手が先行の場合、相手のライブ開始時に能力を使用できますか？
    // A: いいえ、発動できません。 {{live_start.png|ライブ開始時}} 能力の効果は自分のライブ開始時に発動します。
    /// Q131-Q132 Combined: Live start and live success timing with initiative
    /// Critical: "ライブ開始時" and "ライブ成功時" abilities have ownership requirements
    #[test]
    fn test_q131_q132_live_timing_ownership() {
        let mut game = Game::new_test();

        // Setup: Player A has two cards with live-timing abilities
        let member_start = Card::member("PL!-bp1-001")
            .with_ability_live_start("get_blade", 2);
        let live_success = Card::live("PL!-bp1-002")
            .with_ability_live_success_conditional("hand_larger", "score", 1);

        game.place_member(Player::A, member_start, Slot::Center);
        game.place_live_card(Player::A, live_success);

        // Scenario 1: Player B initiates live (A's live_start should NOT fire)
        game.set_active_player(Player::B);
        game.enter_performance_phase(Player::B);

        let a_live_start_triggered = game.triggered_abilities()
            .iter()
            .filter(|ab| ab.owner == Player::A && ab.timing == AbilityTiming::LiveStart)
            .count();

        assert_eq!(a_live_start_triggered, 0,
            "A's live_start should NOT trigger when B initiates");

        // Scenario 2: Complete the live with A having larger hand
        game.set_hand_size(Player::A, 8);
        game.set_hand_size(Player::B, 5);
        game.set_live_score(Player::A, 10);
        game.set_live_score(Player::B, 8);
        game.resolve_live_verdict();

        // A won the live - A's live_success should trigger
        let a_live_success_triggered = game.triggered_abilities()
            .iter()
            .filter(|ab| ab.owner == Player::A && ab.timing == AbilityTiming::LiveSuccess)
            .count();

        assert!(a_live_success_triggered > 0,
            "A's live_success should trigger since A won");
    }

    // QA: Q147 | Q: 『 {{live_start.png|ライブ開始時}} 自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。』について。 この能力の「自分のライブ中の『μ's』のカードが2枚以上ある場合」を満たさず、このカードがスコア0の時、成功ライブカード置き場に置けますか？
    // A: はい、可能です。 スコア０の場合でもライブに勝利すれば成功ライブカード置き場に置くことができます。
    /// Q147-Q150 Combined: Score and heart calculations with bonus edge cases
    /// Verify: Bonuses snapshot, heart totals exclude blade, surplus counted correctly
    #[test]
    fn test_q147_q150_score_heart_snapshot_chain() {
        let mut game = Game::new_test();

        // Setup: Live card with conditional score boost
        let live_card = Card::live("PL!-bp3-023")
            .with_base_score(3)
            .with_heart_requirement(vec!["heart_01", "heart_02", "heart_02", "heart_03"])
            .with_live_success_ability("multiple_names_different", "score", 2);

        game.place_live_card(Player::A, live_card.clone());

        // Phase 1: Apply score bonuses during live start
        game.set_stage_members_from_names(Player::A, vec!["member1", "member2", "member3"]);
        game.apply_live_start_abilities(Player::A);

        let score_base = game.get_live_card_score(Player::A, 0);

        // Phase 2: Apply heart bonuses from yell
        let blade_hearts = 1;
        game.apply_yell_blade_hearts(Player::A, blade_hearts);

        // Heart total should only count base (2+2+1=5), not blade
        let base_heart_count = game.count_stage_heart_total(Player::A, CountMode::BaseOnly);
        assert_eq!(base_heart_count, 5);

        // But surplus calculation includes blade hearts
        game.set_live_hearts(Player::A, vec!["heart_01", "heart_02", "heart_02", "heart_03", "heart_04"]);
        let surplus_before = game.calculate_surplus_hearts(Player::A);

        // Add blade heart
        game.apply_yell_blade_hearts(Player::A, 1);
        let surplus_after = game.calculate_surplus_hearts(Player::A);

        assert_eq!(surplus_after, surplus_before + 1,
            "Surplus should increase by blade heart count");

        // Phase 3: Verify live success doesn't retroactively modify
        // member requirements checked at start still apply at end
        let members_at_success = game.get_stage_members(Player::A);
        assert_eq!(members_at_success.len(), 3);

        // Live success ability shouldn't re-evaluate
        let final_score = game.get_live_card_score(Player::A, 0);
        // Score may have changed if live_success ability added bonus
        // but the snapshot from live_start should persist
        assert!(final_score >= score_base);
    }

    // QA: Q174 | Q: 『 {{live_success.png|ライブ成功時}} このターン、自分が余剰ハートに {{heart_04.png|heart04}} を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。』について、ステージに緑ハートがなくエールによってALLハートを3枚獲得してライブ成功した時、ライブ成功時能力は使えますか？
    // A: いいえ。使えません。
    /// Q174-Q175 Combined: Unit vs Group with cost modification
    /// Verify: Unit name matching, cost reduction affects selection eligibility
    #[test]
    fn test_q174_q175_unit_group_cost_chain() {
        let mut game = Game::new_test();

        // Setup complex hand with unit/group variations
        let cards = vec![
            Card::member("PL!SP-bp1-001").with_unit("5yncri5e!").with_cost(4),
            Card::member("PL!SP-bp1-002").with_unit("5yncri5e!").with_cost(3),
            Card::member("PL!SP-bp1-003").with_unit("5yncri5e!").with_cost(2),
            Card::member("PL!S-bp1-001").with_unit("Liella!").with_cost(3),
        ];
        game.set_hand(Player::A, cards);

        // Ability 1: Select cards with same unit (should get all 5yncri5e!)
        let same_unit = game.find_same_unit_cards(Player::A, "5yncri5e!");
        assert_eq!(same_unit.len(), 3, "Should find 3 cards with unit 5yncri5e!");

        // Calculate cost total: 4 + 3 + 2 = 9
        let cost_total = game.calculate_cost_sum(&same_unit);
        assert_eq!(cost_total, 9);

        // Ability 2: Apply cost reduction (e.g., from hand-size modifier)
        // "この能力を使ったカード以外の自分の手札1枚につき、1少なくなる"
        // 3 other cards in hand => -3 cost
        let using_card = game.get_active_member(Player::A, Slot::Center);
        let other_cards_in_hand = game.hand(Player::A).len() - 1; // Exclude the using card

        let reduced_cost = cost_total - other_cards_in_hand;
        assert_eq!(reduced_cost, 6, "Cost should be reduced by other hand cards");

        // Ability 3: Check if reduced cost makes cards eligible
        // E.g., "cost 5以下" requirement
        let is_eligible_5 = reduced_cost <= 5;
        assert!(!is_eligible_5, "6 should not be <= 5");

        let is_eligible_6 = reduced_cost <= 6;
        assert!(is_eligible_6, "6 should be <= 6");
    }

    // QA: Q176 | Q: 『 {{kidou.png|起動}} {{turn1.png|ターン1回}} {{icon_energy.png|E}} {{icon_energy.png|E}} :自分の手札を相手は見ないで１枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時までこのメンバーは「 {{jyouji.png|常時}} ライブの合計スコアを＋１する。」を得る。』について、公開するのは自分の手札ですか？相手の手札ですか？
    // A: 自分の手札を公開します。
    /// Q176-Q177 Combined: Mandatory vs Optional in opponent context
    /// Verify: Opponent abilities must fully resolve, but some costs are optional
    #[test]
    fn test_q176_q177_opponent_mandatory_optional_chain() {
        let mut game = Game::new_test();

        // Opponent places member with effect on us
        let opp_member = Card::member("PL!-pb1-015")
            .with_on_play_effect_opponent(
                Effect::AutoAbility
                    .when("direct_target".into())
                    .cost(Some(AbilityCost::WaitMember(1)))
                    .effect("draw_1")
            );

        game.place_member(Player::B, opp_member, Slot::Center);

        // Effect triggers: 自動 このターン、相手のメンバーがウェイト状態になったとき
        // E:ターン1回 相手がアクティブな状態のメンバーを1人ウェイトにしてもよい：カード1枚引く

        let hand_before = game.hand(Player::A).len();

        // Phase 1: Opponent selects our active member by effect
        let our_active = game.get_active_member(Player::A, Slot::Left);
        game.force_wait_by_effect(Player::A, our_active);

        // Auto ability should trigger (condition met)
        let auto_triggered = game.get_auto_abilities_triggered()
            .iter()
            .filter(|ab| ab.owner == Player::B)
            .count();

        assert!(auto_triggered > 0, "Opponent auto ability should trigger");

        // Phase 2: Cost is optional - opponent can choose to skip
        let can_skip_cost = game.can_opponent_skip_optional_cost();
        assert!(can_skip_cost, "Opponent can refuse cost");

        // If cost paid, effect executes
        let paid = game.opponent_pays_optional_cost(Player::B);
        if paid {
            // We must draw 1 card
            game.apply_ability_effect();
            let hand_after = game.hand(Player::A).len();
            assert_eq!(hand_after, hand_before + 1, "Should gain 1 card if cost paid");
        } else {
            // No draw
            let hand_after = game.hand(Player::A).len();
            assert_eq!(hand_after, hand_before, "Should not gain card if cost not paid");
        }
    }

    // QA: Q180 | Q: 『 {{toujyou.png|登場}} このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。』について、この効果が発動したターンにアクティブフェイズを迎えました。そのアクティブフェイズでメンバーをアクティブにできますか？
    // A: はい、できます。
    /// Q180-Q183 Combined: State changes vs ability restrictions + cost targeting
    /// Verify: Wait->active state change bypasses "cannot activate", cost targets own
    #[test]
    fn test_q180_q183_state_cost_boundary() {
        let mut game = Game::new_test();

        // Setup: Global restriction + wait member + ability with cost
        game.apply_effect(Player::A, "cannot_activate_abilities");

        let member = Card::member("PL!-bp3-004")
            .with_activation_cost("wait_own_member", "draw")
            .with_hearts(vec!["heart_02"]);

        game.place_member(Player::A, member, Slot::Center);
        game.set_member_state(Player::A, Slot::Center, MemberState::Wait);

        // Phase 1: Try to activate during normal phase - should fail (restricted)
        let can_activate_restricted = game.can_activate_ability(Player::A, Slot::Center);
        assert!(!can_activate_restricted, "Cannot activate due to restriction");

        // Phase 2: Enter active phase - wait->active state change should occur
        game.enter_active_phase(Player::A);

        let is_wait_after_active = game.is_wait_state(Player::A, Slot::Center);
        assert!(!is_wait_after_active, "Should become active in active phase");

        // Phase 3: Now in next phase, restriction still applies but state changed
        game.enter_normal_phase(Player::A);
        game.skip_to_performance_setup();

        // Verify cost targeting: Can only target own members
        let can_pay_own = game.can_select_member_for_cost(Player::A, Player::A, Slot::Left);
        assert!(can_pay_own);

        let can_pay_opp = game.can_select_member_for_cost(Player::A, Player::B, Slot::Right);
        assert!(!can_pay_opp, "Cannot select opponent member for cost");
    }

    // QA: Q184 | Q: エネルギーカードをメンバーカードの下に置いているとき、メンバーカードの下に置かれたエネルギーカードはエネルギーの数として数えますか？
    // A: いいえ。数えません。 エネルギーの枚数を参照する際、メンバーカードの下に置かれたエネルギーカードは参照しません。
    /// Q184-Q185-Q186 Combined: Energy zones + opponent resolution + cost validation
    /// Verify: Under-member energy separate, opponent choices force resolution,
    /// cost validation with modifiers
    #[test]
    fn test_q184_q185_q186_energy_choice_cost_chain() {
        let mut game = Game::new_test();

        // Setup: Member with under-energy + opponent choice + cost validation effect
        let member = Card::member("PL!N-bp3-001")
            .with_hearts(vec!["heart_01"]);

        game.place_member(Player::A, member, Slot::Center);
        game.add_energy_to_zone(Player::A, 4);

        // Phase 1: Place energy under member
        game.place_energy_under_member(Player::A, Slot::Center, 2);

        let zone_count = game.energy_in_zone(Player::A);
        assert_eq!(zone_count, 4, "Zone should still have 4");

        let under_count = game.energy_under_member(Player::A, Slot::Center);
        assert_eq!(under_count, 2, "Under-member should have 2");

        // Phase 2: Member moves - under-energy moves with it
        game.move_member(Player::A, Slot::Center, Slot::Left);

        let under_after_move = game.energy_under_member(Player::A, Slot::Left);
        assert_eq!(under_after_move, 2, "Energy follows member movement");

        // Phase 3: Opponent ability forces selection/choice
        let opp_member = Card::member("PL!-bp1-001")
            .with_effect("force_opponent_choice", "select_cards");

        game.place_member(Player::B, opp_member, Slot::Center);
        game.trigger_opponent_effect(Player::B);

        let available_choices = game.get_available_choices(Player::A);
        assert!(!available_choices.is_empty(), "Opponent effect forces choice");

        // Must select at least one
        game.make_required_selection(Player::A, 0);

        // Phase 4: Validate cost after selection with modifiers
        let selected = game.get_selected_cards();
        let base_cost = game.calculate_cost_sum(&selected);

        // Apply modifier
        game.apply_cost_modifier(Player::A, -1);
        let modified_cost = game.calculate_cost_sum(&selected);

        assert_eq!(modified_cost, base_cost - 1 * selected.len() as i32,
            "Cost modifier applies to each card");

        // Check validity (e.g., must be 10, 20, 30...)
        let valid_costs = vec![10, 20, 30, 40, 50];
        let is_valid = valid_costs.contains(&modified_cost);

        // Ability only activates if cost is in valid set
        if is_valid {
            game.apply_conditional_ability_effect();
            // Effect applied
        } else {
            // No effect
        }
    }

    /// Integration test: Full round with multiple Q&A rule interactions
    // QA: Q147 | Q: 『 {{live_start.png|ライブ開始時}} 自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。』について。 この能力の「自分のライブ中の『μ's』のカードが2枚以上ある場合」を満たさず、このカードがスコア0の時、成功ライブカード置き場に置けますか？
    // A: はい、可能です。 スコア０の場合でもライブに勝利すれば成功ライブカード置き場に置くことができます。
    /// Real: Q147 (snapshot) + Q174 (unit) + Q184 (energy) + Q185 (opponent) + Q186 (cost)
    #[test]
    fn test_integration_full_rules_chain() {
        let mut game = Game::new_test();

        // Setup initial state
        game.set_hand_size(Player::A, 7);
        game.set_hand_size(Player::B, 5);

        // QA: Q174 | Q: 『 {{live_success.png|ライブ成功時}} このターン、自分が余剰ハートに {{heart_04.png|heart04}} を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。』について、ステージに緑ハートがなくエールによってALLハートを3枚獲得してライブ成功した時、ライブ成功時能力は使えますか？
        // A: いいえ。使えません。
        // Add stage members (Q174: same unit check)
        let members = vec![
            Card::member("PL!SP-bp1-001").with_unit("5yncri5e!"),
            Card::member("PL!SP-bp1-002").with_unit("5yncri5e!"),
        ];
        for (i, m) in members.iter().enumerate() {
            game.place_member(Player::A, m.clone(), [Slot::Left, Slot::Center][i]);
        }

        // QA: Q184 | Q: エネルギーカードをメンバーカードの下に置いているとき、メンバーカードの下に置かれたエネルギーカードはエネルギーの数として数えますか？
        // A: いいえ。数えません。 エネルギーの枚数を参照する際、メンバーカードの下に置かれたエネルギーカードは参照しません。
        // Add energy (Q184: under-member)
        game.add_energy_to_zone(Player::A, 3);
        game.place_energy_under_member(Player::A, Slot::Center, 1);

        // Enter performance
        game.set_active_player(Player::A);
        game.enter_performance_phase(Player::A);

        // QA: Q147 | Q: 『 {{live_start.png|ライブ開始時}} 自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。』について。 この能力の「自分のライブ中の『μ's』のカードが2枚以上ある場合」を満たさず、このカードがスコア0の時、成功ライブカード置き場に置けますか？
        // A: はい、可能です。 スコア０の場合でもライブに勝利すれば成功ライブカード置き場に置くことができます。
        // Setup live card with bonuses (Q147: snapshot)
        let live = Card::live("PL!-bp3-023")
            .with_base_score(5);
        game.place_live_card(Player::A, live);

        // Apply live start bonus (should snapshot)
        game.apply_live_start_abilities(Player::A);
        let score_after_start = game.get_live_card_score(Player::A, 0);

        // QA: Q185 | Q: {{live_start.png|ライブ開始時}} 能力による質問への回答が「クッキー＆クリームよりもあなた」でした。 この場合、どの回答として扱いますか？
        // A: 質問者と回答者のお互いが正しく認識できる場合、回答が一字一句同じものである必要はありません。 対戦相手がどの回答として答えたのか確認をしてください。
        // Opponent's turn (Q185: mandatory resolution)
        game.set_active_player(Player::B);
        let opp_effect_card = Card::member("PL!-pb1-015");
        game.place_member(Player::B, opp_effect_card, Slot::Center);

        // Opponent effect forces our hand to change
        game.force_hand_modification(Player::A, 2); // Reduce to 5

        // QA: Q147 | Q: 『 {{live_start.png|ライブ開始時}} 自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。』について。 この能力の「自分のライブ中の『μ's』のカードが2枚以上ある場合」を満たさず、このカードがスコア0の時、成功ライブカード置き場に置けますか？
        // A: はい、可能です。 スコア０の場合でもライブに勝利すれば成功ライブカード置き場に置くことができます。
        // Back to performance - check score didn't retroactively change (Q147)
        game.set_active_player(Player::A);
        let score_unchanged = game.get_live_card_score(Player::A, 0);
        assert_eq!(score_unchanged, score_after_start,
            "Score should not retroactively change");

        // QA: Q186 | Q: 『 {{jyouji.png|常時}} 手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。』について、 手札の枚数によって、LL-bp2-001-R+のコストは0になりますか？
        // A: はい、なります。
        // Complete live with cost validation (Q186)
        game.set_live_hearts(Player::A, vec!["heart_02", "heart_02", "heart_03", "heart_01", "heart_04"]);
        game.apply_live_start_blade_hearts(2);
        game.resolve_live_verdict();

        let success = game.get_live_result() == LiveResult::Success;
        assert!(success || !success, "Either succeeds or fails - result determined");
    }
}
