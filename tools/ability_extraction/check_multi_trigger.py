#!/usr/bin/env python3
import json

with open('data/abilities_extracted_from_cards.json', encoding='utf-8') as f:
    data = json.load(f)

multi_trigger = [a for a in data['unique_abilities'] if a['trigger_count'] > 1]
print(f'Multi-trigger abilities: {len(multi_trigger)}')
for a in multi_trigger[:10]:
    print(f"  Triggers: {a['triggers']} - {a['full_text'][:80]}...")
