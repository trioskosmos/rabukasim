use crate::core::generated_constants::*;
use crate::core::logic::*;

#[test]
fn test_exile_zone_exists() {
    let mut state = GameState::default();

    // Test that we can access and modify the exile zone
    state.core.players[0].exile.push(100);
    assert_eq!(state.core.players[0].exile.len(), 1);
    assert_eq!(state.core.players[0].exile[0], 100);
}

#[test]
fn test_rule_10_5_3_orphan_energy_cleanup() {
    let mut state = GameState::default();
    let db = CardDatabase::default();

    // Setup: Slot 0 has no member (-1) but has energy [10, 20]
    state.core.players[0].stage[0] = -1;
    state.core.players[0].stage_energy[0] = smallvec::smallvec![10, 20];
    state.core.players[0].stage_energy_count[0] = 2; // Although count is derived or tracked separately, let's set it

    // Setup: Energy deck is empty
    state.core.players[0].energy_deck = smallvec::SmallVec::new();

    // Ensure state before rule check
    assert!(!state.core.players[0].stage_energy[0].is_empty());
    assert_eq!(state.core.players[0].energy_deck.len(), 0);

    // Execution
    state.process_rule_checks(&db);

    // Assertion
    // 1. Stage energy should be empty
    assert!(
        state.core.players[0].stage_energy[0].is_empty(),
        "Orphan energy should be removed from stage"
    );
    assert_eq!(
        state.core.players[0].stage_energy_count[0], 0,
        "Energy count should be reset"
    );

    // 2. Energy deck should contain the energy cards
    assert_eq!(
        state.core.players[0].energy_deck.len(),
        2,
        "Energy deck should receive the orphan energy"
    );
    // Since we shuffle, we check containment
    assert!(state.core.players[0].energy_deck.contains(&10));
    assert!(state.core.players[0].energy_deck.contains(&20));
}

#[test]
fn test_play_member_from_hand_opcode_preserves_energy() {
    let mut state = GameState::default();

    // Setup
    // Slot 0 has member 999 and Energy [10, 20]
    state.core.players[0].stage[0] = 999;
    state.core.players[0].stage_energy[0] = smallvec::smallvec![10, 20];
    state.core.players[0].stage_energy_count[0] = 2;
    state.core.players[0].hand = smallvec::smallvec![888]; // Card to play
    state.core.players[0].deck = smallvec::smallvec![123];

    let mut m888 = MemberCard::default();
    m888.card_id = 888;
    let mut m999 = MemberCard::default();
    m999.card_id = 999;

    let mut db = CardDatabase::default();
    db.members.insert(888, m888.clone());
    db.members.insert(999, m999.clone());
    db.members_vec[888] = Some(m888);
    db.members_vec[999] = Some(m999);

    // Opcode: PLAY_MEMBER_FROM_HAND (57)
    // Args: none (uses ctx)
    let bytecode = vec![57, 0, 0, 0, 0, 1, 0, 0, 0, 0];

    let mut ctx = AbilityContext::default();
    ctx.player_id = 0;
    ctx.choice_index = 0; // Hand index 0 (Card 888)
    ctx.target_slot = 0; // Target Slot 0

    // We only invoke resolve_bytecode to test the opcode directly.
    // Step 1: Select Card from Hand (choice_index=0)
    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // Handler should have suspended for the slot.
    assert!(state.interaction_stack.len() > 0);
    let mut resumed_ctx = state.interaction_stack.pop().unwrap().ctx;
    assert_eq!(resumed_ctx.v_remaining, 1);

    // Step 2: Select Slot (choice_index=0)
    resumed_ctx.choice_index = 0;
    state.resolve_bytecode_cref(&db, &bytecode, &resumed_ctx);

    // Assertions

    // 1. Old member 999 should be in discard
    assert_eq!(state.core.players[0].discard.len(), 1);
    assert_eq!(state.core.players[0].discard[0], 999);

    // 2. New member 888 should be in slot 0
    assert_eq!(state.core.players[0].stage[0], 888);

    // 3. Energy should remain!
    assert_eq!(
        state.core.players[0].stage_energy[0].len(),
        2,
        "Energy should be preserved"
    );
    assert_eq!(state.core.players[0].stage_energy[0][0], 10);
    assert_eq!(state.core.players[0].stage_energy[0][1], 20);
    assert_eq!(state.core.players[0].stage_energy_count[0], 2);
}
