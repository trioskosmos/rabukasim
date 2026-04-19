import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
card47 = [a for a in data['unique_abilities'] if '47' in str(a.get('cards', []))]
print(f'Found {len(card47)} abilities for card 47')
for a in card47:
    print(f'Trigger: {a.get("trigger")}')
    print(f'Full text: {a.get("full_text", "")[:300]}')
    print(f'Effect: {a.get("effect")}')
