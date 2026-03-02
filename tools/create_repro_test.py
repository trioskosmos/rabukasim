import json
import sys
import os

def generate_repro_script(state_json_path, output_py_path):
    """
    Generates a Python reproduction script using the Rust engine bindings.
    """
    # Use absolute path for state file in the generated script
    abs_state_path = os.path.abspath(state_json_path).replace("\\", "/")

    script_content = f"""# Auto-generated RabukaSim Repro Script
import engine_rust
import json
import os

def run_repro():
    # 1. Load the pre-compiled card database
    # Assuming standard path relative to project root
    db_path = "data/cards_compiled.bin"
    if not os.path.exists(db_path):
        db_path = "../data/cards_compiled.bin"
        
    print(f"Loading DB from {{db_path}}...")
    with open(db_path, "rb") as f:
        db = engine_rust.CardDatabase.from_binary(f.read())

    # 2. Load the saved state
    state_path = "{abs_state_path}"
    print(f"Loading State from {{state_path}}...")
    with open(state_path, "r", encoding="utf-8") as f:
        state_json = f.read()

    # 3. Create game state and Apply the warp
    gs = engine_rust.GameState()
    try:
        gs.apply_state_json(state_json)
        print("Successfully warped game state.")
    except Exception as e:
        print(f"Failed to apply state: {{e}}")
        return

    # 4. Inspect or Step
    print(f"Current Turn: {{gs.turn}}")
    print(f"Active Player: {{gs.current_player}}")
    # print(f"Legal Actions: {{gs.get_legal_actions(db)}}")
    
    # gs.step(db, action_id) # Example: step the game

if __name__ == "__main__":
    run_repro()
"""
    
    with open(output_py_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    print(f"Repro script generated: {output_py_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/create_repro_test.py <state.json> [output_repro.py]")
    else:
        state_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) > 2 else "repro_test.py"
        generate_repro_script(state_path, out_path)
