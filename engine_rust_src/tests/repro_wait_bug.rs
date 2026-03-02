use engine_rust::core::enums::Phase;
use engine_rust::core::logic::{resolve_bytecode, AbilityContext, CardDatabase, GameState};

#[test]
fn test_card_558_wait_repro() {
    let mut state = GameState::default();
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();

    let p1 = 0;
    // PL!SP-bp4-002-P is ID 558
    let card_id = 558;

    // Put card in hand
    state.players[p1].hand = vec![card_id].into();
    state.players[p1].deck = vec![584, 1179, 1179, 1179].into();

    // Play card to Center (Slot 1)
    state.phase = Phase::Main;
    let ctx = AbilityContext {
        player_id: p1 as u8,
        source_card_id: card_id,
        area_idx: 1,
        ..Default::default()
    };

    // Simulate OnPlay trigger
    let member = db.get_member(card_id).unwrap();
    let bytecode = &member.abilities[0].bytecode;

    println!("Step 1: Initial call");
    resolve_bytecode(&mut state, &db, std::sync::Arc::new(bytecode.clone()), &ctx);

    // Should be suspended for OPTIONAL/TAP cost
    assert_eq!(state.phase, Phase::Response);
    let interaction = state
        .interaction_stack
        .last()
        .expect("Should have an interaction");
    assert_eq!(interaction.choice_type, "OPTIONAL");

    // Resume with YES (0)
    println!("Step 2: Resume with YES");
    let mut resume_ctx = ctx.clone();
    resume_ctx.choice_index = 0;
    resume_ctx.program_counter = interaction.ctx.program_counter;

    state.phase = Phase::Main; // Reset for execution
    state.interaction_stack.pop(); // Simulate consumption
    resolve_bytecode(
        &mut state,
        &db,
        std::sync::Arc::new(bytecode.clone()),
        &resume_ctx,
    );

    // It should NOT return early. It should proceed to LOOK_AND_CHOOSE.
    // Since we have Liella cards in deck, it should show LOOK_AND_CHOOSE interaction.
    assert_eq!(state.phase, Phase::Response);
    let next_interaction = state
        .interaction_stack
        .last()
        .expect("Should have LOOK_AND_CHOOSE interaction");
    assert_eq!(next_interaction.choice_type, "LOOK_AND_CHOOSE");

    // Card should be tapped
    assert!(state.players[p1].is_tapped(1));
}
