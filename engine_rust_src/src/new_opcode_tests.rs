//! # Tests for BP05 New Opcodes
//!
//! This module contains tests for the new opcodes (91-97) and conditions (301-304)
//! added for BP05 series cards.

use crate::test_helpers::{create_test_state, TestUtils};
use crate::core::logic::{CardDatabase, AbilityContext};
use crate::core::{O_RETURN, O_DRAW, O_LOOK_DECK_DYNAMIC, O_REDUCE_SCORE, O_SKIP_ACTIVATE_PHASE};
use crate::core::{C_COUNT_ENERGY, C_COUNT_ENERGY_EXACT, C_OPPONENT_HAS_EXCESS_HEART, C_SCORE_TOTAL_CHECK};

/// Test O_LOOK_DECK_DYNAMIC (91)
/// Look at cards from deck equal to live score + v
#[test]
fn test_opcode_look_deck_dynamic() {
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str).expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Setup: Set player score to 5
    state.core.players[0].score = 5;
    state.core.players[0].live_score_bonus = 0;

    // Ensure deck has enough cards
    state.set_deck(0, &[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);

    let ctx = AbilityContext {
        source_card_id: 0,
        player_id: 0,
        ..Default::default()
    };

    // Execute O_LOOK_DECK_DYNAMIC with v=2
    // Should look at 5 (score) + 2 = 7 cards
    let bytecode = vec![
        O_LOOK_DECK_DYNAMIC, 2, 0, 0, 0,
        O_RETURN, 0, 0, 0, 0
    ];

    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // Verify: looked_cards should have 7 cards
    assert_eq!(state.core.players[0].looked_cards.len(), 7,
        "Should have looked at 7 cards (score 5 + v 2)");
}

/// Test O_REDUCE_SCORE (92)
/// Reduce live score bonus by v
#[test]
fn test_opcode_reduce_score() {
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str).expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Setup: Set live_score_bonus to 10
    state.core.players[0].live_score_bonus = 10;

    let ctx = AbilityContext {
        source_card_id: 0,
        player_id: 0,
        ..Default::default()
    };

    // Execute O_REDUCE_SCORE with v=3
    let bytecode = vec![
        O_REDUCE_SCORE, 3, 0, 0, 0,
        O_RETURN, 0, 0, 0, 0
    ];

    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // Verify: live_score_bonus should be 7
    assert_eq!(state.core.players[0].live_score_bonus, 7,
        "live_score_bonus should be reduced by 3");
}

/// Test O_REDUCE_SCORE doesn't go negative
#[test]
fn test_opcode_reduce_score_not_negative() {
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str).expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Setup: Set live_score_bonus to 2
    state.core.players[0].live_score_bonus = 2;

    let ctx = AbilityContext {
        source_card_id: 0,
        player_id: 0,
        ..Default::default()
    };

    // Execute O_REDUCE_SCORE with v=5 (more than available)
    let bytecode = vec![
        O_REDUCE_SCORE, 5, 0, 0, 0,
        O_RETURN, 0, 0, 0, 0
    ];

    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // Verify: live_score_bonus should be 0 (not negative)
    assert_eq!(state.core.players[0].live_score_bonus, 0,
        "live_score_bonus should not go negative");
}

/// Test O_SKIP_ACTIVATE_PHASE (95)
/// Set skip_next_activate flag
#[test]
fn test_opcode_skip_activate_phase() {
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str).expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Verify initial state
    assert!(!state.core.players[0].skip_next_activate,
        "skip_next_activate should be false initially");

    let ctx = AbilityContext {
        source_card_id: 0,
        player_id: 0,
        ..Default::default()
    };

    // Execute O_SKIP_ACTIVATE_PHASE
    let bytecode = vec![
        O_SKIP_ACTIVATE_PHASE, 0, 0, 0, 0,
        O_RETURN, 0, 0, 0, 0
    ];

    state.resolve_bytecode_cref(&db, &bytecode, &ctx);

    // Verify: skip_next_activate should be true
    assert!(state.core.players[0].skip_next_activate,
        "skip_next_activate should be true after opcode");
}

