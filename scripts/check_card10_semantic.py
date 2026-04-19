import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
card10 = [a for a in data['unique_abilities'] if 'LL-bp2-001-R+' in str(a.get('cards', []))]
print(f'Found {len(card10)} unique abilities for card 10')
for a in card10:
    print(f'Ability: {a.get("trigger", "UNKNOWN")} - {a.get("full_text", "")[:150]}')
    if 'cost' in a:
        print(f'  Cost: {a["cost"]}')
    if 'effect' in a:
        print(f'  Effect: {a["effect"]}')
