use engine_rust::core::logic::{AbilityContext, CardDatabase, GameState};
use engine_rust::core::logic::rules;
use engine_rust::core::models::LiveCard;

#[test]
fn test_card_62_constant_cost_increase_score_total_threshold() {
    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let mut db = CardDatabase::from_json(&json_content).unwrap();

    let p1 = 0;
    let card_id = 62;

    state.players[p1].stage[0] = card_id;
    state.players[p1].stage[1] = -1;
    state.players[p1].stage[2] = -1;

    let ctx = AbilityContext {
        player_id: p1 as u8,
        source_card_id: card_id,
        area_idx: 0,
        ..Default::default()
    };

    let member = db.get_member(card_id).expect("Card 62 not found");
    let ability = member.abilities[0].clone();
    let frame_program = ability
        .frame_program
        .as_ref()
        .expect("Card 62 ability should have frame data");

    // Condition fail: no success lives in place.
    state.resolve_semantic_frames(&db, &frame_program.frames, &ctx);
    assert!(
        state.players[p1].cost_modifiers.is_empty(),
        "Cost modifier should not be added when success live score total < 6"
    );

    state.players[p1].cost_modifiers.clear();
    state.players[p1].success_lives = vec![55001, 55002].into();

    let mut live1 = LiveCard::default();
    live1.card_id = 55001;
    live1.score = 3;
    let mut live2 = LiveCard::default();
    live2.card_id = 55002;
    live2.score = 3;

    db.lives.insert(55001, live1);
    db.lives.insert(55002, live2);

    state.resolve_semantic_frames(&db, &frame_program.frames, &ctx);

    assert_eq!(
        state.players[p1].cost_modifiers.len(),
        1,
        "Cost modifier should be added when success live score total >= 6"
    );
    assert_eq!(
        state.players[p1].cost_modifiers[0].1,
        3,
        "The cost modifier should be +3"
    );
}

#[test]
fn test_card_62_cost_increase_does_not_change_hand_play_cost() {
    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let mut db = CardDatabase::from_json(&json_content).unwrap();

    let p1 = 0;
    let stage_card_id = 62;
    let hand_card_id = 143;

    state.players[p1].stage[0] = stage_card_id;
    state.players[p1].stage[1] = -1;
    state.players[p1].stage[2] = -1;
    state.players[p1].hand.push(hand_card_id);

    let ctx = AbilityContext {
        player_id: p1 as u8,
        source_card_id: stage_card_id,
        area_idx: 0,
        ..Default::default()
    };

    let _stage_base_cost = db.get_member(stage_card_id).unwrap().cost as i32;
    let hand_base_cost = rules::get_member_hand_base_cost(
        &state,
        p1,
        hand_card_id,
        &db,
        0,
        0,
    );
    let hand_play_cost = rules::get_member_cost_from_hand_base_and_aura(
        &state,
        p1,
        hand_card_id,
        1,
        -1,
        &db,
        0,
        hand_base_cost,
        None,
    );

    assert_eq!(
        hand_play_cost,
        hand_base_cost,
        "Hand play cost should equal base cost before stage effect"
    );
    assert!(
        state.players[p1].cost_modifiers.is_empty(),
        "No cost modifier should be added when success live total is below threshold"
    );

    state.players[p1].success_lives = vec![55001, 55002].into();
    let mut live1 = engine_rust::core::models::LiveCard::default();
    live1.card_id = 55001;
    live1.score = 3;
    let mut live2 = engine_rust::core::models::LiveCard::default();
    live2.card_id = 55002;
    live2.score = 3;
    db.lives.insert(55001, live1);
    db.lives.insert(55002, live2);

    state.resolve_semantic_frames(&db, &db.get_member(stage_card_id).unwrap().abilities[0].frame_program.as_ref().unwrap().frames, &ctx);

    assert_eq!(
        state.players[p1].cost_modifiers.len(),
        1,
        "Cost modifier should be added when success live total is >= 6"
    );
    assert_eq!(
        state.players[p1].cost_modifiers[0].1,
        3,
        "The added cost modifier should be +3"
    );

    let hand_play_cost_after = rules::get_member_cost_from_hand_base_and_aura(
        &state,
        p1,
        hand_card_id,
        1,
        -1,
        &db,
        0,
        hand_base_cost,
        None,
    );

    assert_eq!(
        hand_play_cost_after,
        hand_base_cost,
        "Hand play cost should remain unchanged even when stage cost increases"
    );
}
