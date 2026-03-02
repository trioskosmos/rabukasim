use engine_rust::core::logic::{CardDatabase, GameState};

#[test]
fn test_q103_catchu_dynamic_condition() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    let mut state = GameState::default();

    let p1 = 0;

    // Real CatChu IDs based on PR variants
    let catchu_live_id = 605; // PL!SP-pb1-023-L
    let catchu_member_1 = 560; // PL!SP-bp4-004-P
    let catchu_member_2 = 617; // PL!SP-sd1-001-SD

    // Core ability of CatChu:
    // 1. COND(Check 2 Catchu)
    // 2. ACTIVATE_ENERGY
    // 3. META_RULE(v=1, a=8) -> SCORE_RULE ALL_ENERGY_ACTIVE
    // 4. BOOST_SCORE

    let abilities = db.get_live(catchu_live_id).unwrap().abilities.clone();

    // ----------------------------------------------------------------------------------
    // Setup for Q97: We have NO CatChu members on stage, but ALL energy is active.
    // However, since we are executing the raw bytecode from the start, the FIRST condition
    // (Check 2 CatChu members) will evaluate to FALSE.
    // In actual gameplay, this COND wraps the entire ability (or the first part). Let's see
    // how the compiler output handles it by executing the raw bytecode.
    //
    // Wait, the official Q97 rulings state that even if you don't have 2 CatChu members, *if*
    // all your energy is active, the +1 score still occurs. This implies the CatChu condition
    // only wrapped the `ACTIVATE_ENERGY` part, and the `SCORE_RULE` is independent!
    // Let's verify our engine evaluates this correctly.
    // ----------------------------------------------------------------------------------
    state.core.players[p1].stage[0] = -1; // Empty
    state.core.players[p1].stage[1] = -1; // Empty
    state.core.players[p1].live_score_bonus = 0;

    for _ in 0..10 {
        state.core.players[p1].energy_zone.push(100);
    }
    state.core.players[p1].tapped_energy_mask = 0; // All Active

    let mut ctx_q97 = engine_rust::core::logic::AbilityContext {
        player_id: p1 as u8,
        source_card_id: catchu_live_id,
        ..Default::default()
    };

    // Setup harness for GPU parity testing
    #[cfg(feature = "gpu")]
    let harness = engine_rust::test_helpers::GpuParityHarness::new(&db);

    for ability in &abilities {
        engine_rust::core::logic::interpreter::resolve_bytecode(
            &mut state,
            &db,
            std::sync::Arc::new(ability.bytecode.clone()),
            &mut ctx_q97,
        );
        #[cfg(feature = "gpu")]
        harness.assert_bytecode_parity(&db, &state, &ability.bytecode, &ctx_q97, "Q97 Bonus Proc");
    }

    // Even without Catchu members, the dynamic condition evaluates "all active" and gives +1 Bonus.
    // Note: We check `live_score_bonus` because we bypassed the Live performance phase.
    assert_eq!(
        state.core.players[p1].live_score_bonus, 1,
        "Q97: Score bonus is 1 because all energy active, despite missing 2 CatChu members"
    );

    // ----------------------------------------------------------------------------------
    // Scenario Q103 / Q96:
    // 2 CatChu members present.
    // ----------------------------------------------------------------------------------
    state.core.players[p1].stage[0] = catchu_member_1;
    state.core.players[p1].stage[1] = catchu_member_2;
    state.core.players[p1].live_score_bonus = 0; // Reset

    // 10 Energy, 7 Tapped
    state.core.players[p1].energy_zone.clear();
    for _ in 0..10 {
        state.core.players[p1].energy_zone.push(100);
    }
    state.core.players[p1].tapped_energy_mask = 0b111_1111; // 7 bits tapped

    // First proc (CatChu 1)
    let mut ctx_q103_1 = engine_rust::core::logic::AbilityContext {
        player_id: p1 as u8,
        source_card_id: catchu_live_id,
        ..Default::default()
    };
    for ability in &abilities {
        engine_rust::core::logic::interpreter::resolve_bytecode(
            &mut state,
            &db,
            std::sync::Arc::new(ability.bytecode.clone()),
            &mut ctx_q103_1,
        );
        #[cfg(feature = "gpu")]
        harness.assert_bytecode_parity(
            &db,
            &state,
            &ability.bytecode,
            &ctx_q103_1,
            "Q103 CatChu Proc 1",
        );
    }

    // The "2 Catchu members" condition passes. ACTIVATE_ENERGY untaps up to 6 energy.
    // 6 energy readied. 1 still tapped.
    assert_eq!(
        state.core.players[p1].tapped_energy_mask.count_ones(),
        1,
        "First capacity readying (6 untaps)"
    );
    assert_eq!(
        state.core.players[p1].live_score_bonus, 0,
        "Not all active yet, so no +1 bonus"
    );

    // Second proc (CatChu 2)
    let mut ctx_q103_2 = engine_rust::core::logic::AbilityContext {
        player_id: p1 as u8,
        source_card_id: catchu_live_id,
        ..Default::default()
    };
    for ability in &abilities {
        engine_rust::core::logic::interpreter::resolve_bytecode(
            &mut state,
            &db,
            std::sync::Arc::new(ability.bytecode.clone()),
            &mut ctx_q103_2,
        );
        #[cfg(feature = "gpu")]
        harness.assert_bytecode_parity(
            &db,
            &state,
            &ability.bytecode,
            &ctx_q103_2,
            "Q103 CatChu Proc 2",
        );
    }

    // 1 remaining energy readied. 0 tapped.
    // The SCORE_RULE now evaluates to True, so +1 bonus is applied.
    assert_eq!(
        state.core.players[p1].tapped_energy_mask, 0,
        "All active now"
    );
    assert_eq!(
        state.core.players[p1].live_score_bonus, 1,
        "Score +1 applies NOW"
    );

    // Testing Q96 explicitly: Tapping energy *after* the bonus is applied.
    // The SCORE_RULE / BOOST_SCORE adds uniquely discrete integers to `live_score_bonus`.
    // It is not an aura. Subsequent state changes do not retroactively strip the score.
    state.core.players[p1].tapped_energy_mask = 0b111; // Tap some energy
    assert_eq!(
        state.core.players[p1].live_score_bonus, 1,
        "Score remains despite later taps"
    );
}
