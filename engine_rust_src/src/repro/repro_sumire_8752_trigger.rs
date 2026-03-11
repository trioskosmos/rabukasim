use engine_rust::core::logic::GameState;

#[test]
fn test_sumire_8752_trigger_repro() {
    let db = engine_rust::test_helpers::load_real_db();
    
    // Card 8752: PL!SP-bp4-004-P＋
    let sumire_id = 8752;
    let card = db.get_member(sumire_id).expect("Sumire 8752 not in DB");
    
    // Use Liella! members (GROUP_ID=3) for baton sources
    let kanon_id = *db
        .card_no_to_id
        .get("PL!SP-bp4-001-P")
        .expect("Kanon not found");
    
    let mut state = GameState::default();
    state.ui.silent = false;
    let p1 = 0;
    
    // Setup state for double baton
    // Played Sumire to Center (slot 1) replacing something
    state.players[p1].stage[1] = sumire_id;
    state.players[p1].baton_touch_count = 2; // Double baton
    state.players[p1].baton_source_ids.push(kanon_id as i32);
    state.players[p1].baton_source_ids.push(kanon_id as i32); // Simulating 2 Liella sources
    state.prev_card_id = kanon_id as i32; // Primary baton source (Liella)
    state.players[p1].play_count_this_turn = 1; // Just played a card
    
    let ctx = engine_rust::core::logic::AbilityContext {
        player_id: p1 as u8,
        source_card_id: sumire_id,
        area_idx: 1, // Center
        ..Default::default()
    };
    
    // Ability 1 is the OnPlay one
    let ab = &card.abilities[1];
    println!("Ability 1 Pseudocode: {}", ab.pseudocode);
    println!("Ability 1 Bytecode: {:?}", ab.bytecode);
    
    // Manual step through triggers/conditions to see where it fails
    // In real execution, check_condition is called
    let mut cond_results = Vec::new();
    for cond in &ab.conditions {
        let res = engine_rust::core::logic::interpreter::conditions::check_condition(
            &state, &db, p1, cond, &ctx, 0
        );
        println!("Condition {:?} Result: {}", cond.condition_type, res);
        cond_results.push(res);
    }
    
    assert!(cond_results.iter().all(|&r| r), "One or more conditions failed!");
}
