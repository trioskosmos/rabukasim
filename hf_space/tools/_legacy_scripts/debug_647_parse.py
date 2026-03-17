import json

from compiler.parser import AbilityParser


def parse_647():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    card = db["member_db"].get("647")
    if not card:
        print("Card 647 not found in member_db")
        return

    text = card["ability_text"]
    print(f"Text: {text}")

    abilities = AbilityParser.parse_ability_text(text)
    for i, a in enumerate(abilities):
        print(f"Ability {i}:")
        print(a)
        for e in a.effects:
            print(f"  Effect: {e.effect_type.name} val={e.value} params={e.params}")
        for c in a.conditions:
            print(f"  Condition: {c.type.name} params={c.params}")


if __name__ == "__main__":
    parse_647()
