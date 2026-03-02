#[cfg(test)]
mod tests {
    use crate::core::logic::game::GameState;
    use crate::core::logic::card_db::CardDatabase;
    use crate::core::logic::models::*;
    use crate::core::enums::*;
    use crate::core::logic::interpreter::*;
    use crate::core::logic::card_db::MemberCard;

    fn create_test_db() -> CardDatabase {
        use crate::core::logic::card_db::LOGIC_ID_MASK;
        let mut db = CardDatabase::default();
        // ID 100: Liella Member, Cost 1
        let mut m1 = MemberCard::default();
        m1.card_id = 100;
        m1.name = "澁谷かのん".to_string();
        m1.cost = 1;
        m1.groups = vec![3]; // Liella
        db.members.insert(100, m1.clone());
        let lid = (100 & LOGIC_ID_MASK) as usize;
        if db.members_vec.len() <= lid { db.members_vec.resize(lid + 1, None); }
        db.members_vec[lid] = Some(m1);

        // ID 101: Other Member, Cost 5
        let mut m2 = MemberCard::default();
        m2.card_id = 101;
        m2.name = "Other".to_string();
        m2.cost = 5;
        db.members.insert(101, m2.clone());
        let lid2 = (101 & LOGIC_ID_MASK) as usize;
        if db.members_vec.len() <= lid2 { db.members_vec.resize(lid2 + 1, None); }
        db.members_vec[lid2] = Some(m2);

        db
    }

    #[test]
    fn test_hand_filter_liella() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.core.players[0].hand = vec![100, 101, 101].into(); // 1 Liella, 2 Others

        let ctx = AbilityContext::default();

        // Condition: Hand count of Liella! >= 1
        let cond = Condition {
            condition_type: ConditionType::CountHand,
            value: 1,
            attr: 0,
            target_slot: 0,
            params: serde_json::json!({"filter": "GROUP_ID=3"}),
            is_negated: false,
        };

        assert!(check_condition(&state, &db, 0, &cond, &ctx, 0));

        // Condition: Hand count of Liella! >= 2 (should fail)
        let cond2 = Condition {
            condition_type: ConditionType::CountHand,
            value: 2,
            attr: 0,
            target_slot: 0,
            params: serde_json::json!({"filter": "GROUP_ID=3"}),
            is_negated: false,
        };
        assert!(!check_condition(&state, &db, 0, &cond2, &ctx, 0));
    }

    #[test]
    fn test_unique_names_filter() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.core.players[0].stage = [100, 100, -1]; // 2 same cards

        let ctx = AbilityContext::default();

        // Count stage with UNIQUE_NAMES
        let cond = Condition {
            condition_type: ConditionType::CountStage,
            value: 1,
            attr: 0,
            target_slot: 0,
            params: serde_json::json!({"filter": "UNIQUE_NAMES"}),
            is_negated: false,
        };
        assert!(check_condition(&state, &db, 0, &cond, &ctx, 0));

        // Should NOT be >= 2 unique names
        let cond2 = Condition {
            condition_type: ConditionType::CountStage,
            value: 2,
            attr: 0,
            target_slot: 0,
            params: serde_json::json!({"filter": "UNIQUE_NAMES"}),
            is_negated: false,
        };
        assert!(!check_condition(&state, &db, 0, &cond2, &ctx, 0));
    }

    #[test]
    fn test_tapped_filter() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.core.players[0].stage = [100, 101, -1];
        state.core.players[0].set_tapped(0, true); // 100 is tapped

        let ctx = AbilityContext::default();

        // Count tapped
        let cond = Condition {
            condition_type: ConditionType::CountStage,
            value: 1,
            attr: 0,
            target_slot: 0,
            params: serde_json::json!({"filter": "TAPPED"}),
            is_negated: false,
        };
        assert!(check_condition(&state, &db, 0, &cond, &ctx, 0));

        // Count tapped liella
        let cond2 = Condition {
            condition_type: ConditionType::CountStage,
            value: 1,
            attr: 0,
            target_slot: 0,
            params: serde_json::json!({"filter": "TAPPED, GROUP_ID=3"}),
            is_negated: false,
        };
        assert!(check_condition(&state, &db, 0, &cond2, &ctx, 0));
    }

    #[test]
    fn test_filtered_cost_discard() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.core.players[0].hand = vec![101].into(); // Only non-liella

        let ctx = AbilityContext::default();

        // Cost: Discard 1 Liella
        let cost = Cost {
            cost_type: AbilityCostType::DiscardHand,
            value: 1,
            params: serde_json::json!({"filter": "GROUP_ID=3"}),
            is_optional: false,
        };

        assert!(!check_cost(&state, &db, 0, &cost, &ctx));

        // Add Liella
        state.core.players[0].hand.push(100);
        assert!(check_cost(&state, &db, 0, &cost, &ctx));

        // Pay cost
        let success = pay_cost(&mut state, &db, 0, &cost, &ctx);
        assert!(success);
        let expected_hand: smallvec::SmallVec<[i32; 16]> = vec![101].into();
        assert_eq!(state.core.players[0].hand, expected_hand);
        assert_eq!(state.core.players[0].discard.len(), 1);
        assert_eq!(state.core.players[0].discard[0], 100);
    }

    #[test]
    fn test_name_in_filter() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.core.players[0].hand = vec![100, 101].into(); // Kanon, Other

        let ctx = AbilityContext::default();

        // Filter for "澁谷かのん" (Kanon)
        let cond = Condition {
            condition_type: ConditionType::CountHand,
            value: 1,
            attr: 0,
            target_slot: 0,
            params: serde_json::json!({"filter": "NAME_IN=澁谷かのん"}),
            is_negated: false,
        };
        assert!(check_condition(&state, &db, 0, &cond, &ctx, 0));
    }

    #[test]
    fn test_discard_success_live_filter() {
        let db = create_test_db();
        let mut state = GameState::default();
        state.core.players[0].success_lives = vec![100].into(); // Success Live (simulated card ID)

        let ctx = AbilityContext::default();

        // Cost: Discard 1 Success Live with Liella group
        let cost = Cost {
            cost_type: AbilityCostType::DiscardSuccessLive,
            value: 1,
            params: serde_json::json!({"filter": "GROUP_ID=3"}),
            is_optional: false,
        };

        assert!(check_cost(&state, &db, 0, &cost, &ctx));
        assert!(pay_cost(&mut state, &db, 0, &cost, &ctx));
        assert!(state.core.players[0].success_lives.is_empty());
        assert_eq!(state.core.players[0].discard[0], 100);
    }
}
