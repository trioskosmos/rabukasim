import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_rust
from ai.benchmark_decks import parse_deck


def debug_legal_actions():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)
    db = engine_rust.PyCardDatabase(db_content)
    game = engine_rust.PyGameState(db)

    muse_deck_path = "ai/decks/muse_cup.txt"
    p_deck, p_lives = parse_deck(muse_deck_path, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {}))

    p_energy = [2000] * 20
    game.initialize_game(p_deck, p_deck, p_energy, p_energy, p_lives, p_lives)

    # Get past mulligan
    game.step(0)  # P1 muligan - keep all
    game.step(0)  # P2 mulligan - keep all

    # Now in Active/Energy/Draw then Main
    while game.phase != 4:  # Wait for Main phase
        game.step(0)

    print(f"Phase: {game.phase} (Main)")
    print(f"Current Player: {game.current_player}")
    p_state = game.get_player(game.current_player)
    print(f"Stage: {p_state.stage}")
    print(f"Hand: {p_state.hand}")

    # Get legal actions
    legal_ids = game.get_legal_action_ids()
    print(f"\nLegal Action IDs: {legal_ids}")

    # Check for ability actions (200-299)
    ability_actions = [a for a in legal_ids if 200 <= a < 300]
    print(f"Ability Actions: {ability_actions}")

    # Check if any slot has a member
    for i, cid in enumerate(p_state.stage):
        if cid >= 0:
            print(f"  Slot {i} has member ID {cid}")
        else:
            print(f"  Slot {i} is EMPTY")


if __name__ == "__main__":
    debug_legal_actions()
