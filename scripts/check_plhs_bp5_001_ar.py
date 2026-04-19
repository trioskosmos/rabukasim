import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
card = [a for a in data['unique_abilities'] if 'PL!HS-bp5-001-AR' in str(a.get('cards', []))]
print(f'Found {len(card)} abilities for PL!HS-bp5-001-AR')
for a in card:
    print(f'Trigger: {a.get("trigger")}')
    print(f'Full text: {a.get("full_text", "")[:300]}')
    print(f'Effect: {a.get("effect")}')
