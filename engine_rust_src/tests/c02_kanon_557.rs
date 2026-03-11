use engine_rust::core::enums::*;
use engine_rust::core::logic::CardDatabase;
use engine_rust::core::logic::GameState;
use engine_rust::core::logic::AbilityContext;
use std::sync::Arc;

#[test]
fn test_kanon_557_repro() {
    let mut db = CardDatabase::default();

    // Find Kanon 557 (PL!SP-bp4-001-R)
    let kanon_id = 557;
    let mut kanon = engine_rust::core::logic::MemberCard::default();
    kanon.card_id = kanon_id;
    kanon.groups = vec![3]; // Liella
    
    // Ability 1: ON_PLAY -> PLACE_ENERGY_WAIT(1)
    let _filter_attr = 209u64 | (3u64 << 5) | 16u64 | (112u64 << 32); // ALL_MEMBERS {GROUP_ID=3}
    let mut ab = engine_rust::core::logic::Ability::default();
    ab.trigger = engine_rust::core::enums::TriggerType::OnPlay;
    ab.bytecode = vec![
        209, 4, 112, 0, 48,
        213, 7, 0, 0, 48,
        23, 1, 0, 0, 134217732,
        1, 0, 0, 0, 0
    ];
    kanon.abilities.push(ab);
    db.members.insert(kanon_id, kanon);

    let mut state = GameState::default();
    let p1 = 0;

    // Fill energy deck with dummies
    for _ in 0..10 {
        state.core.players[p1].energy_deck.push(3000);
    }

    // Give player 8 energy (more than 7)
    for _ in 0..8 {
        state.core.players[p1].energy_zone.push(3000);
    }

    // Put a generic Liella member on stage to fulfill ALL_MEMBERS FILTER="GROUP_ID=3"
    let dummy_liella_id = 560; // Just another Liella member
    let mut liella = engine_rust::core::logic::MemberCard::default();
    liella.card_id = dummy_liella_id;
    liella.groups = vec![3]; // Liella
    db.members.insert(dummy_liella_id, liella);

    state.core.players[p1].stage[0] = kanon_id;
    state.core.players[p1].stage[1] = dummy_liella_id;

    state.core.current_player = p1 as u8;
    state.core.phase = Phase::Main;
    state.debug.debug_mode = true;

    let ctx = AbilityContext {
        source_card_id: kanon_id,
        player_id: p1 as u8,
        activator_id: p1 as u8,
        area_idx: 0,
        ..Default::default()
    };

    let bc = Arc::new(db.members[&kanon_id].abilities[0].bytecode.clone());
    state.resolve_bytecode(&db, bc, &ctx);

    // Run interpreter just enough to resolve the stack
    for _ in 0..2 {
        let _ = state.step(&db, 0);
    }

    assert_eq!(state.core.players[p1].energy_zone.len(), 9, "Kanon ON_PLAY should trigger at 8 energy!");
}
