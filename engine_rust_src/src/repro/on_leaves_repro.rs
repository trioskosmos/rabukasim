// use crate::test_helpers::{Action, TestUtils, create_test_db, create_test_state, p_state};

#[cfg(test)]
mod tests {
    use crate::core::logic::*;
    use crate::test_helpers::{create_test_db, create_test_state};
    // use std::collections::HashMap;

    #[test]
    fn test_on_leaves_broadcast_bug() {
        let mut db = create_test_db();
        let mut state = create_test_state();

        // Card A (ID 10): Listener
        // Has OnLeaves ability -> O_META_RULE (Cheer Mod) to increment counter
        let mut card_a = MemberCard::default();
        card_a.card_id = 10;
        card_a.name = "Listener".to_string();
        card_a.abilities.push(Ability {
            trigger: TriggerType::OnLeaves,
            bytecode: vec![
                O_META_RULE, 1, 0, 0, // Increment cheer_mod_count by 1
                O_RETURN, 0, 0, 0
            ],
            ..Default::default()
        });
        db.members.insert(1, card_a);

        // Card B (ID 20): Leaver
        // No special abilities needed, just needs to exist
        let mut card_b = MemberCard::default();
        card_b.card_id = 20;
        card_b.name = "Leaver".to_string();
        db.members.insert(20, card_b);

        // Setup Stage
        // Slot 0: Listener (A)
        state.core.players[0].stage[0] = 10;
        // Slot 1: Leaver (B)
        state.core.players[0].stage[1] = 20;

        // Verify initial state
        assert_eq!(state.core.players[0].cheer_mod_count, 0, "Initial count should be 0");

        // Action: Trigger OnLeaves for Card B (Leaver)
        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 20, // Card B matches this ID
            area_idx: 1,        // Card B is at Slot 1
            trigger_type: TriggerType::OnLeaves,
            ..Default::default()
        };

        // We manually call trigger_abilities to simulate the event
        println!("DEBUG: Triggering OnLeaves for Card B (20) at Slot 1");
        state.trigger_abilities(&db, TriggerType::OnLeaves, &ctx);

        println!("DEBUG: Processing Trigger Queue. Queue len: {}", state.trigger_queue.len());
        state.process_trigger_queue(&db); // Ensure queued abilities execute

        println!("DEBUG: Finished Processing. Cheer Mod Count: {}", state.core.players[0].cheer_mod_count);

        // CHECK: Did Card A trigger?
        // If bug exists: Card A saw the event broadcasting and triggered -> count == 1
        // If correct: Card A checks "Is it me?" -> No -> count == 0

        assert_eq!(state.core.players[0].cheer_mod_count, 0,
            "Broadcasting Bug still present: Listener (Card A) triggered OnLeaves when Leaver (Card B) left!");
    }
}
