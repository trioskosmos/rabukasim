import json

path = "engine/data/cards_compiled.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)


# Recursive search
def find_recursive(obj, serial):
    if isinstance(obj, dict):
        if obj.get("card_no") == serial or serial in str(obj.get("card_no", "")):
            return obj
        for v in obj.values():
            res = find_recursive(v, serial)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_recursive(item, serial)
            if res:
                return res
    return None


target = find_recursive(data, "pb1-007-R")

if target:
    print(f"Card: {target.get('card_no')} - {target.get('name')}")
    abilities = target.get("abilities", [])
    print(f"Ability count: {len(abilities)}")
    for i, ab in enumerate(abilities):
        print(f"\n--- Ability {i} ---")
        print(f"Trigger: {ab.get('trigger')}")
        print(f"Raw Text: {ab.get('raw_text')}")
        effs = []
        for e in ab.get("effects", []):
            effs.append(f"Type {e.get('effect_type')} Val {e.get('value')} Params {e.get('params')}")
        print(f"Effects: {effs}")
        print(f"Conditions: {ab.get('conditions', [])}")
        print(f"Costs: {ab.get('costs', [])}")
else:
    print("Card not found")
