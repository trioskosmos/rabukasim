import json
import os
import sys

import engine_rust

# Ensure project root is in path
sys.path.append(os.getcwd())


def create_mock_db():
    # Minimal DB with some test cards
    member_db = {
        "1": {
            "card_id": 1,
            "card_no": "1",
            "name": "Basic Member",
            "cost": 1,
            "hearts": [1, 0, 0, 0, 0, 0, 0],
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
            "blades": 1,
            "groups": [],
            "units": [],
            "abilities": [],
            "volume_icons": 1,
            "draw_icons": 0,
            "char_id": 1,
        },
        "2": {
            "card_id": 2,
            "card_no": "2",
            "name": "Searcher",
            "cost": 2,
            "hearts": [0, 1, 0, 0, 0, 0, 0],
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
            "blades": 1,
            "groups": [],
            "units": [],
            "abilities": [{"trigger": 0, "bytecode": [22, 0, 0, 0]}],
            "volume_icons": 1,
            "draw_icons": 0,
            "char_id": 2,
        },
        "3": {
            "card_id": 3,
            "card_no": "3",
            "name": "Drawer",
            "cost": 3,
            "hearts": [0, 0, 1, 0, 0, 0, 0],
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
            "blades": 1,
            "groups": [],
            "units": [],
            "abilities": [{"trigger": 0, "bytecode": [10, 2, 0, 0]}],
            "volume_icons": 1,
            "draw_icons": 0,
            "char_id": 3,
        },
        "4": {
            "card_id": 4,
            "card_no": "4",
            "name": "Big Member",
            "cost": 5,
            "hearts": [0, 0, 0, 1, 0, 0, 0],
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
            "blades": 2,
            "groups": [],
            "units": [],
            "abilities": [],
            "volume_icons": 2,
            "draw_icons": 0,
            "char_id": 4,
        },
    }
    live_db = {
        "10001": {
            "card_id": 10001,
            "card_no": "L1",
            "name": "Easy Live",
            "score": 1,
            "required_hearts": [1, 0, 0, 0, 0, 0, 0],
            "abilities": [],
            "groups": [],
            "units": [],
            "volume_icons": 0,
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
        },
        "10002": {
            "card_id": 10002,
            "card_no": "L2",
            "name": "Hard Live",
            "score": 2,
            "required_hearts": [5, 5, 5, 0, 0, 0, 0],
            "abilities": [],
            "groups": [],
            "units": [],
            "volume_icons": 0,
            "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
        },
    }

    json_str = json.dumps({"member_db": member_db, "live_db": live_db})
    return engine_rust.PyCardDatabase(json_str)


def demonstrate():
    db = create_mock_db()
    game = engine_rust.PyGameState(db)

    # Setup Deck for P0
    p0_deck = [1, 1, 1, 2, 2, 3, 3, 4]
    p1_deck = [1, 1, 1, 1, 1, 1, 1, 1]
    p0_lives = [10001, 10002]
    p1_lives = [10001, 10002]

    # Use the initialize_game private-ish method exposed via PyGameState
    # But wait, `initialize_game` is not exposed in the snippet I read?
    # Ah, I read `src/py_bindings.rs` and it shows:
    # `fn initialize_game(...)` IS exposed.

    game.initialize_game(p0_deck, p1_deck, [], [], p0_lives, p1_lives)

    print("\n--- Heuristic Demonstration ---\n")

    print("Scenario 1: Empty Board, Early Game")
    # P0 Hand: Mix of cards
    # Use GameEnd horizon (default) or TurnEnd? The Rust side has `SearchHorizon` enum.
    # In py_bindings, `get_mcts_suggestions` signature is `(sims, horizon=SearchHorizon::GameEnd)`.

    suggestions = game.get_mcts_suggestions(50, engine_rust.SearchHorizon.TurnEnd)
    print("MCTS Suggestions (Action, Score, Visits):")
    for s in suggestions:
        print(f"  Action {s[0]}: Score {s[1]:.4f}, Visits {s[2]}")

    # Scenario 2: Simulate different states
    # Since I cannot force state easily, I will just infer from the code and logic.
    # But wait, I can modify the heuristic in the next step to address "Volume Lead" as requested.

    # The user asked: "How does it score a position vs how it predicts a future position?"
    # Answer: It scores the LEAF node position (future) using `evaluate_player`.
    # It backs up these scores (averaged) to the root.

    # "There should be some concern over the opponent having a higher live score and also winning the live."
    # My current heuristic ignores the opponent score. I need to fix that.

    # "What is the mcts seeing?" -> The heuristic value at the leaf.

    # I will construct the answer based on the code analysis and the user's prompt.
    # The demonstration script proves I can run MCTS.


if __name__ == "__main__":
    try:
        demonstrate()
    except Exception as e:
        print(f"Error: {e}")
