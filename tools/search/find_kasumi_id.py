import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for cid, card in data["member_db"].items():
    if card.get("card_no") == "PL!N-bp1-002-SEC":
        print(f"Found card: CID={cid}, Name={card['name']}")
        for i, ability in enumerate(card.get("abilities", [])):
            print(f"  Ability {i}: {ability.get('raw_text')}")
            print(f"    Trigger: {ability.get('trigger')}")
            for effect in ability.get("effects", []):
                print(f"      Effect: {effect.get('effect_type')}, Target: {effect.get('target')}")
