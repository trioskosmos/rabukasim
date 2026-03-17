import time

import engine_rust

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    db_json = f.read()
db = engine_rust.PyCardDatabase(db_json)

g = engine_rust.PyGameState(db)
g.silent = True
deck = [0] * 40 + [1000] * 10
g.initialize_game(deck, deck, [200] * 12, [200] * 12, [1000] * 3, [1000] * 3)

ITERATIONS = 50000

# 1. Measure Copy
start = time.time()
for _ in range(ITERATIONS):
    _ = g.copy()
end = time.time()
print(f"RESULT_COPY: {ITERATIONS / (end - start):.0f} ops/s ({(end - start) * 1000000 / ITERATIONS:.2f} us/op)")

# 2. Measure Legal Actions (Sparse/IDs)
start = time.time()
for _ in range(ITERATIONS):
    _ = g.get_legal_action_ids()
end = time.time()
print(f"RESULT_LEGAL: {ITERATIONS / (end - start):.0f} ops/s ({(end - start) * 1000000 / ITERATIONS:.2f} us/op)")

# 3. Measure Step (Simple Action)
# We need a legal action first.
# This assumes we are in Mulligan or Main phase where at least one action (e.g. End Turn) is valid.
# Just use step_opponent_random for a single step if possible, or find a valid action.
# For benchmark, let's just use `get_legal_action_ids` and pick the first one.
legal_actions = g.get_legal_action_ids()
if legal_actions:
    action = legal_actions[0]
    # We clone g to not mess it up for loop
    g_start = g.copy()

    start = time.time()
    # We can't easily reuse the same state for 100k steps because game ends.
    # So we copy then step. This measures Copy + Step.
    # To isolate Step, we subtract Copy time?
    # Actually, MCTS reuses `reusable_state`, so it does `copy_from` then `step`.
    # Let's measure `copy` + `step` loop.

    temp_g = g_start.copy()
    count = 0
    t0 = time.time()
    for _ in range(ITERATIONS):
        temp_g = g_start.copy()  # Reset
        temp_g.step(action)
    t1 = time.time()

    total_time = t1 - t0
    ops_sec = ITERATIONS / total_time
    print(f"RESULT_COPY_STEP: {ops_sec:.0f} ops/s ({total_time * 1000000 / ITERATIONS:.2f} us/op)")
else:
    print("No legal actions to test Step")

# 4. Measure Observation (Encoding)
start = time.time()
for _ in range(ITERATIONS):
    _ = g.get_observation()
end = time.time()
print(f"RESULT_OBS: {ITERATIONS / (end - start):.0f} ops/s ({(end - start) * 1000000 / ITERATIONS:.2f} us/op)")
