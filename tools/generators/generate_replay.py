import json
import os
import sys
import time

# Add parent path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from headless_runner import AbilityFocusAgent, RandomAgent


def generate():
    print("Initializing Game for Replay...")
    server.init_game(
        deck_type="normal"
    )  # Or 'ability_only' if supported by init_game args (need to check server.py init_game)
    # server.init_game takes deck_type.
    # NOTE: server.init_game logic for 'ability_only' is NOT seemingly implemented in server.py view I saw earlier?
    # I saw 'normal', 'easy'. 'starter'.
    # I might need to patch server.py or just use 'normal' for now.
    # The user wants to see the AI that fails/wins.
    # Let's check server.py init_game signature again properly or just default to normal.
    # Actually, headless_runner had the logic for 'ability_only'. Server might not.
    # I'll stick to 'normal' to avoid crash, or random if chaos is key.

    # Use AbilityFocusAgent for P0, Random for P1 (as per previous tests)
    p0_agent = AbilityFocusAgent()
    p1_agent = RandomAgent()

    replay_data = {"game_id": int(time.time()), "winner": None, "states": []}

    max_turns = 300

    print("Running Simulation...")
    while not server.game_state.is_terminal() and server.game_state.turn_number < max_turns:
        # Capture State
        # We need to capture state BEFORE action to show the board "as is"
        state_snapshot = server.serialize_state()

        # Decide Action
        pid = server.game_state.current_player
        if pid == 0:
            action = p0_agent.choose_action(server.game_state, 0)
        else:
            action = p1_agent.choose_action(server.game_state, 1)

        # Record action and agent names in snapshot
        state_snapshot["action_taken"] = int(action)
        state_snapshot["p0_agent"] = p0_agent.__class__.__name__
        state_snapshot["p1_agent"] = p1_agent.__class__.__name__

        # SANITIZE
        clean_snapshot = make_serializable(state_snapshot)
        replay_data["states"].append(clean_snapshot)

        print(f"Turn {server.game_state.turn_number} P{pid} Action {action}...", end="\r")

        # Apply Action
        server.game_state = server.game_state.step(action)

    # Capture Final State
    final_snapshot = server.serialize_state()
    final_snapshot["action_taken"] = -1
    replay_data["states"].append(make_serializable(final_snapshot))

    replay_data["winner"] = server.game_state.get_winner()

    out_file = "replays/ai_match.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(replay_data, f, ensure_ascii=False)  # minified to save space? or indented? UI might not care.

    print(f"\nMessage: Replay saved to {out_file}. Frame count: {len(replay_data['states'])}")


def make_serializable(obj):
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, list):
        return [make_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): make_serializable(v) for k, v in obj.items()}
    if hasattr(obj, "tolist"):  # NumPy arrays
        return obj.tolist()
    # Fallback for objects
    return str(obj)


if __name__ == "__main__":
    generate()
