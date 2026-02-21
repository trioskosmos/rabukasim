//! Tests for core game mechanics like Drawing, Stat Buffing, and Playing Members.
//! These tests verify higher-level game flow and simple card placements using production data.

use crate::core::logic::*;
use crate::test_helpers::{load_real_db};

/// Verifies that the O_DRAW opcode correctly moves cards from deck to hand using real card IDs.
#[test]
fn test_opcode_draw() {
    let mut state = GameState::default();
    let db = load_real_db();

    // Eli (121), Rin (124). Total 5 in deck.
    state.core.players[0].deck = vec![121, 124, 121, 124, 121].into();

    let ctx = AbilityContext {
        player_id: 0,
        ..AbilityContext::default()
    };

    // O_DRAW 2
    let bytecode = vec![O_DRAW, 2, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bytecode, &ctx);

    assert_eq!(state.core.players[0].hand.len(), 2);
    assert_eq!(state.core.players[0].deck.len(), 3);
}

/// Verifies that O_ADD_BLADES correctly applies blade buffs to a real member on stage.
#[test]
fn test_opcode_blades() {
    let mut state = GameState::default();
    let db = load_real_db();
    state.core.players[0].stage[0] = 121; // Eli

    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        ..AbilityContext::default()
    };

    // O_ADD_BLADES 3 to SELF (Slot 4)
    let bytecode = vec![O_ADD_BLADES, 3, 0, 4, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bytecode, &ctx);

    assert_eq!(state.core.players[0].blade_buffs[0], 3);
}

/// Verifies that O_ADD_HEARTS correctly applies colored heart buffs to a real member on stage.
#[test]
fn test_opcode_hearts() {
    let mut state = GameState::default();
    let db = load_real_db();
    state.core.players[0].stage[0] = 124; // Rin

    let ctx = AbilityContext {
        player_id: 0,
        area_idx: 0,
        ..AbilityContext::default()
    };

    // O_ADD_HEARTS 1 to Red (Attr 1), Slot 4 (SELF)
    let bytecode = vec![O_ADD_HEARTS, 1, 1, 4, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bytecode, &ctx);

    assert_eq!(state.core.players[0].heart_buffs[0].get_color_count(1), 1);
}

/// Verifies that O_REDUCE_COST correctly modifies the player's cost_reduction stat.
#[test]
fn test_opcode_reduce_cost() {
    let mut state = GameState::default();
    let db = load_real_db();
    let ctx = AbilityContext { player_id: 0, ..AbilityContext::default() };

    // O_REDUCE_COST 2
    let bytecode = vec![O_REDUCE_COST, 2, 0, 0, O_RETURN, 0, 0, 0];
    state.resolve_bytecode(&db, &bytecode, &ctx);

    assert_eq!(state.core.players[0].cost_reduction, 2);
}

/// Verifies that conditional jumps based on hand size (C_COUNT_HAND) work correctly with real IDs.
#[test]
fn test_condition_count_hand() {
    let mut state = GameState::default();
    let db = load_real_db();

    // Hand: Eli (121), Rin (124), Energy (0). Total 3 cards.
    state.core.players[0].hand = vec![121, 124, 0].into();

    let ctx = AbilityContext { player_id: 0, ..AbilityContext::default() };

    // Condition: C_COUNT_HAND GE 3 -> O_DRAW 1
    let bytecode = vec![
        C_COUNT_HAND, 3, 0, 0,
        O_JUMP_IF_FALSE, 1, 0, 0,
        O_DRAW, 1, 0, 0,
        O_RETURN, 0, 0, 0
    ];

    // Case 1: Met
    state.core.players[0].deck = vec![121].into();
    state.resolve_bytecode(&db, &bytecode, &ctx);
    assert_eq!(state.core.players[0].hand.len(), 4);

    // Case 2: Not Met
    state.core.players[0].hand = vec![121].into(); // 1 card
    state.core.players[0].deck = vec![124].into();
    state.resolve_bytecode(&db, &bytecode, &ctx);
    assert_eq!(state.core.players[0].hand.len(), 1);
}

/// Verifies that O_PLAY_MEMBER_FROM_HAND correctly moves a real card from hand to a target stage slot.
#[test]
fn test_opcode_play_member_from_hand() {
    let mut state = GameState::default();
    let db = load_real_db();

    // Hand: [Eli (121), Rin (124)]
    state.core.players[0].hand = vec![121, 124].into();
    // Add infinite energy or enough for cost
    state.core.players[0].energy_zone = vec![9000, 9001, 9002, 9003, 9004].into();

    // choice_index=1 (Rin/124), target_slot=2
    let ctx = AbilityContext {
        player_id: 0,
        choice_index: 1,
        target_slot: 2,
        ..AbilityContext::default()
    };

    // O_PLAY_MEMBER_FROM_HAND
    let bytecode = vec![O_PLAY_MEMBER_FROM_HAND, 0, 0, 0, O_RETURN, 0, 0, 0];

    state.resolve_bytecode(&db, &bytecode, &ctx);

    // Card 124 should be on stage slot 2
    assert_eq!(state.core.players[0].stage[2], 124);
    // Hand should have 1 card (Card 121)
    assert_eq!(state.core.players[0].hand.len(), 1);
    assert_eq!(state.core.players[0].hand[0], 121);
}
