use engine_rust::core::logic::{GameState, CardDatabase};
use engine_rust::core::logic::filter::CardFilter;

fn main() {
    let json_content = std::fs::read_to_string("data/cards_compiled.json").expect("Failed to read");
    let db = CardDatabase::from_json(&json_content).unwrap();
    let state = GameState::default();

    let a = 1157627908u64;
    let filter = CardFilter::from_attr(a as i64);
    println!("Parsed Filter: {:#?}", filter);

    let kota_id = 726;
    let m = db.get_member(kota_id).unwrap();
    println!("Kota Cost: {}", m.cost);

    let matches = state.card_matches_filter(&db, kota_id, a);
    println!("Kota matches filter? {}", matches);
}
