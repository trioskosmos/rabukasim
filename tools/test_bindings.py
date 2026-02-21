import json

import engine_rust

data = {"member_db": {}, "live_db": {}}
db = engine_rust.PyCardDatabase(json.dumps(data))
state = engine_rust.PyGameState(db)

print(f"engine_rust members: {dir(engine_rust)}")
print(f"HeuristicConfig type: {type(engine_rust.HeuristicConfig)}")

print(f"PyGameState members: {dir(state)}")
try:
    print(f"get_greedy_evaluations doc: {state.get_greedy_evaluations.__doc__}")
except Exception as e:
    print(f"Failed to get doc: {e}")

try:
    cfg = engine_rust.HeuristicConfig()
    print(f"Successfully created HeuristicConfig: {cfg}")
except Exception as e:
    print(f"Failed to create HeuristicConfig: {e}")

try:
    evals = state.get_greedy_evaluations(db, 0, config=None)
    print("Successfully called get_greedy_evaluations with keyword config")
except Exception as e:
    print(f"Failed to call with keyword config: {e}")

try:
    evals = state.get_greedy_evaluations(db, 0, None)
    print("Successfully called get_greedy_evaluations positionally")
except Exception as e:
    print(f"Failed to call positionally: {e}")
