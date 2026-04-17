import json

data = json.load(open('data/abilities_extracted_from_cards.json', encoding='utf-8'))
for i, ab in enumerate(data['unique_abilities']):
    cost = ab.get('cost')
    if cost and not isinstance(cost, dict):
        print(f'Ability {i} has non-dict cost: {cost} (type: {type(cost)})')
        break
else:
    print('All costs are dicts')
