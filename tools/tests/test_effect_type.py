import json

import engine_rust

# Try to create a card database from a JSON with effect_type 42
test_db_json = json.dumps(
    {
        "members": {
            "1": {
                "card_id": 1,
                "card_no": "TEST-001",
                "name": "Test Card",
                "rarity": "N",
                "group": "Aqours",
                "unit": "CYaRon!",
                "hearts": [0, 0, 0, 0, 0, 0, 0],
                "blades": 0,
                "hand_count": 0,
                "deck_count": 0,
                "abilities": [
                    {
                        "raw_text": "Test",
                        "trigger": 1,
                        "costs": [],
                        "conditions": [],
                        "effects": [{"effect_type": 42, "value": 1, "target": 0, "params": {}}],
                        "bytecode": [1, 0, 0, 0],
                    }
                ],
            }
        },
        "lives": {},
    }
)

try:
    db = engine_rust.PyCardDatabase(test_db_json)
    print("SUCCESS: PyCardDatabase accepted effect_type 42")
except Exception as e:
    print(f"FAILURE: {e}")
