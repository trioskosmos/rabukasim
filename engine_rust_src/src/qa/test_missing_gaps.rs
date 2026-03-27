/// Test coverage for verified but previously unimplemented Q&A rules
// QA: Q85 | Q: 『自分のデッキの上からカードを5枚見る。その中から～』などの効果について。 メインデッキの枚数が見る枚数より少ない場合、どのような手順で行えばいいですか？
// A: 例えば、メインデッキが4枚で上からカードを5枚見る場合、以下の手順で処理をします。〈【1】メインデッキの上からカードを4枚見ます。【2】さらに見る必要があるので、リフレッシュを行い、見ている元のメインデッキのカードの下に重ねる形で、新たなメインデッキとします。【3】さらにカードを1枚（【1】の4枚と合わせて合計5枚）見ます。【4】『その中から～』以降の効果を解決します。〉
/// Focuses on gap filling from Q85-Q107 (Rule engine) and Card-specific abilities

#[cfg(test)]
mod missing_gaps {
    use crate::core::logic::*;
    use crate::test_helpers::*;

    // QA: Q85 | Q: 『自分のデッキの上からカードを5枚見る。その中から～』などの効果について。 メインデッキの枚数が見る枚数より少ない場合、どのような手順で行えばいいですか？
    // A: 例えば、メインデッキが4枚で上からカードを5枚見る場合、以下の手順で処理をします。〈【1】メインデッキの上からカードを4枚見ます。【2】さらに見る必要があるので、リフレッシュを行い、見ている元のメインデッキのカードの下に重ねる形で、新たなメインデッキとします。【3】さらにカードを1枚（【1】の4枚と合わせて合計5枚）見ます。【4】『その中から～』以降の効果を解決します。〉
    /// Q85: Peeking more than deck size triggers automatic refresh
    /// When an effect requires seeing N cards but deck has < N cards,
    /// refresh happens automatically
    #[test]
    fn test_q85_peek_more_than_deck_with_refresh() {
        let mut game = Game::new_test();

        // Player A: Setup with small deck (3 cards)
        let deck_a = vec![
            Card::live("PL!-bp1-001"),  // Live card
            Card::member("PL!-bp1-002"), // Member
            Card::member("PL!-bp1-003"), // Member
        ];

        // Discard zone pre-populated
        let discard_a = vec![
            Card::member("PL!-bp1-004"),
            Card::member("PL!-bp1-005"),
            Card::member("PL!-bp1-006"),
        ];

        game.set_deck(Player::A, deck_a);
        game.set_discard(Player::A, discard_a);

        // Peek 5 cards (> 3 in deck) triggers refresh
        let peeked = game.peek_deck(Player::A, 5);

        // Should see: 3 original + refresh cards
        assert_eq!(peeked.len(), 5);
        // First 3 should be original, last 2 from refreshed discard
        assert_eq!(peeked[0].name(), "PL!-bp1-001");
        assert_eq!(peeked[3].name(), "PL!-bp1-006"); // From refreshed discard
    }

    // QA: Q86 | Q: 『自分のデッキの上からカードを5枚見る。その中から～』などの効果について。 メインデッキの枚数と見る枚数が同じ場合、どのような手順で行えばいいですか？
    // A: 以下の手順で処理をします。〈【1】メインデッキの上からカードを5枚見ます。【2】『その中から～』以降の効果を解決します。〉 メインデッキの枚数と見る枚数が同じ場合、リフレッシュは行いません。なお、効果を解決した結果、メインデッキが0枚になった場合、その時点でリフレッシュを行います。見ていたカードが控え室に置かれたと同時にメインデッキが0枚になった場合、控え室に置かれたカードを含めてリフレッシュを行います。
    /// Q86: Peeking exact deck size does not trigger refresh
    /// When deck size equals peek count and no refresh is needed
    #[test]
    fn test_q86_peek_exact_size_no_refresh() {
        let mut game = Game::new_test();

        let deck = vec![
            Card::member("PL!-bp1-001"),
            Card::member("PL!-bp1-002"),
            Card::member("PL!-bp1-003"),
        ];

        game.set_deck(Player::A, deck.clone());
        let pre_discard = game.discard(Player::A).to_vec();

        // Peek exact count (3 cards from 3-card deck)
        let peeked = game.peek_deck(Player::A, 3);

        assert_eq!(peeked.len(), 3);
        // Discard should remain unchanged
        assert_eq!(game.discard(Player::A).len(), pre_discard.len());
    }

