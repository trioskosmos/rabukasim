use engine_rust::core::logic::CardDatabase;
use engine_rust::core::logic::GameState;
use engine_rust::core::logic::TriggerType;
use engine_rust::core::logic::AbilityContext;
use engine_rust::core::logic::MemberCard;
use engine_rust::core::logic::Ability;
use engine_rust::core::enums::*;
use std::sync::Arc;

#[test]
fn test_sumire_8752_repro() {
    let mut db = CardDatabase::default();
    
    let sumire_id = 8752;
    let cheap_liella_id = 557;

    // Create dummy Sumire
    let mut sumire = MemberCard::default();
    sumire.card_id = sumire_id;
    sumire.groups = vec![3];
    
    // Ability 1: DRAW(2); PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=3, COST_LE_4"}
    // Attribute calculation for "GROUP_ID=3, COST_LE_4, TARGET=SELF":
    // GROUP_ENABLE (bit 4) | (3 << 5) | TARGET=SELF (1) = 113
    // VALUE_ENABLE (bit 24) | (4 << 25) | LE (bit 30) | COST (bit 31) = 0xC9000000 (wait, 4<<25 is 0x08000000)
    // Actually 113 | 0xC9000000
    let filter_attr = 3372220416i64 | 113i64; // 0xC9000000 | 113

    let mut ab = Ability::default();
    ab.trigger = TriggerType::OnPlay;
    ab.bytecode = vec![
        10, 2, 0, 0, 0,       // DRAW(2)
        63, 1, (filter_attr & 0xFFFFFFFF) as i32, (filter_attr >> 32) as i32, 458756, // PLAY_MEMBER_FROM_DISCARD(1)
        1, 0, 0, 0, 0         // RETURN
    ];
    sumire.abilities.push(ab);
    db.members.insert(sumire_id, sumire);

    // Create dummy Liella member
    let mut liella = MemberCard::default();
    liella.card_id = cheap_liella_id;
    liella.groups = vec![3];
    liella.cost = 1;
    db.members.insert(cheap_liella_id, liella);

    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let p1 = 0;
    state.core.players[p1].stage[1] = sumire_id;
    state.core.players[p1].baton_touch_count = 2;
    state.core.players[p1].baton_source_slots.push(1); // Baton touched slot 1
    state.core.players[p1].discard.push(cheap_liella_id);
    for i in 0..10 { state.core.players[p1].deck.push(100 + i); }

    let mut ctx = AbilityContext {
        source_card_id: sumire_id,
        player_id: p1 as u8,
        activator_id: p1 as u8,
        area_idx: 1,
        ..Default::default()
    };

    println!("--- Running Bytecode ---");
    let bc = Arc::new(db.members[&sumire_id].abilities[0].bytecode.clone());
    state.resolve_bytecode(&db, bc, &ctx);
    
    println!("Hand size after DRAW: {}", state.core.players[p1].hand.len());
    println!("Interaction stack size: {}", state.core.interaction_stack.len());
    
    if let Some(pending) = state.core.interaction_stack.last() {
        println!("Opcode: {}, ChoiceType: {:?}", pending.effect_opcode, pending.choice_type);
        assert_eq!(pending.effect_opcode, 63);
        assert_eq!(pending.choice_type, ChoiceType::SelectStageEmptyBaton);
    } else {
        panic!("Should have a pending interaction for PLAY_MEMBER_FROM_DISCARD");
    }
}
