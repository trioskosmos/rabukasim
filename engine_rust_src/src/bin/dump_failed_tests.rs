use std::fs::File;
use std::io::Write;
use engine_rust::core::logic::{GameState, CardDatabase, AbilityContext};
use smallvec::smallvec;

fn main() {
    let mut states = vec![];

    // 1. verify_buff_logic
    let mut state1 = GameState::default();
    state1.ui.silent = true;
    state1.core.players[0].stage[0] = 120;
    state1.core.players[0].success_lives = smallvec![6, 7];
    states.push(("verify_buff_logic", state1));

    // 2. test_conditions_group_cd_context_input
    let mut state2 = GameState::default();
    state2.core.players[0].success_lives = smallvec![10];
    state2.core.players[0].score = 5;
    states.push(("test_group_cd", state2));

    // 3. test_score_compare
    let mut state3 = GameState::default();
    state3.core.players[0].score = 10;
    state3.core.players[1].score = 5;
    states.push(("test_score_compare", state3));

    // Dump to JSON
    for (name, state) in states {
        let json = serde_json::to_string_pretty(&state).unwrap();
        let filename = format!("../{}_raw.json", name);
        let mut file = File::create(&filename).unwrap();
        file.write_all(json.as_bytes()).unwrap();
        println!("Exported {}", filename);
    }
}
