import json
import re


def sanitize_test_name(name):
    """Sanitize card No/Name into a valid Python function name."""
    s = str(name).lower()
    s = re.sub(r"[^a-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def generate_batch3_tests():
    with open("batch3_parsing_check.json", "r", encoding="utf-8") as f:
        batch_cards = json.load(f)

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    output_path = "engine/tests/cards/batches/test_easy_wins_batch_3.py"

    header = """import pytest
from engine.game.game_state import GameState
from engine.models.ability import TriggerType

# Batch 3 Verification Tests
# Targets cards identified in pending_easy_wins.json (Batch 3)

"""

    test_template_member = """
def test_{test_name}(game_state: GameState):
    \"\"\"
    Card: {card_no} ({name})
    Ability: {ability_text}
    \"\"\"
    card_id = {card_id}
    # Setup: Put card in hand
    game_state.players[0].hand = [card_id]
    game_state.players[0].energy = 10

    # Action: Play the card
    game_state._play_member(0, 0)

    # Assertions
    assert card_id in game_state.players[0].stage
"""

    test_template_live = """
def test_{test_name}_live(game_state: GameState):
    \"\"\"
    Live Card: {card_no} ({name})
    Ability: {ability_text}
    \"\"\"
    card_id = {card_id}
    # Setup: Put in hand
    game_state.players[0].hand = [card_id]

    # Action: Set as live card
    game_state._set_live_card(0)

    # Assertions
    assert card_id in game_state.players[0].live_zone
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        for card in batch_cards:
            if not card["abilities"]:
                continue

            is_live = str(card["id"]) in db["live_db"]
            template = test_template_live if is_live else test_template_member

            test_name = sanitize_test_name(card["card_no"])
            f.write(
                template.format(
                    test_name=test_name,
                    card_no=card["card_no"],
                    name=card["name"],
                    ability_text=card["abilities"][0]["text"],
                    card_id=card["id"],
                )
            )

    print(f"Generated {output_path}")


if __name__ == "__main__":
    generate_batch3_tests()
