use engine_rust::core::logic::*;
use std::sync::Arc;

#[test]
fn test_sumire_8752_repro() {
    let mut db = CardDatabase::default();
    
    let sumire_id = 8752;
    let cheap_liella_id = 557;

    let mut sumire = MemberCard::default();
    sumire.card_id = sumire_id;
    sumire.groups = vec![3];
    
    // Attribute: GROUP=3 (112) | TARGET=SELF (1) | VALUE_ENABLE (0x01000000) | 4 (0x08000000) | LE (0x40000000) | COST (0x80000000)
    // 0x80000000 | 0x40000000 | 0x08000000 | 0x01000000 | 113 = 0xC9000071
    let filter_attr: u64 = 0xC9000071;

    let mut ab = Ability::default();
    ab.trigger = TriggerType::OnPlay;
    ab.bytecode = vec![
        O_DRAW as i32, 2, 0, 0, 0,
        O_PLAY_MEMBER_FROM_DISCARD as i32, 1, (filter_attr & 0xFFFFFFFF) as i32, (filter_attr >> 32) as i32, (FLAG_EMPTY_SLOT_ONLY as i32) | 4, // s = FLAG_EMPTY_SLOT_ONLY | 4 (Stage)
        O_RETURN as i32, 0, 0, 0, 0
    ];
    sumire.abilities.push(ab);
    db.members.insert(sumire_id, sumire);

    let mut liella = MemberCard::default();
    liella.card_id = cheap_liella_id;
    liella.groups = vec![3];
    liella.cost = 1;
    db.members.insert(cheap_liella_id, liella);

    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let p1 = 0;
    state.players[p1].stage[1] = sumire_id;
    state.players[p1].baton_touch_count = 2;
    state.players[p1].discard.push(cheap_liella_id);
    for i in 0..10 { state.players[p1].deck.push(100 + i); }

    let ctx = AbilityContext {
        source_card_id: sumire_id,
        player_id: p1 as u8,
        activator_id: p1 as u8,
        area_idx: 1,
        ..Default::default()
    };

    println!("--- Running Bytecode ---");
    let bc = Arc::new(db.members[&sumire_id].abilities[0].bytecode.clone());
    state.resolve_bytecode(&db, bc, &ctx);
    
    println!("Hand size after DRAW: {}", state.players[p1].hand.len());
    println!("Interaction stack size: {}", state.interaction_stack.len());
    
    if let Some(pending) = state.interaction_stack.last() {
        println!("Opcode: {}, ChoiceType: {:?}", pending.effect_opcode, pending.choice_type);
        assert_eq!(pending.effect_opcode, O_PLAY_MEMBER_FROM_DISCARD as i32);
        assert_eq!(pending.choice_type, ChoiceType::SelectDiscardPlay);
    } else {
        panic!("Should have a pending interaction for PLAY_MEMBER_FROM_DISCARD");
    }

    // Step 2: Choose the card from discard.
    // In a real game, this would be handled by handle_response which pops the interaction stack.
    state.interaction_stack.pop();
    
    let mut resume_ctx = ctx.clone();
    resume_ctx.choice_index = 0; // Choose first matched card
    resume_ctx.program_counter = 5; // Pointing to O_PLAY_MEMBER_FROM_DISCARD
    
    println!("--- Resuming for Slot Selection ---");
    let bc2 = Arc::new(db.members[&sumire_id].abilities[0].bytecode.clone());
    state.resolve_bytecode(&db, bc2, &resume_ctx);

    println!("Interaction stack size after resume: {}", state.interaction_stack.len());
    if let Some(pending) = state.interaction_stack.last() {
        println!("New Opcode: {}, ChoiceType: {:?}", pending.effect_opcode, pending.choice_type);
        assert_eq!(pending.choice_type, ChoiceType::SelectStageEmpty);
        // CRITICAL: Ensure choice_index was reset to -1 so SelectStage interaction is created
        assert_eq!(pending.ctx.choice_index, -1);
    } else {
        panic!("Should have a second pending interaction for slot selection");
    }
}
