import json
import re

with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

icon_map = set()
pattern = re.compile(r'\{\{([^|]*?\.png)\|([^}]*?)\}\}')

for card_id, data in cards.items():
    ability = data.get('ability', '')
    if ability:
        matches = pattern.findall(ability)
        for img, label in matches:
            icon_map.add(f"{img}|{label}")

with open('icon_mappings.txt', 'w', encoding='utf-8') as f:
    for item in sorted(list(icon_map)):
        f.write(item + '\n')

print(f"Extracted {len(icon_map)} unique mappings.")
