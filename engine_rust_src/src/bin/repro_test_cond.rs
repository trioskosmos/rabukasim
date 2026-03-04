use engine_rust::core::logic::{CardDatabase, GameState};

fn main() {
    let json_content =
        std::fs::read_to_string("../data/cards_compiled.json").expect("Failed to read");
    let db = CardDatabase::from_json(&json_content).unwrap();
    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let p1 = 0;
    let catchu_live_id = 605;

    state.players[p1].stage[0] = 373;
    state.players[p1].stage[1] = 374;
    state.players[p1].score = 0;

    for _ in 0..10 {
        state.players[p1].energy_zone.push(100);
    }
    state.players[p1].tapped_energy_mask = 0b111_1111; // 7 bits

    let ability = db.get_live(catchu_live_id).unwrap().abilities[0].clone();

    println!(
        "Initial tapped mask: {}",
        state.players[p1].tapped_energy_mask
    );

    let mut ctx1 = engine_rust::core::logic::AbilityContext {
        player_id: p1 as u8,
        source_card_id: catchu_live_id,
        ..Default::default()
    };
    engine_rust::core::logic::interpreter::resolve_bytecode(
        &mut state,
        &db,
        std::sync::Arc::new(ability.bytecode.clone()),
        &mut ctx1,
    );

    println!(
        "After 1st execution tapped mask: {}",
        state.players[p1].tapped_energy_mask
    );
    println!("Score after 1st: {}", state.players[p1].score);

    let mut ctx2 = engine_rust::core::logic::AbilityContext {
        player_id: p1 as u8,
        source_card_id: catchu_live_id,
        ..Default::default()
    };
    engine_rust::core::logic::interpreter::resolve_bytecode(
        &mut state,
        &db,
        std::sync::Arc::new(ability.bytecode.clone()),
        &mut ctx2,
    );

    println!(
        "After 2nd execution tapped mask: {}",
        state.players[p1].tapped_energy_mask
    );
    println!("Score after 2nd: {}", state.players[p1].score);
}
