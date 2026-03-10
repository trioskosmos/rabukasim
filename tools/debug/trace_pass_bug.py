import os
import sys

# Core path setup
project_root = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy"
if project_root not in sys.path:
    sys.path.append(project_root)
    sys.path.append(os.path.join(project_root, "engine_rust_src", "target", "release"))

from engine_rust import EvalMode, PyCardDatabase, PyGameState, SearchHorizon


def test_rps_loop():
    # Load DB
    with open(os.path.join(project_root, "data", "cards_compiled.json"), "r", encoding="utf-8") as f:
        cards_json = f.read()
    db = PyCardDatabase(cards_json)

    # Init state
    state = PyGameState(db)
    state.initialize_game(
        [1000] * 30,
        [1000] * 30,  # Decks
        [1000] * 10,
        [1000] * 10,  # Energy
        [10000] * 3,
        [10000] * 3,  # Lives
    )

    print(f"Initial Phase: {state.phase}")

    moves = 0
    max_moves = 100

    # Track actions to detect loops
    action_history = []

    # Enums
    eval_mode = EvalMode.Blind
    horizon = SearchHorizon.GameEnd()

    while state.phase != 9 and moves < max_moves:  # 9 is Terminal
        current_phase = state.phase
        acting_player = state.acting_player

        # MCTS suggestions for current state
        # In RPS phase, we want to see if it still loops
        try:
            suggestions = state.get_mcts_suggestions(100, 0.1, horizon, eval_mode)
            if not suggestions:
                print(f"Move {moves}: No suggestions! Breaking.")
                break

            # Pick best action (deterministic for testing)
            action = suggestions[0][0]
            score = suggestions[0][1]
            visits = suggestions[0][2]
        except Exception as e:
            print(f"Error at move {moves}: {e}")
            break

        action_history.append(action)

        # Log if it's RPS or if phase changes
        if current_phase == -3:
            print(f"Move {moves} [P{acting_player} RPS]: Action {action} (Score: {score:.4f}, Visits: {visits})")

        state.step(action)
        state.auto_step(db)

        moves += 1

        if state.phase != current_phase:
            print(f"Phase changed to {state.phase} at move {moves}")
            if state.phase != -3:  # If we exited RPS
                break

    if state.phase == -3:
        print("FAILED: Still in RPS phase after 100 moves.")
    else:
        print(f"SUCCESS: Exited RPS phase to {state.phase} in {moves} moves.")

    # Check if we saw draws
    log = state.rule_log
    draw_count = sum(1 for line in log if "Draw" in line)
    print(f"Total RPS draws encountered: {draw_count}")
    for line in log:
        if "Draw" in line or "Maximum RPS draws" in line:
            print(f"Log: {line}")


if __name__ == "__main__":
    test_rps_loop()
