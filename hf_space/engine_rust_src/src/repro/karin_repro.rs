// use crate::test_helpers::{Action, TestUtils, create_test_db, create_test_state, p_state};

#[cfg(test)]
mod tests {
    use crate::core::logic::*;
    use crate::test_helpers::{Action, create_test_db, create_test_state};


    #[test]
    fn test_karin_activation_and_wait_cost() {
        let mut db = create_test_db();
        let mut state = create_test_state();

        // Asaka Karin (ID 599)
        // TRIGGER: ACTIVATED
        // COST: TAP_MEMBER(0); DISCARD_HAND(1)
        // EFFECT: RECOVER_LIVE(1) -> CARD_HAND

        let mut card = MemberCard::default();
        card.card_id = 599;
        card.name = "Asaka Karin".to_string();
        card.abilities.push(Ability {
            trigger: TriggerType::Activated,
            conditions: vec![Condition {
                condition_type: ConditionType::Turn1,
                ..Default::default()
            }],
            costs: vec![
                Cost { cost_type: AbilityCostType::TapMember, value: 0, ..Default::default() },
                Cost { cost_type: AbilityCostType::DiscardHand, value: 1, ..Default::default() }
            ],
            bytecode: vec![
                58, 1, 0, 6,  // O_MOVE_TO_DISCARD (discard hand)
                15, 1, 0, 6,  // O_RECOVER_LIVE
                1, 0, 0, 0    // O_RETURN
            ],
            ..Default::default()
        });
        db.members.insert(599, card);

        // Add Live card 1500
        let mut live = LiveCard::default();
        live.card_id = 1500;
        live.name = "Test Live".to_string();
        db.lives.insert(1500, live);

        // Setup Player 0
        state.players[0].stage[0] = 599;
        state.players[0].hand.push(100); // Card to discard for cost
        state.players[0].hand.push(101); // Card to discard for effect (O_MOVE_TO_DISCARD)
        state.players[0].discard.push(1500); // Live card to recover

        // Populate deck to prevent auto-refresh
        for i in 200..210 {
            state.players[0].deck.push(i);
        }

        // Verify initial state
        assert_eq!(state.players[0].hand.len(), 2);
        assert_eq!(state.players[0].discard.len(), 1);
        assert!(!state.players[0].is_tapped(0));

        // Act 1: Activate Ability (Slot 0, Ab 0)
        state.step(&db, Action::ActivateAbility { slot_idx: 0, ab_idx: 0 }.id()).expect("Activation failed");

        // After activation:
        // 1. Cost paid: Tapped, Card 101 discarded. Hand: [100], Discard: [1500, 101]
        // 2. Bytecode O_MOVE_TO_DISCARD run -> Suspends.
        assert!(state.players[0].is_tapped(0));
        assert_eq!(state.phase, Phase::Response);
        assert_eq!(state.interaction_stack.last().unwrap().effect_opcode, 58);
        assert_eq!(state.players[0].hand.len(), 1);

        // Act 2: Discard card 100 (Choice index 0)
        state.step(&db, Action::SelectHand { hand_idx: 0 }.id()).expect("Discard step failed");

        // After discard:
        // 1. Card 100 discarded. Hand: [], Discard: [1500, 101, 100]
        // 2. Bytecode O_RECOVER_LIVE run -> Suspends for RECOV_L choice.
        assert_eq!(state.phase, Phase::Response);
        assert_eq!(state.interaction_stack.last().unwrap().effect_opcode, 15);

        // Act 3: Recover ID 1500 (Choice index 0)
        state.step(&db, Action::SelectChoice { choice_idx: 0 }.id()).expect("Recovery step failed");

        // After recovery:
        // 1. ID 1500 moved from discard to looked_cards.
        // 2. Suspends for selection from looked_cards?
        // Wait, handle_recovery suspends with choice_type ChoiceType::RecovL but then immediately pauses for pick?
        // No, RECOV_L moves card to Hand in handle_recovery?
        // Let's check handle_recovery...
        // It says: state.players[p_idx].hand.push(cid);
        // Correct!

        // Wait! My previous trace was wrong. RECOV_L in interpreter adds it to hand immediately.
        // So no suspension needed for picking from looked_cards for RECOV_L?
        // Wait, look at handle_recovery:
        /*
        1802:         let cid = state.players[p_idx].looked_cards.remove(choice);
        1803:         state.players[p_idx].hand.push(cid);
        */
        // Yes, it's immediate.

        // So after Act 3, it should be back to Main.
        assert_eq!(state.phase, Phase::Main, "Should be back in Main phase");
        assert_eq!(state.players[0].hand.len(), 1);
        assert_eq!(state.players[0].hand[0], 1500);
        assert_eq!(state.players[0].discard.len(), 2);
    }
}
