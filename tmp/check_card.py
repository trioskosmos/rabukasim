import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for card_no, card_data in d.get("member_db", {}).items():
    if card_no == "PL!N-bp3-005-R\uff0b" or card_data.get("card_no") == "PL!N-bp3-005-R\uff0b":
        print(f"Found by key: {card_no}")
        for i, ab in enumerate(card_data.get("abilities", [])):
            print(f"\n=== Ability {i} ===")
            print(f"Trigger: {ab.get('trigger')}")
            print(f"Bytecode: {ab.get('bytecode')}")
            print(f"Conditions: {json.dumps(ab.get('conditions', []), indent=2, ensure_ascii=False)}")
            print(f"Costs: {json.dumps(ab.get('costs', []), indent=2, ensure_ascii=False)}")
        break
else:
    # Try numeric keys
    for key, card_data in d.get("member_db", {}).items():
        if str(card_data.get("card_id")) == "4369":
            print(f"Found by ID: key={key}")
            for i, ab in enumerate(card_data.get("abilities", [])):
                print(f"\n=== Ability {i} ===")
                print(f"Trigger: {ab.get('trigger')}")
                print(f"Bytecode: {ab.get('bytecode')}")
                print(f"Conditions: {json.dumps(ab.get('conditions', []), indent=2, ensure_ascii=False)}")
                print(f"Costs: {json.dumps(ab.get('costs', []), indent=2, ensure_ascii=False)}")
            break
    else:
        print("NOT FOUND. Sample keys:", list(d.get("member_db", {}).keys())[:5])
