import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
card777 = [a for a in data['unique_abilities'] if 'PL!N-bp5-029-L' in str(a.get('cards', []))]
print(f'Found {len(card777)} abilities for card 777')
for a in card777:
    print(f'Trigger: {a.get("trigger")}')
    print(f'Full text: {a.get("full_text", "")}')
    print(f'Effect: {a.get("effect")}')
