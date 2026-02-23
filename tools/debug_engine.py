
import os
import sys
import json

# Add project root to path
sys.path.append(os.getcwd())

import engine_rust
print(f"Path: {engine_rust.__file__}")

from engine_rust import PyGameState, PyCardDatabase

def test_log_grouping():
    db_json = json.dumps({"members": {}, "lives": {}})
    db = PyCardDatabase(db_json)
    state = PyGameState(db)
    
    print("\n--- Available methods ---")
    methods = [m for m in dir(state) if not m.startswith('_')]
    print(methods)
    
    if hasattr(state, 'generate_execution_id'):
        print("Found generate_execution_id")
        state.generate_execution_id()
    else:
        print("MISSING generate_execution_id")
        # Try to find it in dir
        if 'generate_execution_id' in methods:
             print("It is in dir() but not hasattr()?!")
             # Try calling it anyway
             func = getattr(state, 'generate_execution_id')
             func()

    exec_id = state.current_execution_id
    print(f"Current Execution ID: {exec_id}")
    
    state.log("Test log entry")
    print(f"Rule log: {state.rule_log}")

if __name__ == "__main__":
    test_log_grouping()
