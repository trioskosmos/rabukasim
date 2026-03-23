use engine_rust::core::logic::{CardDatabase, GameState};
use std::fs;

fn main() {
    println!("Turn Sequencer Diagnostic Tool");
    let candidates = ["data/cards_vanilla.json", "../data/cards_vanilla.json"];
    let mut db_opt = None;
    for path in &candidates {
        if let Ok(json) = fs::read_to_string(path) {
            if let Ok(mut db) = CardDatabase::from_json(&json) {
                db.is_vanilla = true;
                db_opt = Some(db);
                break;
            }
        }
    }

    if let Some(db) = db_opt {
        println!("Loaded DB successfully");
        let mut state = GameState::default();
        let members: Vec<i32> = db.members.keys().take(48).cloned().collect();
        let lives: Vec<i32> = db.lives.keys().take(12).cloned().collect();
        let energy: Vec<i32> = db.energy_db.keys().take(12).cloned().collect();
        state.initialize_game(
            members.clone(),
            members,
            energy.clone(),
            energy,
            lives.clone(),
            lives,
        );
        println!("Game initialized. Turn: {}", state.turn);
    } else {
        println!("Could not load database");
    }
}
