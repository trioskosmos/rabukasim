import json
with open('data/cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for k, v in data.items():
    rare_list = v.get("rare_list", [])
    if rare_list:
        print(f"Base: {k} ({v.get('name')})")
        for variant in rare_list:
            print(f"  - Variant: {variant.get('card_no')} ({variant.get('rare')})")
        count += 1
        if count >= 5:
            break
