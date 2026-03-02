import json
import sys
import os

def generate_rust_test(state_json_path, output_rs_path, test_name="test_repro_state"):
    """
    Generates a Rust test file that loads a serialized GameState from JSON.
    """
    abs_state_path = os.path.abspath(state_json_path).replace("\\", "/")

    script_content = f"""// Auto-generated RabukaSim Repro Script for Rust
use engine_rust::core::logic::{{GameState, CardDatabase}};
use engine_rust::core::logic::Phase;

#[test]
fn {test_name}() {{
    // 1. Load the pre-compiled card database
    let db_path = "../data/cards_compiled.json";
    let json_content = std::fs::read_to_string(db_path)
        .expect("Failed to read cards_compiled.json. Make sure you run this from engine_rust_src/");
    let db = CardDatabase::from_json(&json_content)
        .expect("Failed to parse CardDatabase from JSON");

    println!("DB Loaded. Members: {{}}, Lives: {{}}", db.members.len(), db.lives.len());

    // 2. Load the saved state JSON
    let state_path = "{abs_state_path}";
    let state_json = std::fs::read_to_string(state_path)
        .expect("Failed to read state dump file");

    // 3. Deserialize directly into GameState
    let mut state: GameState = serde_json::from_str(&state_json)
        .expect("Failed to deserialize GameState. Format mismatch?");

    println!("State successfully warped to Turn {{}}, Phase: {{:?}}", state.turn, state.phase);

    // 4. Inspect or Step
    // Example: Print legal actions
    // let actions = state.get_legal_actions(&db);
    // println!("Legal Actions: {{:?}}", actions);

    // Example: Step the game
    // let action_id = 0; // Replace with desired action, or PASS (0 normally)
    // state.step(&db, action_id).expect("Step failed");
    
    // Add your assertions here
    // assert_eq!(state.players[0].score, 100);
}}
"""
    
    with open(output_rs_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    print(f"Rust repro test generated: {output_rs_path}")
    print(f"Run it with: `cd engine_rust_src && cargo test {test_name} -- --nocapture`")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/create_rust_test.py <state.json> [output_repro.rs] [test_name]")
    else:
        state_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) > 2 else "engine_rust_src/tests/repro_generated.rs"
        t_name = sys.argv[3] if len(sys.argv) > 3 else "test_repro_state"
        generate_rust_test(state_path, out_path, t_name)
