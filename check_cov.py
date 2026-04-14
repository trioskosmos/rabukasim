import json

data = json.load(open('data/abilities_extracted_simple.json', 'r', encoding='utf-8'))
avg_cov = sum(a['coverage'] for a in data['abilities']) / len(data['abilities'])
print(f'Average coverage: {avg_cov:.1%}')

low_cov = [a for a in data['abilities'] if a['coverage'] < 0.5]
print(f'Abilities with < 50% coverage: {len(low_cov)}')