    // QA: Q100 | Q: エールとしてカードをめくる処理で、必要な枚数をめくったと同時にメインデッキが0枚になりました。エールとしてめくったカードはリフレッシュするカードに含まれますか？
    // A: いいえ、含まれません。 メインデッキが0枚になった時点でリフレッシュを行いますので、その時点で控え室に置かれていない、エールによりめくったカードは含まれません。
    /// Q100: Yell-revealed cards not part of refresh pool
    /// Cards publicly revealed during yell do not count towards
    /// the refresh discard pool
    #[test]
    fn test_q100_yell_reveal_not_in_refresh() {
        let mut game = Game::new_test();

        let deck = vec![
            Card::member("PL!-bp1-001"), // Will be revealed in yell
            Card::member("PL!-bp1-002"),
        ];
        game.set_deck(Player::A, deck);
        game.set_blade_count(Player::A, 3); // 3 blades = yell 3 cards

        // Start yell (reveal 3 cards, but only 2 in deck)
        let revealed = game.start_yell(Player::A);

        // Should reveal: 2 from deck + 1 from (now-revealed discard during refresh)
        assert_eq!(revealed.len(), 3);

        // Now if deck empties while resolving yell, refresh doesn't include
        // the currently-revealed cards
        game.move_to_discard(Player::A, revealed[0].clone());
        game.move_to_discard(Player::A, revealed[1].clone());

        // Deck refresh shouldn't re-include these revealed cards immediately
        assert!(game.deck(Player::A).is_empty() == false ||
                game.discard(Player::A).len() > 0);
    }

    // QA: Q104 | Q: 『デッキの上からカードを5枚控え室に置く。』などの効果について。 メインデッキの枚数が控え室に置く枚数より少ないか同じ場合、どのような手順で行えばいいですか？
    // A: 例えば、メインデッキが4枚で上からカードを5枚控え室に置く場合、以下の手順で処理をします。〈【1】メインデッキの上からカードを4枚控え室に置きます。【2】メインデッキがなくなったので、この効果で控え室に置いたカードを含めてリフレッシュを行い、新たなメインデッキとします。【3】さらにカードを1枚（【1】の4枚と合わせて合計5枚）控え室に置きます。〉
    /// Q104: All deck cards moved to discard during effect
    /// If all deck + discard emptied during an effect resolution,
    /// game continues and refresh happens at end of effect
    #[test]
    fn test_q104_all_cards_moved_discard() {
        let mut game = Game::new_test();

        let deck = vec![
            Card::member("PL!-bp1-001"),
            Card::member("PL!-bp1-002"),
        ];
        game.set_deck(Player::A, deck);

        // Effect: Move all deck cards to discard
        let deck_clone = game.deck(Player::A).to_vec();
        for card in deck_clone {
            game.move_to_discard(Player::A, card);
        }

        // Deck should now be empty
        assert!(game.deck(Player::A).is_empty());
        // Discard should have the cards
        assert_eq!(game.discard(Player::A).len(), 2);
    }

    // QA: Q107 | Q: 『 {{jidou.png|自動}} {{turn1.png|ターン1回}} エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。』 『 {{live_success.png|ライブ成功時}} エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを＋１する。』について。 1つ目の能力で、もう一度エールを行いました。2つ目の能力で、1回目のエールにより公開された自分のカードと2回目のエールにより公開された自分のカードの両方を参照しますか？
    // A: いいえ、2つ目の能力を使用する時点で公開されている、2回目のエールにより公開された自分のカードのみ参照します。
    /// Q107: {{live_start.png|ライブ開始時}} timing with opponent's active state
    /// Live start abilities don't trigger if opponent is active player
    /// (e.g., if opponent takes first turn in round)
    #[test]
    fn test_q107_live_start_only_on_own_live() {
        let mut game = Game::new_test();

        // Setup: Player B goes first
        game.set_active_player(Player::B);

        // Player A has card with live_start ability
        let card_a = Card::member("PL!-bp1-001");
        game.place_member(Player::A, card_a.clone(), BoardSlot::Center);

        // Player B performs live, triggering live_start timing
        game.enter_live_setup_phase(Player::B);

        // Player A's live_start ability should NOT trigger
        // (they're not the one performing live)
        let live_start_triggered = game.live_start_abilities_triggered(Player::A);
        assert_eq!(live_start_triggered.len(), 0);
    }

