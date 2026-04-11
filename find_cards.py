import json

# Try compiled cards first
with open('data/cards_compiled.json', encoding='utf-8') as f:
    data = json.load(f)

members = data.get('members', {})

target_patterns = ['PL!S-bp5-009', 'PL!HS-bp5-011', 'PL!HS-bp5-013', 'PL!N-bp5-014', 'PL!S-bp5-014', 'PL!S-bp5-015']

results = []
for k, v in members.items():
    card_no = v.get('card_no', '')
    if any(p in card_no for p in target_patterns):
        results.append({'numeric_id': k, 'card_no': card_no, 'name': v.get('name','N/A')})

with open('card_lookup.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"Found {len(results)} cards, written to card_lookup.json")
