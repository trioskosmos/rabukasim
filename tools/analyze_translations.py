import json
import re

with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Extract all unique card names
all_names = {}
for card_id, card in cards.items():
    if 'name' in card and card['name'].strip():
        card_type = card.get('type', 'unknown')
        if card['name'] not in all_names:
            all_names[card['name']] = card_type

# Read existing names.js to see what's already translated
with open('frontend/web_ui/js/i18n/names.js', 'r', encoding='utf-8') as f:
    names_content = f.read()
    existing = {}
    pattern = r'"([^"]+)":\s*"([^"]+)"'
    for match in re.finditer(pattern, names_content):
        existing[match.group(1)] = match.group(2)

print(f'Already have {len(existing)} translations')
print(f'Total unique card names: {len(all_names)}')

# Categorize what we need to add
members = [n for n, t in all_names.items() if t == 'メンバー']
lives = [n for n, t in all_names.items() if t == 'ライブ']
energies = [n for n, t in all_names.items() if t == 'エネルギー']

print(f'\nMembers to handle: {len(members)}')
print(f'Lives to handle: {len(lives)}')
print(f'Energies to handle: {len(energies)}')

# Show what's not yet translated
not_translated_members = [n for n in members if n not in existing]
print(f'\nMembers NOT yet translated: {len(not_translated_members)}')
for name in sorted(not_translated_members)[:15]:
    print(f'  - {name}')

# Show Lives (many are already in English, some need JP)
print(f'\nAll Lives sample:')
for name in sorted(lives)[:20]:
    trans = existing.get(name, '(needs translation)')
    print(f'  - {name} -> {trans}')

# Extract products
products = {}
for card in cards.values():
    if 'product' in card:
        products[card['product']] = 1

print(f'\nProducts to translate:')
for prod in sorted(products.keys()):
    print(f'  - {prod}')

# Extract series
series = {}
for card in cards.values():
    if 'series' in card:
        series[card['series']] = 1

print(f'\nSeries to translate:')
for ser in sorted(series.keys()):
    print(f'  - {ser}')
