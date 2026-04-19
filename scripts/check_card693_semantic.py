import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
card693 = [a for a in data['unique_abilities'] if '693' in str(a.get('cards', []))]
print(f'Found {len(card693)} abilities for card 693')
for a in card693:
    print(f'Trigger: {a.get("trigger")}')
    print(f'Full text: {a.get("full_text", "")[:200]}')
    print(f'Effect: {a.get("effect")}')