/// Test C_COUNT_ENERGY_EXACT (301)
/// Check if energy count equals val exactly
#[test]
fn test_condition_count_energy_exact() {
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str).expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Setup: Set energy zone to have exactly 3 cards
    state.core.players[0].energy_zone.clear();
    for i in 0..3 {
        state.core.players[0].energy_zone.push(5000 + i);
    }

    let ctx = AbilityContext {
        source_card_id: 0,
        player_id: 0,
        ..Default::default()
    };

    // Test condition with val=3 (should pass)
    // Use C_COUNT_ENERGY (213) which counts total energy
    let bytecode_pass = vec![
        C_COUNT_ENERGY, 3, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,  // Draw 1 if condition passes
        O_RETURN, 0, 0, 0, 0
    ];

    let hand_before = state.core.players[0].hand.len();
    state.resolve_bytecode_cref(&db, &bytecode_pass, &ctx);
    assert_eq!(state.core.players[0].hand.len(), hand_before + 1,
        "Should draw 1 card when energy count is exactly 3");

    // Reset
    state.core.players[0].hand.clear();

    // Test condition with val=4 (should fail)
    let bytecode_fail = vec![
        C_COUNT_ENERGY_EXACT, 4, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,  // Draw 1 if condition passes
        O_RETURN, 0, 0, 0, 0
    ];

    let hand_before = state.core.players[0].hand.len();
    state.resolve_bytecode_cref(&db, &bytecode_fail, &ctx);
    assert_eq!(state.core.players[0].hand.len(), hand_before,
        "Should not draw card when energy count is not 4");
}

/// Test C_OPPONENT_HAS_EXCESS_HEART (303)
/// Check if opponent has excess hearts
#[test]
fn test_condition_opponent_has_excess_heart() {
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str).expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Setup: Set opponent excess_hearts to 2
    state.core.players[1].excess_hearts = 2;

    let ctx = AbilityContext {
        source_card_id: 0,
        player_id: 0,
        ..Default::default()
    };

    // Test condition (should pass)
    let bytecode_pass = vec![
        C_OPPONENT_HAS_EXCESS_HEART, 0, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,  // Draw 1 if condition passes
        O_RETURN, 0, 0, 0, 0
    ];

    let hand_before = state.core.players[0].hand.len();
    state.resolve_bytecode_cref(&db, &bytecode_pass, &ctx);
    assert_eq!(state.core.players[0].hand.len(), hand_before + 1,
        "Should draw 1 card when opponent has excess hearts");

    // Reset
    state.core.players[0].hand.clear();
    state.core.players[1].excess_hearts = 0;

    // Test condition (should fail)
    let bytecode_fail = vec![
        C_OPPONENT_HAS_EXCESS_HEART, 0, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,  // Draw 1 if condition passes
        O_RETURN, 0, 0, 0, 0
    ];

    let hand_before = state.core.players[0].hand.len();
    state.resolve_bytecode_cref(&db, &bytecode_fail, &ctx);
    assert_eq!(state.core.players[0].hand.len(), hand_before,
        "Should not draw card when opponent has no excess hearts");
}

/// Test C_SCORE_TOTAL_CHECK (304)
/// Check total score of success lives
#[test]
fn test_condition_score_total_check() {
    use crate::core::logic::card_db::LOGIC_ID_MASK;
    use crate::core::models::LiveCard;

    let mut db = CardDatabase::default();

    // Create a live card with score 15
    let mut live = LiveCard::default();
    live.card_id = 55001;
    live.score = 15;
    db.lives.insert(55001, live.clone());
    let lid = (55001 & LOGIC_ID_MASK) as usize;
    if db.lives_vec.len() <= lid { db.lives_vec.resize(lid + 1, None); }
    db.lives_vec[lid] = Some(live);

    // Create another live card with score 10
    let mut live2 = LiveCard::default();
    live2.card_id = 55002;
    live2.score = 10;
    db.lives.insert(55002, live2.clone());
    let lid2 = (55002 & LOGIC_ID_MASK) as usize;
    if db.lives_vec.len() <= lid2 { db.lives_vec.resize(lid2 + 1, None); }
    db.lives_vec[lid2] = Some(live2);

    let mut state = create_test_state();
    state.debug.debug_mode = true;

    // Setup: Add success live with score 15
    state.core.players[0].success_lives = vec![55001].into();

    let ctx = AbilityContext {
        source_card_id: 0,
        player_id: 0,
        ..Default::default()
    };

    // Test condition with val=15 (should pass)
    let bytecode_pass = vec![
        C_SCORE_TOTAL_CHECK, 15, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,  // Draw 1 if condition passes
        O_RETURN, 0, 0, 0, 0
    ];

    let hand_before = state.core.players[0].hand.len();
    state.resolve_bytecode_cref(&db, &bytecode_pass, &ctx);
    assert_eq!(state.core.players[0].hand.len(), hand_before + 1,
        "Should draw 1 card when total score >= 15");

    // Reset
    state.core.players[0].hand.clear();

    // Test condition with val=20 (should fail)
    let bytecode_fail = vec![
        C_SCORE_TOTAL_CHECK, 20, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,  // Draw 1 if condition passes
        O_RETURN, 0, 0, 0, 0
    ];

    let hand_before = state.core.players[0].hand.len();
    state.resolve_bytecode_cref(&db, &bytecode_fail, &ctx);
    assert_eq!(state.core.players[0].hand.len(), hand_before,
        "Should not draw card when total score < 20");
}
