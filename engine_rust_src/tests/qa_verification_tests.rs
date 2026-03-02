#[allow(unused_imports)]
use engine_rust::core::logic::{ActionFactory, CardDatabase, GameState, PendingInteraction, Phase};

#[test]
fn test_q103_dynamic_condition_resolution() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let mut _db = CardDatabase::from_json(&json_content).unwrap();
}
