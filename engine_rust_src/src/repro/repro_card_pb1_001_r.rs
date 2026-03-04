use crate::core::generated_constants::ACTION_BASE_MODE;
use crate::core::logic::*;
use crate::test_helpers::{load_real_db, TestUtils};
use smallvec::smallvec;

#[test]
fn test_repro_pb1_001_r_softlock_fix() {
    let db = load_real_db();

    // We use the real card 4684 (PL!SP-pb1-001-R) from the compiled database.
    // Ability 0: ON_LIVE_START Select Mode -> [0] Pay 2 Energy, [1] Discard 2 Hand -> else [2] Start Live (Implicit)
    let mut state = GameState::default();
    state.players[0].player_id = 0;
    state.players[1].player_id = 1;

    // Test Case: Empty hand, enough energy.
    // Option 0 (Pay 2 Energy) is VALID. Option 1 (Discard 2 Hand) is INVALID.
    state.players[0].hand.clear();
    state.players[0].energy_zone = smallvec![100, 101]; // 2 Energy available

    let card_id = 4684;
    crate::test_helpers::generate_card_report(card_id);
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_id,
        ability_index: 0,
        ..Default::default()
    };

    // Start the ability to hit the mode selection interaction suspension
    println!("--- Starting Ability for Card {} ---", card_id);
    state.resolve_bytecode_cref(
        &db,
        &db.get_member(card_id).unwrap().abilities[0].bytecode,
        &ctx,
    );
    state.dump_verbose();

    // Engine should be suspended waiting for interaction
    assert_eq!(state.phase, Phase::Response);

    // Generate the actions available to the player at this pause
    let mut actions = Vec::new();
    state.generate_legal_actions(&db, 0, &mut actions);

    // Based on validation logic, only Mode 0 (Pay Energy) should be available. Mode 1 (Discard Hand) is skipped.
    assert!(
        actions.contains(&(ACTION_BASE_MODE as i32 + 0)),
        "Option 0 (Pay Energy) should be valid!"
    );
    assert!(
        !actions.contains(&(ACTION_BASE_MODE as i32 + 1)),
        "Option 1 (Discard Hand) MUST BE HIDDEN to prevent softlock!"
    );
}

#[test]
fn test_repro_pb1_001_r_all_combinations() {
    let db = load_real_db();

    // Test Matrix for Card 4684 (ON_LIVE_START)
    // Mode 0: Pay 2 Energy (v=2)
    // Mode 1: Discard 2 Hand (v=2)

    let scenarios = vec![
        (2, 2, true, true),   // Both valid
        (0, 2, false, true),  // Only hand valid
        (2, 0, true, false),  // Only energy valid
        (0, 0, false, false), // Neither valid — engine will handle gracefully
    ];

    for (en, hn, exp_0, exp_1) in scenarios {
        let mut state = GameState::default();
        state.players[0].hand = (0..hn).map(|i| 1000 + i as i32).collect();
        state.players[0].energy_zone = (0..en).map(|i| (2000 + i) as i32).collect();

        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 4684,
            ability_index: 0,
            ..Default::default()
        };

        let target_id = 4684;
        state.resolve_bytecode_cref(
            &db,
            &db.get_member(target_id).unwrap().abilities[0].bytecode,
            &ctx,
        );
        state.dump_verbose();

        let mut actions = Vec::new();
        state.generate_legal_actions(&db, 0, &mut actions);

        let has_0 = actions.contains(&(ACTION_BASE_MODE as i32 + 0));
        let has_1 = actions.contains(&(ACTION_BASE_MODE as i32 + 1));

        assert_eq!(
            has_0, exp_0,
            "Scenario (En:{}, Hn:{}): Mode 0 mismatch",
            en, hn
        );
        assert_eq!(
            has_1, exp_1,
            "Scenario (En:{}, Hn:{}): Mode 1 mismatch",
            en, hn
        );
    }
}

#[test]
fn test_repro_card_103_full_board() {
    let mut state = GameState::default();
    let db = load_real_db();

    // Fill the board for Player 0
    state.players[0].stage[0] = 1001;
    state.players[0].stage[1] = 1002;
    state.players[0].stage[2] = 1003;

    // Discard has a valid cost-2 member
    state.players[0].discard.push(103); // Play another nico from discard

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: 103, // Triggered by Nico playing
        ability_index: 0,
        ..Default::default()
    };

    // Execute Opcode 63 (PLAY_MEMBER_FROM_DISCARD) with FLAG_EMPTY_SLOT_ONLY
    // The engine should NOT suspend for slot selection because there are 0 valid slots.
    // It should skip the effect for P0.

    state.resolve_bytecode_cref(
        &db,
        &db.get_member(103).unwrap().abilities[0].bytecode,
        &ctx,
    );
    state.dump_verbose();

    // Verification:
    // 1. Board should still be the same (no overlaps)
    assert_eq!(state.players[0].stage[0], 1001);
    assert_eq!(state.players[0].stage[1], 1002);
    assert_eq!(state.players[0].stage[2], 1003);

    // 2. The Nico in discard should STILL BE in discard (it wasn't moved/lost)
    assert!(state.players[0].discard.contains(&103));

    // 3. Since P0 skipped, it should have moved to P1's part of the ability or finished.
    // If P1 board is also full, phase should NOT be Response.
    assert_ne!(state.phase, Phase::Response);
}