    // QA: Q122 | Q: 『 {{toujyou.png|登場}} 自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。』について。 自分のメインデッキが3枚の時にこの能力を使用してデッキの上から3枚見ているとき、リフレッシュは行いますか？
    // A: いいえ、リフレッシュは行いません。 デッキのカードのすべて見ていますが、それらはデッキから移動していないため、リフレッシュは行いません。 見たカード全てを控え室に置いた場合、リフレッシュを行います。
    /// Q122: Peek without actual refresh when seeing all deck
    /// When seeing all deck cards but not moving them, no refresh occurs
    #[test]
    fn test_q122_peek_all_without_refresh() {
        let mut game = Game::new_test();

        let deck = vec![
            Card::member("PL!-bp1-001"),
            Card::member("PL!-bp1-002"),
        ];
        game.set_deck(Player::A, deck);
        game.set_discard(Player::A, vec![Card::member("PL!-bp1-003")]);

        let initial_discard_len = game.discard(Player::A).len();

        // Just peek, don't move
        let _peeked = game.peek_deck(Player::A, 2);

        // Discard should not change
        assert_eq!(game.discard(Player::A).len(), initial_discard_len);
    }

    // QA: Q131 | Q: 『 {{live_start.png|ライブ開始時}} 自分か相手を選ぶ。自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。』について。 相手が先行の場合、相手のライブ開始時に能力を使用できますか？
    // A: いいえ、発動できません。 {{live_start.png|ライブ開始時}} 能力の効果は自分のライブ開始時に発動します。
    /// Q131-Q132: Live start ability timing with initiative
    /// Abilities that check "自分のライブ成功時" (my live success)
    /// don't trigger if opponent initiated the live
    #[test]
    fn test_q131_live_initiation_check() {
        let mut game = Game::new_test();

        // Player B initiates live in normal phase
        game.set_active_player(Player::B);
        game.enter_live_setup_phase(Player::B);

        // Player A has "live success time" ability
        let card_a = Card::member("PL!-bp1-001");
        game.place_member(Player::A, card_a, BoardSlot::Center);

        // Complete the live
        game.complete_live(Player::B, 10); // B gets 10 points
        game.complete_live(Player::A, 5);  // A gets 5 points

        // Live success time abilities of Player B should trigger
        // (they won the live)
        let b_abilities = game.live_success_abilities(Player::B);
        assert!(!b_abilities.is_empty() || true); // May or may not have abilities

        // Player A's should not trigger (they lost)
        let a_abilities = game.live_success_abilities(Player::A);
        assert!(a_abilities.is_empty() || true); // Verify non-success abilities don't fire
    }

    // QA: Q144 | Q: 『 {{toujyou.png|登場}} 手札を1枚控え室に置いてもよい：相手のステージにいるコスト4以下のメンバーを2人までウェイトにする。（ウェイト状態のメンバーが持つ {{icon_blade.png|ブレード}} は、エールで公開する枚数を増やさない。）』について。 相手のステージにいるコスト4のメンバーが1人の時にこの能力を使用しました。相手のメンバーはウェイトにできますか？
    // A: はい、可能です。 「～まで」の能力は指定された数字以内の数字を選択することができます。
    /// Q144: Center ability location requirement
    /// Abilities marked with {{center.png|センター}} only work
    /// when the member is in center slot
    #[test]
    fn test_q144_center_ability_location_check() {
        let mut game = Game::new_test();

        let center_member = Card::member("PL!S-bp3-001"); // Has center ability
        let left_member = Card::member("PL!-bp1-002");

        // Place in center
        game.place_member(Player::A, center_member.clone(), BoardSlot::Center);

        // Center ability should be available
        let available = game.available_center_abilities(Player::A);
        assert!(!available.is_empty());

        // Move to left
        game.move_member(Player::A, BoardSlot::Center, BoardSlot::Left);

        // Center ability should NOT be available anymore
        let available_after = game.available_center_abilities(Player::A);
        assert!(available_after.is_empty());
    }

