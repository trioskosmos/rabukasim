import json
import sys
from pathlib import Path

import numpy as np

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

# Wait, we need the exact paths from overnight_pure_zero for engine
import engine_rust

from alphazero.alphanet import build_action_decomposition_table
from alphazero.training.overnight_pure_zero import load_tournament_decks


def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    db_path = root_dir / "data" / "cards_compiled.json"

    with open(db_path, "r", encoding="utf-8") as f:
        full_db = json.load(f)

    db_engine = engine_rust.PyCardDatabase(json.dumps(full_db))
    decks = load_tournament_decks(full_db)

    if len(decks) < 2:
        print("Not enough decks.")
        return

    print(f"Loaded {len(decks)} decks format.")

    type_table, sub_table = build_action_decomposition_table()

    # Track sub_idx > 100
    subidx_violations = set()
    total_actions_seen = set()

    state = engine_rust.PyGameState(db_engine)

    d0 = decks[0]
    d1 = decks[1]

    state.initialize_game(d0["members"] + d0["lives"], d1["members"] + d1["lives"], d0["energy"], d1["energy"], [], [])
    state.silent = True

    turn_limit = 50
    print("Starting test game...")

    while not state.is_terminal() and state.turn < turn_limit:
        legal_ids = state.get_legal_action_ids()
        if not legal_ids:
            break

        for aid in legal_ids:
            total_actions_seen.add(aid)
            sub_idx = sub_table[aid]
            if sub_idx >= 100:
                subidx_violations.add((aid, sub_idx))

        suggestions = state.get_mcts_suggestions(
            50, 1.41, engine_rust.SearchHorizon.GameEnd(), engine_rust.EvalMode.TerminalOnly
        )

        acts = [s[0] for s in suggestions]
        vts = [s[2] for s in suggestions]

        if not acts:
            action = legal_ids[0]
        else:
            action = acts[np.argmax(vts)]

        state.step(action)
        state.auto_step(db_engine)
        print(f"Turn {state.turn} - Step {(state.get_player(0).score, state.get_player(1).score)} - Action {action}")

    print("\n--- RESULTS ---")
    print(f"Game finished at turn {state.turn}")
    print(f"Total unique actions seen: {len(total_actions_seen)}")
    if subidx_violations:
        print(f"WARNING: FOUND {len(subidx_violations)} ACTIONS WITH SUB_IDX >= 100:")
        # Sort by action ID
        viols = sorted(list(subidx_violations))
        for aid, sub in viols:
            print(f"Action ID: {aid} -> sub-index {sub}")
    else:
        print("ALL CLEAR: No legal actions exceeded sub-index 99!")


if __name__ == "__main__":
    main()
