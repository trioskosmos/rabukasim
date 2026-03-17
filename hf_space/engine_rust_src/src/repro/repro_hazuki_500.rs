use crate::test_helpers::*;
use crate::core::enums::*;

#[test]
fn test_hazuki_500_optional_cost_skip() {
    let mut state = create_test_state();
    let db = load_real_db();
    state.ui.silent = true;

    let p_idx = 0usize;
    state.current_player = p_idx as u8;

    // Ren Hazuki (500)
    // [On Play] You may put 1 card from your hand into the waiting room:
    // Look at the top 5 cards of your deck. You may reveal up to 1 'Liella!' card among them and add it to your hand.
    // Put the rest into the waiting room.

    let hazuki_id = 500;
    state.players[p_idx].hand.push(hazuki_id);
    state.players[p_idx].hand.push(999); // Dummy card to discard
    state.players[p_idx].stage[0] = hazuki_id; // Set on stage

    // Set up deck with some Liella cards
    state.players[p_idx].deck = vec![101, 101, 101, 101, 101].into();

    // Trigger OnPlay
      // Trigger OnPlay using the unified entry point
    state.trigger_event(&db, TriggerType::OnPlay, p_idx, hazuki_id, 0, 0, -1);
    state.process_trigger_queue(&db);

    // Initial state: Should be suspended for optional discard
    assert_eq!(state.phase, Phase::Response);

    // Simulate user choosing NOT to pay (Skip/Cancel)
    // For ChoiceType::Optional, usually 1 is skip, but standard ChoiceType is CHOICE_DONE (99) or 1?
    // Let's check interaction.rs for Optional prompt.
    // Wait, handle_move_to_discard uses ChoiceType::Optional if it's the first prompt?
    // Actually handle_move_to_discard uses ChoiceType::SelectHandDiscard (12).
    // Ren Hazuki pseudocode: DISCARD_HAND(1) (Optional) -> SUCCESS

    // Let's check current interaction
    let interact = state.interaction_stack.last().expect("Should be suspended");
    assert_eq!(interact.choice_type as u8, ChoiceType::SelectHandDiscard as u8);

    // Send Pass action (0) to skip optional discard
    state.step(&db, 0).expect("Should handle skip");

    // In the FIXED version, it returns RETURN (finishing the ability)
    // because JUMP_IF_FALSE (ip=05) should now jump to ip=20
    assert_eq!(state.phase, Phase::Main, "Should have returned to Main phase after skipping cost");

    // If it proceeds, deck would be moved to looked_cards
    assert_eq!(state.players[p_idx as usize].looked_cards.len(), 0, "Should NOT have cards in looked_cards if cost was skipped");
}
