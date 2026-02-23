
import os
import sys
import json

# Add project root to path
sys.path.append(os.getcwd())

try:
    from engine_rust import PyGameState, PyCardDatabase
    print("Successfully imported engine_rust")
except ImportError:
    print("Could not import engine_rust. Ensure it is built and renamed to .pyd")
    sys.exit(1)

def test_log_grouping():
    # PyCardDatabase needs a JSON string
    db_json = json.dumps({"members": {}, "lives": {}})
    db = PyCardDatabase(db_json)
    state = PyGameState(db)
    
    print("\n--- Simulating Ability Activation ---")
    
    # 1. Start execution context
    state.generate_execution_id()
    exec_id = state.get_current_execution_id()
    print(f"Generated Execution ID: {exec_id}")
    
    # 2. Log several events
    state.log("Triggering [PL!HS-PR-021-PR] Anyoji Hime")
    state.log("Looked at cards and chose 1")
    state.log("Draw 1 card(s)")
    state.log("Moved 2 card(s) from Hand to Discard")
    
    # 3. Clear context
    state.clear_execution_id()
    
    # 4. Check rule log
    print("\n--- Resulting Rule Logs in Engine ---")
    for entry in state.rule_log:
        print(f"Raw Log: {entry}")

if __name__ == "__main__":
    test_log_grouping()
