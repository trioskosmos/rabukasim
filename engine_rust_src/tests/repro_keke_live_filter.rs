use engine_rust::core::logic::*;
use engine_rust::test_helpers::*;

#[cfg(test)]
mod tests {
    use super::*;

    fn create_repro_db() -> CardDatabase {
        let mut db = CardDatabase::default();

        // Member Card with Cost 11 (ID: 100)
        let mut member = MemberCard::default();
        member.card_id = 100;
        member.cost = 11;
        db.members.insert(100, member.clone());
        db.members_vec[100 as usize % LOGIC_ID_MASK as usize] = Some(member);

        // Live Card with Required Hearts summing to 12 (ID: 200)
        let mut live = LiveCard::default();
        live.card_id = 200;
        live.required_hearts = [0, 4, 0, 4, 0, 4, 0]; // Sum = 12
        db.lives.insert(200, live.clone());
        db.lives_vec[200 as usize % LOGIC_ID_MASK as usize] = Some(live);

        db
    }

    #[test]
    fn test_cost_filter_member_only_by_default() {
        let db = create_repro_db();
        let state = create_test_state();

        // Filter: COST_GE=11, Type=Any (0)
        // Threshold 11 (0x0B), GE=0
        // attr = (1 << 24) | (11 << 25) = 0x17000000
        let filter_any = 0x17000000;

        // Member should match
        assert!(state.card_matches_filter(&db, 100, filter_any), "Member with Cost 11 should match generic COST_GE=11");

        // Live should NOT match (even though hearts = 12 >= 11) because it's not type-constrained to Live
        assert!(!state.card_matches_filter(&db, 200, filter_any), "Live card should NOT match generic COST_GE=11 (Bug Repro)");
    }

    #[test]
    fn test_cost_filter_explicit_member() {
        let db = create_repro_db();
        let state = create_test_state();

        // Filter: COST_GE=11, Type=Member (1)
        // attr = 0x17000000 | (0x01 << 2) = 0x17000004
        let filter_member = 0x17000004;

        assert!(state.card_matches_filter(&db, 100, filter_member), "Member should match Member-constrained COST_GE=11");
        assert!(!state.card_matches_filter(&db, 200, filter_member), "Live should NOT match Member-constrained COST_GE=11");
    }

    #[test]
    fn test_heart_filter_explicit_live() {
        let db = create_repro_db();
        let state = create_test_state();

        // Filter: HEARTS_GE=11, Type=Live (2)
        // attr = 0x17000000 | (0x02 << 2) = 0x17000008
        let filter_live = 0x17000008;

        assert!(!state.card_matches_filter(&db, 100, filter_live), "Member should NOT match Live-constrained HEARTS_GE=11");
        assert!(state.card_matches_filter(&db, 200, filter_live), "Live should match Live-constrained HEARTS_GE=11");
    }
}
