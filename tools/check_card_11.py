import json

path = "data/cards_compiled.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for card in data:
    if isinstance(card, dict) and card.get("card_no") == "PL!HS-bp2-011-N":
        print(f"Card: {card['card_no']}")
        for i, ability in enumerate(card.get("abilities", [])):
            print(f"Ability {i}:")
            # The compiled data doesn't have the original Ability object, but maybe we can see params in cards.json first
            pass

# Also let's check the manual pseudocode parsing directly
from compiler.parser_v2 import AbilityParserV2

parser = AbilityParserV2()
text = """TRIGGER: ON_PLAY
EFFECT: MOVE_TO_DISCARD(5) {FROM="DECK_TOP"}"""
abilities = parser.parse(text)
for a in abilities:
    for e in a.effects:
        print(f"Effect: {e.effect_type}")
        print(f"Params: {e.params}")
        # Manual check of what source_val would be
        source = str(
            e.params.get("source")
            or e.params.get("SOURCE")
            or e.params.get("from")
            or e.params.get("FROM")
            or "discard"
        ).lower()
        print(f"Calculated source string: {source}")
