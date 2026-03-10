import json
import sys
import time
from pathlib import Path

import engine_rust

# Add project root for engine imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def mcts_stability_audit():
    print("Starting MCTS Stability Audit...")

    # 1. Setup Environment
    db_path = "data/cards_compiled.json"
    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)
    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))

    # Load 103/2001 fallback decks for consistent testing
    tournament_decks = [{"name": "Standard_Test", "members": [103] * 48, "lives": [2001] * 12, "energy": [1001] * 12}]

    d0 = tournament_decks[0]
    p0_main = d0["members"] + d0["lives"]
    p1_main = d0["members"] + d0["lives"]

    state = engine_rust.PyGameState(db_engine)
    state.initialize_game(p0_main, p1_main, d0["energy"], d0["energy"], [], [])
    state.silent = True

    # 2. Play until first live success
    print("Playing until first Live Success...")
    while not state.is_terminal():
        p0 = state.get_player(0)
        p1 = state.get_player(1)
        if len(p0.success_lives) > 0 or len(p1.success_lives) > 0:
            print(f"Goal Reached! Player 0: {len(p0.success_lives)}, Player 1: {len(p1.success_lives)}")
            break

        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        # Fast play using 16 sims for speed
        suggestions = state.get_mcts_suggestions(
            16, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal
        )
        action = suggestions[0][0] if suggestions else legal_ids[0]
        state.step(action)
        state.auto_step(db_engine)

    # 3. Time-Slicing MCTS Audit
    print("\n--- Starting 10s MCTS Choice Audit ---")
    current_best_action = -1
    best_action_label = ""
    start_time = time.time()
    audit_log = []

    # We will run MCTS with increasing simulation counts to simulate "thinking" over 10 seconds
    # and observe how the consensus changes.
    total_sims = 0
    step_size = 100

    while time.time() - start_time < 10:
        # Run a chunk of simulations
        # Note: We use get_mcts_suggestions with a timeout/sim limit
        # To truly see it "change", we need to see the result of the TOTAL accumulated tree
        # Since get_mcts_suggestions creates a fresh tree, we'll run it with increasing volume
        total_sims += step_size

        suggestions = state.get_mcts_suggestions(
            total_sims, 0.0, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.Normal
        )
        if not suggestions:
            continue

        top_action = suggestions[0][0]
        top_score = suggestions[0][1]
        top_visits = suggestions[0][2]

        if top_action != current_best_action:
            new_label = state.get_action_label(top_action)
            elapsed = time.time() - start_time
            change_msg = f"[{elapsed:.2f}s] BEST ACTION CHANGED: {best_action_label} -> {new_label} (Sims: {total_sims}, Score: {top_score:.3f})"
            print(change_msg)
            audit_log.append(change_msg)

            current_best_action = top_action
            best_action_label = new_label

        # Dynamically increase step size to cover more ground as the 10s window progresses
        step_size = int(step_size * 1.2)

    print("\nAudit Complete.")
    with open("mcts_audit_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(audit_log))


if __name__ == "__main__":
    mcts_stability_audit()
