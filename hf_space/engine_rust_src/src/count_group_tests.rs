#[cfg(test)]
mod tests {
    use crate::core::logic::interpreter::conditions::check_condition_opcode;
    use crate::core::logic::*;
    use crate::test_helpers::*;

    #[test]
    fn test_count_group_unique_names() {
        let mut db = create_test_db();
        let mut state = create_test_state();

        // Setup cards: 3 cards with Group 10
        // Card A: ID 3001, Name "Member A", Group 10
        // Card B: ID 3002, Name "Member A" (Duplicate Name), Group 10
        // Card C: ID 3003, Name "Member C", Group 10

        let groups = vec![10];
        add_card(&mut db, 3001, "Member A", groups.clone(), vec![]);
        add_card(&mut db, 3002, "Member A", groups.clone(), vec![]);
        add_card(&mut db, 3003, "Member C", groups.clone(), vec![]);

        // Put all 3 on stage
        state.players[0].stage = [3001, 3002, 3003];

        let ctx = AbilityContext {
            player_id: 0,
            ..Default::default()
        };

        // 1. Total Count (Wait 3, Group 10 Member, Target Self)
        // Revision 5 packing: 1 (Self) | (1 << 2, Member) | (1 << 4, Group Enabled) | (10 << 5, Group ID) = 341
        let passed_total = check_condition_opcode(&state, &db, 208, 3, 341, -1, &ctx, 0);
        assert!(passed_total, "Should find 3 members of Group 10");

        // 2. Unique Count (Wait 3, Group 10 Member, Unique Flag bit 15)
        // Revision 5 packing: 341 | (1 << 15) = 33109
        let passed_unique_3 = check_condition_opcode(&state, &db, 208, 3, 33109, -1, &ctx, 0);
        assert!(
            !passed_unique_3,
            "Should NOT find 3 UNIQUE names (only 2: Member A and Member C)"
        );

        // 3. Unique Count (Wait 2, Group 10 Member, Unique Flag bit 15)
        let passed_unique_2 = check_condition_opcode(&state, &db, 208, 2, 33109, -1, &ctx, 0);
        assert!(passed_unique_2, "Should find 2 UNIQUE names");
    }
}
