use engine_rust::core::logic::{CardDatabase, GameState, AbilityContext, PendingInteraction, ActionFactory};
use engine_rust::core::enums::{Phase, ChoiceType, O_SELECT_MODE};
use std::sync::Arc;
use smallvec::smallvec;

#[test]
fn test_repro_kanon_4684() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let p1 = 0;
    let card_id = *db.card_no_to_id.get("PL!SP-pb1-001-R").unwrap();

    // Ability 0: ON_LIVE_START
    let ab = db.get_member(card_id).unwrap().abilities.get(0).unwrap().clone();

    // ----------------------------------------------------------------------------------
    // Case 1: Select "Pay Energy" (Choice 0)
    // ----------------------------------------------------------------------------------
    state.core.players[p1].energy_zone = smallvec![100, 101, 102];
    state.core.players[p1].tapped_energy_mask = 0;
    state.core.players[p1].hand = smallvec![1, 2];
    state.core.interaction_stack.clear();

    let mut ctx = AbilityContext::default();
    ctx.player_id = p1 as u8;
    ctx.source_card_id = card_id;
    ctx.ability_index = 0;
    ctx.choice_index = 0; // Pay Energy

    engine_rust::core::logic::interpreter::resolve_bytecode(
        &mut state,
        &db,
        Arc::new(ab.bytecode.clone()),
        &mut ctx,
    );

    // Verify 2 energy tapped
    assert_eq!(state.core.players[p1].tapped_energy_mask.count_ones(), 2, "2 energy should be tapped");
    assert_eq!(state.core.players[p1].hand.len(), 2, "Hand should remain 2 cards");

    // ----------------------------------------------------------------------------------
    // Case 2: Select "Discard Hand" (Choice 1)
    // ----------------------------------------------------------------------------------
    state.core.players[p1].tapped_energy_mask = 0; // Reset
    state.core.players[p1].hand = smallvec![1, 2, 3];
    state.core.interaction_stack.clear();

    let mut ctx2 = AbilityContext::default();
    ctx2.player_id = p1 as u8;
    ctx2.source_card_id = card_id;
    ctx2.ability_index = 0;
    ctx2.choice_index = 1; // Discard Hand

    engine_rust::core::logic::interpreter::resolve_bytecode(
        &mut state,
        &db,
        Arc::new(ab.bytecode.clone()),
        &mut ctx2,
    );

    // Should be suspended for MOVE_TO_DISCARD
    assert_eq!(state.core.phase, Phase::Response, "Should be in Response phase for card selection");
    assert_eq!(state.core.interaction_stack.len(), 1);
    let pi = state.core.interaction_stack.last().unwrap();
    assert_eq!(pi.choice_type, ChoiceType::SelectHandDiscard);
    assert_eq!(pi.v_remaining, 2, "Should expect 2 cards to discard");

    // Verify choice index was reset in the engine (so it doesn't try to use it for card selection yet)
    assert_eq!(pi.ctx.choice_index, -1, "Choice index should be reset before suspension");

    // ----------------------------------------------------------------------------------
    // Case 3: Verify Labels via ActionFactory
    // ----------------------------------------------------------------------------------
    // Simulate being suspended at O_SELECT_MODE
    state.core.interaction_stack.clear();
    let mut pi_modal = PendingInteraction::default();
    pi_modal.ctx = ctx2.clone();
    pi_modal.card_id = card_id;
    pi_modal.ability_index = 0;
    pi_modal.effect_opcode = O_SELECT_MODE as i32;
    pi_modal.choice_type = ChoiceType::SelectMode;
    pi_modal.v_remaining = 2;
    state.core.interaction_stack.push(pi_modal);

    let label0 = ActionFactory::get_verbose_action_label(500, &state, &db); // SelectMode Choice 0
    let label1 = ActionFactory::get_verbose_action_label(501, &state, &db); // SelectMode Choice 1

    println!("Label 0: {}", label0);
    println!("Label 1: {}", label1);

    assert!(label0.contains("PAY_ENERGY"), "Label 0 should contain PAY_ENERGY. Got: {}", label0);
    assert!(label1.contains("DISCARD_HAND"), "Label 1 should contain DISCARD_HAND. Got: {}", label1);
}
