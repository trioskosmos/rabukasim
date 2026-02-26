#[allow(unused_imports)]
use crate::core::logic::*;
use crate::test_helpers::load_real_db;

#[test]
fn test_meta_rule_yell_mulligan() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = false;
    state.debug.debug_ignore_conditions = true;
    state.current_player = 0; 

    // Card 418: PL!S-bp2-004-R (Kurosawa Dia)
    let dia_id = 418;
    state.core.players[0].stage[1] = dia_id;
    
    let member_id = 1; 
    state.core.players[0].deck.push(member_id);
    state.core.players[0].deck.push(member_id);

    // Force collection for yell context 
    state.core.players[0].yell_cards.push(member_id);

    // Directly execute trigger logic
    let ab = &db.get_member(dia_id).unwrap().abilities[0];
    let ctx = AbilityContext { 
        source_card_id: dia_id, 
        player_id: 0, 
        area_idx: 1, 
        ..Default::default() 
    };
    state.resolve_bytecode(&db, &ab.bytecode, &ctx);

    assert_eq!(state.core.players[0].cheer_mod_count, 1);
}

#[test]
fn test_selective_retrieval_natsumi() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = false;
    state.phase = Phase::Main;

    let natsumi_id = 537;
    state.core.players[0].hand.push(natsumi_id);
    for i in 0..11 { state.core.players[0].energy_zone.push(3000 + i as i32); }
    state.core.players[0].discard.push(100);

    state.current_player = 0;
    state.play_member(&db, 0, 1).expect("Should play Natsumi");
    state.process_trigger_queue(&db);

    assert_eq!(state.phase, Phase::Response);
    assert!(state.interaction_stack.last().unwrap().choice_type.contains("CHOOSE"));
}

#[test]
fn test_opponent_choice_penalty_maki() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.debug.debug_ignore_conditions = true; 
    state.phase = Phase::Main;
    
    let maki_id = 461;
    state.core.players[0].hand.push(maki_id);
    state.current_player = 0;
    state.play_member(&db, 0, 1).expect("Play Maki");
    state.process_trigger_queue(&db);
    
    assert_eq!(state.phase, Phase::Response);
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, "OPPONENT_CHOOSE");
}

#[test]
fn test_area_rotation_mei() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.debug.debug_ignore_conditions = true;
    state.phase = Phase::Main;

    let mei_id = 590;
    state.core.players[0].stage[0] = 10;
    state.core.players[0].stage[1] = 20;
    state.core.players[0].stage[2] = 30;

    state.core.players[0].hand.push(mei_id);
    state.current_player = 0;
    state.play_member(&db, 0, 0).expect("Play Mei");
    state.process_trigger_queue(&db);

    assert_eq!(state.core.players[0].stage[1], mei_id);
}

#[test]
fn test_heart_transformation_kanan_via_reduction() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.debug.debug_ignore_conditions = true;
    state.phase = Phase::Main;
    state.current_player = 0;

    // Manually execute O_REDUCE_HEART_REQ (48) for Red (1)
    let bc = vec![48, 1, 0, 1, O_RETURN, 0, 0, 0];
    let ctx = AbilityContext { player_id: 0, ..Default::default() };
    state.resolve_bytecode(&db, &bc, &ctx);

    assert!(state.core.players[0].heart_req_reductions.get_color_count(1) == 1);
}

#[test]
fn test_selective_reveal_kanon() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.debug.debug_ignore_conditions = true;
    state.phase = Phase::Main;
    state.current_player = 0;

    let kanon_id = 588;
    state.core.players[0].hand.push(kanon_id);
    
    let ab = &db.get_member(kanon_id).unwrap().abilities[0];
    let ctx = AbilityContext { source_card_id: kanon_id, player_id: 0, area_idx: 1, ..Default::default() };
    state.resolve_bytecode(&db, &ab.bytecode, &ctx);

    assert_eq!(state.phase, Phase::Response);
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, "SELECT_MODE");
}