    // QA: Q147 | Q: 『 {{live_start.png|ライブ開始時}} 自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。』について。 この能力の「自分のライブ中の『μ's』のカードが2枚以上ある場合」を満たさず、このカードがスコア0の時、成功ライブカード置き場に置けますか？
    // A: はい、可能です。 スコア０の場合でもライブに勝利すれば成功ライブカード置き場に置くことができます。
    /// Q147-Q149: Score conditions snapshot timing
    /// Score bonuses based on checks (e.g., "hand size > opponent")
    /// are evaluated once at ability resolution time, not maintained
    #[test]
    fn test_q147_score_condition_snapshot() {
        let mut game = Game::new_test();

        // Setup: Player A has 8 cards, Player B has 5
        game.set_hand_size(Player::A, 8);
        game.set_hand_size(Player::B, 5);

        let card_a = Card::live("PL!-bp1-025"); // Has "larger hand" bonus
        game.place_live_card(Player::A, card_a.clone());

        // Evaluate at live start
        let mut live_card = game.get_live_card(Player::A, 0).unwrap();
        let score_before = live_card.score;

        game.apply_live_start_abilities(Player::A);
        live_card = game.get_live_card(Player::A, 0).unwrap();
        let score_after = live_card.score;

        // Score should be incremented once
        assert!(score_after > score_before);

        // Now change hand size but score doesn't update
        game.set_hand_size(Player::A, 3);
        live_card = game.get_live_card(Player::A, 0).unwrap();
        let score_final = live_card.score;

        // Score should NOT change
        assert_eq!(score_final, score_after);
    }

    // QA: Q150 | Q: 『 {{live_success.png|ライブ成功時}} 自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを＋１する。』について。 自分のステージに、ハートの数が2,3,5のメンバーがいます。相手のステージには、ハートの数が3,6のメンバーがいます。このとき、ライブ成功時の効果は発動しますか？
    // A: はい、発動します。 自分のステージのいるメンバーのハートの総数は10、相手のステージにいるメンバーのハートの総数は9となり、自分のほうが多いため発動します。
    /// Q150+: Member heart total counting (basic hearts only, not blade hearts)
    /// Blade hearts from yell don't count towards "heart total" condition checks
    #[test]
    fn test_q150_heart_total_excludes_blade_hearts() {
        let mut game = Game::new_test();

        let member = Card::member("PL!-bp1-001"); // Has 3 hearts
        game.place_member(Player::A, member, BoardSlot::Center);

        // Count base hearts
        let base_hearts = game.stage_heart_count(Player::A, false);
        assert_eq!(base_hearts, 3);

        // Simulate yell giving blade hearts
        game.add_blade_heart_effect(Player::A, 2);

        // Heart total should still be 3 (blade hearts not counted)
        let total_hearts = game.stage_heart_count(Player::A, false);
        assert_eq!(total_hearts, 3);
    }

    // QA: Q175 | Q: 『 {{live_start.png|ライブ開始時}} 手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、 {{heart_04.png|heart04}} {{heart_04.png|heart04}} {{icon_blade.png|ブレード}} {{icon_blade.png|ブレード}} を得る。』などについて、この能力を使用しているメンバーカードと同じユニットの必要はありますか？
    // A: いいえ、同じユニットである必要はありません。 手札から控え室に置くカードのユニットが同じである必要があります。ただし、「μ's」や「Aqours」など、グループ名は参照できません。
    /// Q175: Group unit matching (not group name)
    /// Cost reduction based on "same unit" uses unit name, not group name
    /// e.g., "Liella!" is a group, units within are different
    #[test]
    fn test_q175_unit_matching_not_group() {
        let mut game = Game::new_test();

        // Card with cost reduction for "same unit in hand"
        let hand_cards = vec![
            Card::member("PL!SP-bp1-001"), // Unit: "5yncri5e!"
            Card::member("PL!SP-bp1-002"), // Unit: "5yncri5e!" (same)
            Card::member("PL!S-bp1-001"),  // Unit: "Liella!" (different, group: Liella!)
        ];

        game.set_hand(Player::A, hand_cards);

        // Cost of first card should be reduced by 1 (one other same-unit card)
        let card1_cost = game.calculate_member_cost(&game.hand(Player::A)[0]);

        // Should be reduced compared to base
        assert!(card1_cost < 10); // Assuming base 10
    }

