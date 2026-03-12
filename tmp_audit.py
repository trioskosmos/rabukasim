import json
import os

filepath = 'data/consolidated_abilities.json'
with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = []
for jp_text, entry in data.items():
    pseudocode = entry.get('pseudocode', '')
    if 'まで' in jp_text:
        if '(Optional)' not in pseudocode:
            results.append({
                'cards': entry.get('cards', []),
                'pseudo': pseudocode,
                'jp': jp_text
            })

with open('reports/audit_optional_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"Found {len(results)} potential missing (Optional) tags\n\n")
    for r in results:
        f.write(f"Cards: {r['cards']}\n")
        f.write(f"JP: {r['jp']}\n")
        f.write(f"Pseudo: {r['pseudo']}\n")
        f.write("-" * 40 + "\n")
