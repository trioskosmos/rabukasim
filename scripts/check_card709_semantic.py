import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
card709 = [a for a in data['unique_abilities'] if 'PL!HS-bp5-018-L' in str(a.get('cards', []))]
print(f'Found {len(card709)} abilities for card 709')
for a in card709:
    print(f'Trigger: {a.get("trigger")}')
    print(f'Full text: {a.get("full_text", "")[:300]}')
    print(f'Effect: {a.get("effect")}')