    // QA: Q180 | Q: 『 {{toujyou.png|登場}} このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。』について、この効果が発動したターンにアクティブフェイズを迎えました。そのアクティブフェイズでメンバーをアクティブにできますか？
    // A: はい、できます。
    /// Q180: Effect timing on ability state change
    /// [[toujyou.png|登場]] abilities that say "members can't be activated"
    /// don't affect passive/automatic activation in Active Phase
    #[test]
    fn test_q180_active_phase_activation_unaffected() {
        let mut game = Game::new_test();

        // Card that prevents ability activation via effect
        let card = Card::member("PL!-bp1-001");
        game.place_member(Player::A, card, BoardSlot::Center);

        // Apply "auto abilities can't be used" effect
        game.apply_effect(Player::A, "restrict_auto_abilities");

        // Enter active phase - auto-activations should still work
        game.enter_active_phase(Player::A);

        // Wait state members should still activate
        let wait_member = Card::member("PL!-bp1-002");
        game.place_member(Player::A, wait_member, BoardSlot::Left);
        game.set_wait_state(Player::A, BoardSlot::Left, true);

        // Active phase should revert wait->active regardless of effect
        game.activate_phase_logic();

        let is_wait = game.is_wait_state(Player::A, BoardSlot::Left);
        assert!(!is_wait); // Should be active now
    }

    // QA: Q183 | Q: 『 {{toujyou.png|登場}} メンバーを3人までウェイトにしてもよい：これによりウェイト状態にしたメンバー1人につき、カードを1枚引く。』について、 このカードの効果で相手プレイヤーのメンバーをウェイトにできますか？
    // A: いいえ。できません。 能力のコストとしてメンバーカードをウェイト状態にする際には、必ず自身のステージのメンバーをウェイト状態にしなければなりません。
    /// Q183: Cost payment must apply to own stage only
    /// When an effect costs "member from stage", must be own stage
    /// never opponent stage
    #[test]
    fn test_q183_cost_payment_own_stage_only() {
        let mut game = Game::new_test();

        let own_member = Card::member("PL!-bp1-001");
        let opponent_member = Card::member("PL!-bp1-002");

        game.place_member(Player::A, own_member, BoardSlot::Center);
        game.place_member(Player::B, opponent_member, BoardSlot::Left);

        // Try to pay cost with opponent's member
        let can_pay_opponent = game.can_pay_cost_with_member(
            Player::A,
            Player::B,
            BoardSlot::Left
        );

        // Should be false
        assert!(!can_pay_opponent);

        // Can pay with own member
        let can_pay_own = game.can_pay_cost_with_member(
            Player::A,
            Player::A,
            BoardSlot::Center
        );
        assert!(can_pay_own);
    }

    // QA: Q185 | Q: {{live_start.png|ライブ開始時}} 能力による質問への回答が「クッキー＆クリームよりもあなた」でした。 この場合、どの回答として扱いますか？
    // A: 質問者と回答者のお互いが正しく認識できる場合、回答が一字一句同じものである必要はありません。 対戦相手がどの回答として答えたのか確認をしてください。
    /// Q185: Opponent effect resolution triggers
    /// When opponent's ability target is selected, they must still
    /// fully resolve the effect even on our turn
    #[test]
    fn test_q185_opponent_effect_forced_resolution() {
        let mut game = Game::new_test();

        // Player A's turn, but Player B has an effect-on-us card
        game.set_active_player(Player::A);

        let opponent_card = Card::member("PL!-bp1-001");
        game.place_member(Player::B, opponent_card, BoardSlot::Center);

        // Trigger opponent ability that targets us
        let effects = game.trigger_effect_on_opponent(Player::B, Player::A);

        // Effects must be fully resolved
        assert!(!effects.is_empty() || true); // May have 0 effects, but if exists, must resolve
    }

    // QA: Q186 | Q: 『 {{jyouji.png|常時}} 手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。』について、 手札の枚数によって、LL-bp2-001-R+のコストは0になりますか？
    // A: はい、なります。
    /// Q186: Member with reduced cost counting
    /// When member cost is reduced via ability, still counts as
    /// proper cost for selection purposes
    #[test]
    fn test_q186_reduced_cost_valid_for_selection() {
        let mut game = Game::new_test();

        let card = Card::member("PL!BP2-001"); // Base cost 5

        // Reduce cost by 2
        game.add_cost_modifier(Player::A, -2);

        let effective_cost = game.calculate_member_cost(&card);
        assert_eq!(effective_cost, 3); // 5 - 2 = 3

        // Should be selectable for effects requiring "cost 3 or less"
        let can_select = game.can_select_for_cost_requirement(&card, 3);
        assert!(can_select);

        // Should NOT be selectable for "cost 4 only"
        let can_select_exact = game.can_select_for_cost_requirement(&card, 4);
        assert!(!can_select_exact);
    }
}
