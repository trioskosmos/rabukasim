import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
card708 = [a for a in data['unique_abilities'] if '708' in str(a.get('cards', []))]
print(f'Found {len(card708)} abilities for card 708')
for a in card708:
    print(f'Trigger: {a.get("trigger")}')
    print(f'Full text: {a.get("full_text", "")[:300]}')
    print(f'Effect: {a.get("effect")}')
