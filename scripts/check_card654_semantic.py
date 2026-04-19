import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
cards = [a for a in data['unique_abilities'] if '654' in str(a.get('cards', []))]
print(f'Found cards with 654: {len(cards)}')
for a in cards[:5]:
    print(f'Cards: {a.get("cards")}')
    print(f'Trigger: {a.get("trigger")}')
    print(f'Full text: {a.get("full_text", "")[:200]}')
