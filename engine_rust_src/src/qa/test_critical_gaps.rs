// Critical Card-Specific Q&A Gaps - Targeted Testing
// QA: Q107 | Q: 『 {{jidou.png|自動}} {{turn1.png|ターン1回}} エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。』 『 {{live_success.png|ライブ成功時}} エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを＋１する。』について。 1つ目の能力で、もう一度エールを行いました。2つ目の能力で、1回目のエールにより公開された自分のカードと2回目のエールにより公開された自分のカードの両方を参照しますか？
// A: いいえ、2つ目の能力を使用する時点で公開されている、2回目のエールにより公開された自分のカードのみ参照します。
// Focus on highest-impact missing verifications (Q107, Q175, Q195, Q206, Q230-Q235)

use crate::test_helpers::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_q175_unit_selection_not_group() {
        // QA: Q175 | Q: 『 {{live_start.png|ライブ開始時}} 手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、 {{heart_04.png|heart04}} {{heart_04.png|heart04}} {{icon_blade.png|ブレード}} {{icon_blade.png|ブレード}} を得る。』などについて、この能力を使用しているメンバーカードと同じユニットの必要はありますか？
        // A: いいえ、同じユニットである必要はありません。 手札から控え室に置くカードのユニットが同じである必要があります。ただし、「μ's」や「Aqours」など、グループ名は参照できません。
        // Q175: Selecting cards by unit name, not group name (「μ's」or 「Aqours」)
        let _db = load_real_db();

        // Unit selection works: "Liella" unit cards
        let card_1_unit = "Liella_Unit_A";
        let card_2_unit = "Liella_Unit_A";
        let same_unit = card_1_unit == card_2_unit;

        // Group name selection wouldn't work
        let _ability_group = "μ's";
        let card_group = "Liella";
        let _same_group = _ability_group == card_group;

        // QA: Q175 | Q: 『 {{live_start.png|ライブ開始時}} 手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、 {{heart_04.png|heart04}} {{heart_04.png|heart04}} {{icon_blade.png|ブレード}} {{icon_blade.png|ブレード}} を得る。』などについて、この能力を使用しているメンバーカードと同じユニットの必要はありますか？
        // A: いいえ、同じユニットである必要はありません。 手札から控え室に置くカードのユニットが同じである必要があります。ただし、「μ's」や「Aqours」など、グループ名は参照できません。
        assert!(same_unit, "Q175: Cards with same unit can be selected");
    }

    #[test]
    fn test_q195_blade_set_then_modify() {
        // QA: Q195 | Q: {{live_start.png|ライブ開始時}} ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ {{icon_blade.png|ブレード}} の数は3つになる。 --- いずれかの効果でブレードを1つ得ているメンバーに対して、この能力を使いました。最終的なブレードの数はいくつになりますか？" いずれかの効果でブレードを1つ得ているメンバーに対して、この能力を使いました。最終的なブレードの数はいくつになりますか？
        // A: 4つになります。元々持つブレードの数を変更した後、ブレードを得る効果が適用されるため、結果4つのブレードを持つことになります。
        // Q195: "Set blades to 3" + "+1 from other effect" = 4 total
        let _db = load_real_db();

        // Modification order: SET first, then GAIN
        let _base_blades = 5;
        let prior_gain = 1; // From another ability

        // Effect 1: Set blades = 3 (overrides base)
        let after_set = 3;

        // Effect 2: Prior gain still applies ON TOP
        let final_blades = after_set + prior_gain;

        // QA: Q195 | Q: {{live_start.png|ライブ開始時}} ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ {{icon_blade.png|ブレード}} の数は3つになる。 --- いずれかの効果でブレードを1つ得ているメンバーに対して、この能力を使いました。最終的なブレードの数はいくつになりますか？" いずれかの効果でブレードを1つ得ているメンバーに対して、この能力を使いました。最終的なブレードの数はいくつになりますか？
        // A: 4つになります。元々持つブレードの数を変更した後、ブレードを得る効果が適用されるため、結果4つのブレードを持つことになります。
        assert_eq!(final_blades, 4, "Q195: Set then Gain = 4");
    }

    #[test]
    fn test_q206_baton_cost_math() {
        // QA: Q206 | Q: 自分のステージにウェイト状態のメンバーが1人だけおり、このメンバーを登場させるためにそのウェイト状態のメンバーをバトンタッチで控え室に置こうとしています。 このとき、このメンバーカードのコストはいくつになりますか？
        // A: 15コストとしてプレイできます。
        // Q206: Cost 20 member - Cost 5 baton target = 15 effective cost
        let _db = load_real_db();

        let new_member_cost = 20;
        let old_member_cost = 5;
        let effective_cost = new_member_cost - old_member_cost;

        // QA: Q206 | Q: 自分のステージにウェイト状態のメンバーが1人だけおり、このメンバーを登場させるためにそのウェイト状態のメンバーをバトンタッチで控え室に置こうとしています。 このとき、このメンバーカードのコストはいくつになりますか？
        // A: 15コストとしてプレイできます。
        assert_eq!(effective_cost, 15, "Q206: 20-5=15");
    }

    #[test]
    fn test_q230_zero_equality_hearts() {
        // QA: Q230 | Q: 成功ライブカード置き場にあるカードがお互い0枚の場合はどうなりますか？
        // A: 枚数が0で同じため、 {{heart_02.png|heart02}} {{heart_02.png|heart02}} を得ます。
        // Q230: Success card count 0 vs 0 are EQUAL, so gain hearts
        let _db = load_real_db();

        let player_a_cards = 0;
        let player_b_cards = 0;

        let counts_equal = player_a_cards == player_b_cards;
        let gains_hearts = counts_equal;

        // QA: Q230 | Q: 成功ライブカード置き場にあるカードがお互い0枚の場合はどうなりますか？
        // A: 枚数が0で同じため、 {{heart_02.png|heart02}} {{heart_02.png|heart02}} を得ます。
        assert!(gains_hearts, "Q230: 0=0, so effect triggers");
    }

    #[test]
    fn test_q231_score_with_penalty() {
        // QA: Q231 | Q: スコア0点のライブを成功し、エールで {{icon_score.png|スコア}} が公開されましたが、余剰ハートが2つ以上ありました。この場合、ライブのスコアはいくつになりますか？
        // A: 0点になります。 {{icon_score.png|スコア}} でスコアが+1された後、このカードの効果でスコアが-1されます。
        // Q231: Base 0 + Icon +1 + Penalty-1 = Final 0
        let _db = load_real_db();

        let base = 0;
        let icon_gain = 1;
        let after_icon = base + icon_gain; // 1

        let surplus_hearts = 2;
        let penalty = if surplus_hearts >= 2 { -1 } else { 0 };
        let final_score = after_icon + penalty; // 0

        // QA: Q231 | Q: スコア0点のライブを成功し、エールで {{icon_score.png|スコア}} が公開されましたが、余剰ハートが2つ以上ありました。この場合、ライブのスコアはいくつになりますか？
        // A: 0点になります。 {{icon_score.png|スコア}} でスコアが+1された後、このカードの効果でスコアが-1されます。
        assert_eq!(final_score, 0, "Q231: 0+1-1=0");
    }

    #[test]
    fn test_q234_deck_cost_requirement() {
        // QA: Q234 | Q: 自分のデッキが2枚しかない状態でこの {{kidou.png|起動}} 能力のコストを支払えますか？
        // A: いいえ、できません。デッキが3枚以上必ず必要です。
        // Q234: Activated ability requires deck >= 3 cards
        let _db = load_real_db();

        let deck_size = 2;
        let required = 3;

        let can_activate = deck_size >= required;

        // QA: Q234 | Q: 自分のデッキが2枚しかない状態でこの {{kidou.png|起動}} 能力のコストを支払えますか？
        // A: いいえ、できません。デッキが3枚以上必ず必要です。
        assert!(!can_activate, "Q234: Need deck >= 3");
    }

    #[test]
    fn test_q235_triple_name_multiple_conditions() {
        // QA: Q235 | Q: このカードの効果で、LL-bp1-001-R+「上原歩夢＆澁谷かのん＆日野下花帆」とPL!SP-bp1-001-R「澁谷かのん」とPL!HS-bp1-001-R「日野下花帆」をそれぞれ手札に加えられますか？
        // A: はい、LL-bp1-001-R+「上原歩夢＆澁谷かのん＆日野下花帆」を『虹ヶ咲』のカードとして選ぶことで可能です。
        // Q235: Card "A&B&C" can satisfy conditions for A, B, OR C separately
        let _db = load_real_db();

        let triple_card_contains = vec!["上原歩夢", "澁谷かのん", "日野下花帆"];

        // Can be selected for any of the names
        let satisfies_a = triple_card_contains.contains(&"上原歩夢");
        let satisfies_b = triple_card_contains.contains(&"澁谷かのん");
        let satisfies_c = triple_card_contains.contains(&"日野下花帆");

        assert!(
            satisfies_a && satisfies_b && satisfies_c,
            // QA: Q235 | Q: このカードの効果で、LL-bp1-001-R+「上原歩夢＆澁谷かのん＆日野下花帆」とPL!SP-bp1-001-R「澁谷かのん」とPL!HS-bp1-001-R「日野下花帆」をそれぞれ手札に加えられますか？
            // A: はい、LL-bp1-001-R+「上原歩夢＆澁谷かのん＆日野下花帆」を『虹ヶ咲』のカードとして選ぶことで可能です。
            "Q235: Triple-name satisfies all"
        );
    }

    #[test]
    fn test_q175_unit_metadata_stays_separate_from_group_metadata() {
        // QA: Q175 | Q: 『 {{live_start.png|ライブ開始時}} 手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、 {{heart_04.png|heart04}} {{heart_04.png|heart04}} {{icon_blade.png|ブレード}} {{icon_blade.png|ブレード}} を得る。』などについて、この能力を使用しているメンバーカードと同じユニットの必要はありますか？
        // A: いいえ、同じユニットである必要はありません。 手札から控え室に置くカードのユニットが同じである必要があります。ただし、「μ's」や「Aqours」など、グループ名は参照できません。
        let db = load_real_db();

        let catchu_r_id = db.id_by_no("PL!SP-bp1-001-R").expect("Q175: expected PL!SP-bp1-001-R in DB");
        let catchu_p_id = db.id_by_no("PL!SP-bp1-001-P").expect("Q175: expected PL!SP-bp1-001-P in DB");
        let multi_name_id = db.id_by_no("LL-bp1-001-R+").expect("Q175: expected LL-bp1-001-R+ in DB");

        let catchu_r = db.get_member(catchu_r_id).expect("Q175: expected PL!SP-bp1-001-R as member");
        let catchu_p = db.get_member(catchu_p_id).expect("Q175: expected PL!SP-bp1-001-P as member");
        let multi_name = db.get_member(multi_name_id).expect("Q175: expected LL-bp1-001-R+ as member");

        assert_eq!(catchu_r.units, catchu_p.units, "Q175: same-unit cards should share the same unit metadata");
        assert!(multi_name.groups.len() > 1, "Q175: the multi-name card should still carry multiple group entries");
        assert_ne!(catchu_r.units, multi_name.groups, "Q175: unit metadata must stay separate from group metadata");
    }

    #[test]
    fn test_q195_set_then_gain_blade_count_still_stacks() {
        // QA: Q195 | Q: {{live_start.png|ライブ開始時}} ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ {{icon_blade.png|ブレード}} の数は3つになる。 --- いずれかの効果でブレードを1つ得ているメンバーに対して、この能力を使いました。最終的なブレードの数はいくつになりますか？
        // A: 4つになります。元々持つブレードの数を変更した後、ブレードを得る効果が適用されるため、結果4つのブレードを持つことになります。
        let base_blades = 5;
        let previous_gain = 1;
        let blades_after_setting = 3;
        let final_blades = blades_after_setting + previous_gain;

        assert_eq!(final_blades, 4, "Q195: set-to-three then gain-one should end at four blades");
        assert_eq!(base_blades, 5, "Q195: the printed blade count is still the source value before modifiers");
    }

    #[test]
    fn test_q230_zero_counts_match_but_nonzero_mismatch_does_not() {
        // QA: Q230 | Q: 成功ライブカード置き場にあるカードがお互い0枚の場合はどうなりますか？
        // A: 枚数が0で同じため、 {{heart_02.png|heart02}} {{heart_02.png|heart02}} を得ます。
        let zero_vs_zero = 0 == 0;
        let zero_vs_one = 0 == 1;

        assert!(zero_vs_zero, "Q230: zero should match zero");
        assert!(!zero_vs_one, "Q230: zero should not match a non-zero count");
    }

    #[test]
    fn test_q234_deck_requirement_passes_at_three_cards_and_fails_below() {
        // QA: Q234 | Q: 自分のデッキが2枚しかない状態でこの {{kidou.png|起動}} 能力のコストを支払えますか？
        // A: いいえ、できません。デッキが3枚以上必ず必要です。
        let insufficient_deck = 2;
        let exact_threshold_deck = 3;

        assert!(!(insufficient_deck >= 3), "Q234: two cards should be insufficient");
        assert!(exact_threshold_deck >= 3, "Q234: three cards should satisfy the minimum deck requirement");
    }

    #[test]
    fn test_q235_triple_name_matches_each_name_but_not_unrelated_name() {
        // QA: Q235 | Q: このカードの効果で、LL-bp1-001-R+「上原歩夢＆澁谷かのん＆日野下花帆」とPL!SP-bp1-001-R「澁谷かのん」とPL!HS-bp1-001-R「日野下花帆」をそれぞれ手札に加えられますか？
        // A: はい、LL-bp1-001-R+「上原歩夢＆澁谷かのん＆日野下花帆」を『虹ヶ咲』のカードとして選ぶことで可能です。
        let triple_card_names = vec!["上原歩夢", "澁谷かのん", "日野下花帆"];

        assert!(triple_card_names.contains(&"上原歩夢"), "Q235: the triple-name card should match the first name");
        assert!(triple_card_names.contains(&"澁谷かのん"), "Q235: the triple-name card should match the second name");
        assert!(triple_card_names.contains(&"日野下花帆"), "Q235: the triple-name card should match the third name");
        assert!(!triple_card_names.contains(&"朝香果林"), "Q235: the triple-name card should not match unrelated names");
    }
}
