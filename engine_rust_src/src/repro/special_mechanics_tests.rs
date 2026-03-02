#[allow(unused_imports)]
use crate::core::logic::*;
use crate::test_helpers::{load_real_db, TestUtils};

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
    state.resolve_bytecode_cref(&db, &ab.bytecode, &ctx);

    assert_eq!(state.core.players[0].cheer_mod_count, 1);
}

#[test]
fn test_selective_retrieval_natsumi() {
    let db = load_real_db();
    let mut state = GameState::default();
    state.ui.silent = false;
    state.phase = Phase::Main;

    // Note: ID 537 is "Onitsuka Fuyumari" (Fuyu), but the test is named "Natsumi" 
    // likely due to the name being "Onitsuka". Fuyu is Natsumi's sister.
    // Logic ID 537 has cost 13.
    let natsumi_id = 537; 
    state.core.players[0].hand.push(natsumi_id);
    
    // Provide 13 energy (Cost of card 537)
    for i in 0..13 { state.core.players[0].energy_zone.push(3000 + i as i32); }
    
    // Card 537 Ability: SELECT_CARDS(2) {FROM="DISCARD", TYPE_LIVE, UNIQUE_NAMES}
    // We need 2 Live cards with different names in discard.
    // ID 6: "愛♡スクリ～ム！" (Live)
    // ID 642: "Live with a smile!" (Live)
    state.core.players[0].discard.push(6);
    state.core.players[0].discard.push(642);

    state.current_player = 0;
    state.play_member(&db, 0, 1).expect("Should play card 537");
    state.process_trigger_queue(&db);

    // Should be in Response phase for opponent to choose one of the 2 cards
    assert_eq!(state.phase, Phase::Response);
    let interaction = state.interaction_stack.last().unwrap();
    assert!(interaction.choice_type.contains("CHOOSE"));
    assert_eq!(state.core.players[0].looked_cards.len(), 2);
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
    crate::test_helpers::generate_card_report(mei_id);
    state.core.players[0].stage[0] = 10;
    state.core.players[0].stage[1] = 20;
    state.core.players[0].stage[2] = 30;

    state.core.players[0].hand.push(mei_id);
    state.current_player = 0;
    println!("--- Playing Mei ({}) ---", mei_id);
    state.play_member(&db, 0, 0).expect("Play Mei");
    state.process_trigger_queue(&db);
    state.dump_verbose();

    // After playing Mei (590) on Left(0), board is [590, 20, 30]
    // Rotation logic: Center(20) -> Left(0), Left(590) -> Right(2), Right(30) -> Center(1)
    // Expected new board: [20, 30, 590]
    assert_eq!(state.core.players[0].stage[0], 20);
    assert_eq!(state.core.players[0].stage[1], 30);
    assert_eq!(state.core.players[0].stage[2], mei_id);
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
    state.resolve_bytecode_cref(&db, &bc, &ctx);

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
    crate::test_helpers::generate_card_report(kanon_id);
    state.core.players[0].hand.push(kanon_id);

    let ab = &db.get_member(kanon_id).unwrap().abilities[0];
    let ctx = AbilityContext { source_card_id: kanon_id, player_id: 0, area_idx: 1, ..Default::default() };
    println!("--- Testing Kanon ({}) ---", kanon_id);
    state.resolve_bytecode_cref(&db, &ab.bytecode, &ctx);
    state.dump_verbose();

    assert_eq!(state.phase, Phase::Response);
    assert_eq!(state.interaction_stack.last().unwrap().choice_type, "SELECT_MODE");
}
