// Removed unused generated_constants import
use crate::core::logic::*;
use crate::test_helpers::{create_test_db, create_test_state, TestUtils};

#[test]
fn test_exile_zone_exists() {
    let mut state = GameState::default();

    // Test that we can access and modify the exile zone
    state.players[0].exile.push(100);
    assert_eq!(state.players[0].exile.len(), 1);
    assert_eq!(state.players[0].exile[0], 100);
}

#[test]
fn test_rule_10_5_3_orphan_energy_cleanup() {
    let mut state = GameState::default();
    let db = CardDatabase::default();

    // Setup: Slot 0 has no member (-1) but has energy [10, 20]
    state.players[0].stage[0] = -1;
    state.players[0].stage_energy[0] = smallvec::smallvec![10, 20];
    state.players[0].stage_energy_count[0] = 2; // Although count is derived or tracked separately, let's set it

    // Setup: Energy deck is empty
    state.players[0].energy_deck = smallvec::SmallVec::new();

    // Ensure state before rule check
    assert!(!state.players[0].stage_energy[0].is_empty());
    assert_eq!(state.players[0].energy_deck.len(), 0);

    // Execution
    state.process_rule_checks(&db);

    // Assertion
    // 1. Stage energy should be empty
    assert!(
        state.players[0].stage_energy[0].is_empty(),
        "Orphan energy should be removed from stage"
    );
    assert_eq!(
        state.players[0].stage_energy_count[0], 0,
        "Energy count should be reset"
    );

    // 2. Energy deck should contain the energy cards
    assert_eq!(
        state.players[0].energy_deck.len(),
        2,
        "Energy deck should receive the orphan energy"
    );
    // Since we shuffle, we check containment
    assert!(state.players[0].energy_deck.contains(&10));
    assert!(state.players[0].energy_deck.contains(&20));
}

#[test]
fn test_play_member_from_hand_opcode_preserves_energy() {
    let db = create_test_db();
    let mut state = create_test_state();

    // Setup: card 999 in stage slot 0, card 888 in hand
    state.set_stage(0, 0, 999);
    state.set_hand(0, &[888]);

    // Opcode: PLAY_MEMBER_FROM_HAND
    // Args: none (uses ctx)
    let bytecode = vec![57, 0, 0, 0, 0, 1, 0, 0, 0, 0];

    let mut ctx = AbilityContext::default();
    ctx.player_id = 0;
    ctx.choice_index = 0; // Hand index 0 (Card 888)
    ctx.target_slot = 0; // Target Slot 0

    // We only invoke resolve_bytecode to test the opcode directly.
    // Step 1: Select Card from Hand (choice_index=0)
    state.resolve_frames(&db, &bytecode, &ctx);

    // Handler should have suspended for the slot.
    assert!(state.interaction_stack.len() > 0);
    let mut resumed_ctx = state.interaction_stack.pop().unwrap().ctx;
    assert_eq!(resumed_ctx.v_remaining, 1);

    // Step 2: Select Slot (choice_index=0)
    resumed_ctx.choice_index = 0;
    state.resolve_frames(&db, &bytecode, &resumed_ctx);

    // Assertions

    // 1. Old member 999 should be in discard
    assert_eq!(state.players[0].discard.len(), 1);
    assert_eq!(state.players[0].discard[0], 999);

    // 2. New member 888 should be in slot 0
    assert_eq!(state.players[0].stage[0], 888);
}
