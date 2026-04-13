import json

data = json.load(open('data/abilities_extracted.json', encoding='utf-8'))
for i, a in enumerate(data['abilities']):
    jp = a['source_ability_texts'][0].get('jp', '')
    if 'ライブカードが公開されるまで' in jp:
        print(f"Index {i}:")
        print(f"  JP: {jp}")
        print(f"  Logic: {a['source_ability_texts'][0]['logic'] if a['source_ability_texts'][0]['logic'] else 'EMPTY'}")
        print()
