use crate::core::logic::*;
use crate::test_helpers::{load_real_db, create_test_state};

/// Verifies that O_DRAW and O_MOVE_TO_DISCARD correctly manipulate hand and deck using real card IDs.
#[test]
fn test_opcode_draw_discard() {
    let db = load_real_db(); // Use production DB
    let mut state = create_test_state();
    state.ui.silent = true;

    // Use real card IDs: 121 (Eli), 124 (Rin)
    state.core.players[0].deck = vec![121, 124, 121, 124, 121].into();

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_DRAW 2
    let bc = vec![O_DRAW, 2, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert_eq!(state.core.players[0].hand.len(), 2);
    assert_eq!(state.core.players[0].deck.len(), 3);
    assert!(state.core.players[0].hand.contains(&121) || state.core.players[0].hand.contains(&124));

    // O_MOVE_TO_DISCARD 1 (attr 2 = Hand)
    // Pre-seed choice_index so it doesn't suspend, since inline bytecode can't be resumed
    let discard_ctx = AbilityContext { player_id: 0, choice_index: 0, ..Default::default() };
    let bc = vec![O_MOVE_TO_DISCARD, 1, 2, 0, 6, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &discard_ctx);

    assert_eq!(state.core.players[0].hand.len(), 1);
    assert_eq!(state.core.players[0].discard.len(), 1);
}

/// Verifies that O_ADD_BLADES, O_ADD_HEARTS, and O_BOOST_SCORE correctly apply stat buffs.
#[test]
fn test_opcode_stats_boost() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.core.players[0].stage[0] = 121; // Real card ID

    let ctx = AbilityContext { player_id: 0, area_idx: 0, ..Default::default() };

    // O_ADD_BLADES 2 to SELF (Slot 4)
    let bc = vec![O_ADD_BLADES, 2, 0, 0, 4, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert_eq!(state.core.players[0].blade_buffs[0], 2);

    // O_ADD_HEARTS 3 (Pink=0) to SELF (Slot 4)
    let bc = vec![O_ADD_HEARTS, 3, 0, 0, 4, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert_eq!(state.core.players[0].heart_buffs[0].get_color_count(0), 3);

    // O_BOOST_SCORE 5 to SELF
    let bc = vec![O_BOOST_SCORE, 5, 0, 0, 0, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert_eq!(state.core.players[0].live_score_bonus, 5);
}

/// Verifies that O_SET_TAPPED can both tap and untap members.
#[test]
fn test_opcode_tap_untap() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.core.players[0].stage[1] = 124; // Real card ID
    state.core.players[0].set_tapped(1, false);

    let ctx = AbilityContext { player_id: 0, area_idx: 1, ..Default::default() };

    // O_SET_TAPPED 1 SELF
    let bc = vec![O_SET_TAPPED, 1, 0, 0, 4, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert!(state.core.players[0].is_tapped(1));

    // O_SET_TAPPED 0 SELF
    let bc = vec![O_SET_TAPPED, 0, 0, 0, 4, O_RETURN, 0, 0, 0, 0];
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert!(!state.core.players[0].is_tapped(1));
}

/// Verifies that conditional jumps (O_JUMP_F) work correctly based on card count in hand (C_COUNT_HAND).
#[test]
fn test_conditions_basic() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.core.players[0].hand = vec![121, 124, 121].into();

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    let bc = vec![
        C_COUNT_HAND, 3, 0, 0, 0,
        O_JUMP_IF_FALSE, 1, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,
        O_RETURN, 0, 0, 0, 0
    ];

    state.core.players[0].deck = vec![124].into();
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert_eq!(state.core.players[0].hand.len(), 4);

    // C_COUNT_HAND GE 5 (False) -> Draw 1
    let mut state = create_test_state();
    state.core.players[0].hand = vec![121, 124, 121].into();
    state.core.players[0].deck = vec![124].into();
    let bc = vec![
        C_COUNT_HAND, 5, 0, 0, 0,
        O_JUMP_IF_FALSE, 1, 0, 0, 0,
        O_DRAW, 1, 0, 0, 0,
        O_RETURN, 0, 0, 0, 0
    ];
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert_eq!(state.core.players[0].hand.len(), 3);
}

/// Verifies that O_LOOK_AND_CHOOSE correctly defaults to deck and moves remainder to discard using real data.
#[test]
fn test_look_and_choose_remainder() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.core.players[0].deck = vec![121, 124, 121, 124, 121].into();

    let ctx = AbilityContext { player_id: 0, ..Default::default() };

    // O_LOOK_DECK 4 -> O_LOOK_AND_CHOOSE 1 to Hand (Source 6)
    let bc = vec![O_LOOK_DECK, 4, 0, 0, 0, O_LOOK_AND_CHOOSE, 1, 0, 0, 6, O_RETURN, 0, 0, 0, 0];

    // Execution 1: Reveal cards
    state.resolve_bytecode_cref(&db, &bc, &ctx);
    assert_eq!(state.phase, Phase::Response);
    assert_eq!(state.core.players[0].looked_cards.len(), 4);
    assert_eq!(state.core.players[0].deck.len(), 1);

    // Simulated selection of index 1
    let mut state2 = state.clone();
    let mut ctx2 = state2.interaction_stack.last().expect("Missing pending_interaction").ctx.clone();
    ctx2.choice_index = 1;
    state2.resolve_bytecode_cref(&db, &bc, &ctx2);

    assert_eq!(state2.players[0].hand.len(), 1);
    assert_eq!(state2.players[0].deck.len(), 4); // 1 unlooked + 3 remainder
    assert_eq!(state2.players[0].looked_cards.len(), 0);

    // Execution 2: Skip selection (999)
    let mut state3 = state.clone();
    let mut ctx3 = state3.interaction_stack.last().expect("Missing pending_interaction").ctx.clone();
    ctx3.choice_index = 999;
    state3.resolve_bytecode_cref(&db, &bc, &ctx3);

    assert_eq!(state3.players[0].hand.len(), 0);
    assert_eq!(state3.players[0].deck.len(), 5); // All 4 + 1 back to deck
}
