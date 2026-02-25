
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

    // Setup: Slot 0 has no member (-1) but has energy [10, 20]
    state.core.players[0].stage[0] = -1;
    state.core.players[0].stage_energy[0] = vec![10, 20].into();
    state.core.players[0].stage_energy_count[0] = 2; // Although count is derived or tracked separately, let's set it

    // Setup: Energy deck is empty
    state.core.players[0].energy_deck = vec![].into();

    // Ensure state before rule check
    assert!(!state.core.players[0].stage_energy[0].is_empty());
    assert_eq!(state.core.players[0].energy_deck.len(), 0);

    // Execution
    state.process_rule_checks();

    // Assertion
    // 1. Stage energy should be empty
    assert!(state.core.players[0].stage_energy[0].is_empty(), "Orphan energy should be removed from stage");
    assert_eq!(state.core.players[0].stage_energy_count[0], 0, "Energy count should be reset");

    // 2. Energy deck should contain the energy cards
    assert_eq!(state.core.players[0].energy_deck.len(), 2, "Energy deck should receive the orphan energy");
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
    state.core.players[0].stage_energy[0] = vec![10, 20].into();
    state.core.players[0].stage_energy_count[0] = 2;
    state.core.players[0].hand = vec![888].into(); // Card to play
    state.core.players[0].deck = vec![123].into();

    let mut members = std::collections::HashMap::new();
    let m888 = MemberCard { card_id: 888, ..MemberCard::default() };
    let m999 = MemberCard { card_id: 999, ..MemberCard::default() };
    members.insert(888, m888.clone());
    members.insert(999, m999.clone());

    let mut db = CardDatabase {
        members,
        lives: std::collections::HashMap::new(),
        ..CardDatabase::default()
    };
    db.members_vec[888] = Some(m888);
    db.members_vec[999] = Some(m999);

    // Opcode: O_PLAY_MEMBER_FROM_HAND (57)
    // Args: none (uses ctx)
    let bytecode = vec![O_PLAY_MEMBER_FROM_HAND, 0, 0, 0, 0, O_RETURN, 0, 0, 0, 0];

    let ctx = AbilityContext {
        player_id: 0,
        choice_index: 0, // Hand index 0 (Card 888)
        target_slot: 0,  // Target Slot 0
        ..AbilityContext::default()
    };


    // We only invoke resolve_bytecode to test the opcode directly.
    state.resolve_bytecode(&db, &bytecode, &ctx);

    // Assertions

    // 1. Old member 999 should be in discard
    assert_eq!(state.core.players[0].discard.len(), 1);
    assert_eq!(state.core.players[0].discard[0], 999);

    // 2. New member 888 should be in slot 0
    assert_eq!(state.core.players[0].stage[0], 888);

    // 3. Energy should remain!
    assert_eq!(state.core.players[0].stage_energy[0].len(), 2, "Energy should be preserved");
    assert_eq!(state.core.players[0].stage_energy[0][0], 10);
    assert_eq!(state.core.players[0].stage_energy[0][1], 20);
    assert_eq!(state.core.players[0].stage_energy_count[0], 2);
}
