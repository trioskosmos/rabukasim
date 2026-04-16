#!/usr/bin/env python3
"""
Extract and analyze simple effects for pattern-based extraction.
This script reads: ../data/abilities_extracted_from_cards.json
This script writes: ../data/simple_effects_patterns.json
"""

import json
import re
from collections import Counter

with open('../data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract unique simple abilities (no comma, exactly one full stop)
simple_abilities = []
for ab in data['unique_abilities']:
    costless_text = ab.get('costless_text', '')
    if costless_text and '、' not in costless_text and costless_text.count('。') == 1:
        simple_abilities.append(costless_text)

unique_simple = list(set(simple_abilities))

# Analyze patterns
patterns = {
    'draw': [],
    'add_to_hand': [],
    'activate_energy': [],
    'wait': [],
    'discard': [],
    'move_to_deck': [],
    'gain_resource': [],
    'other': []
}

for text in unique_simple:
    if 'カードを' in text and '引く' in text:
        patterns['draw'].append(text)
    elif '手札に加える' in text:
        patterns['add_to_hand'].append(text)
    elif 'アクティブにする' in text:
        patterns['activate_energy'].append(text)
    elif 'ウェイトにする' in text:
        patterns['wait'].append(text)
    elif '控え室に置く' in text:
        patterns['discard'].append(text)
    elif 'デッキ' in text and ('置く' in text or '戻す' in text):
        patterns['move_to_deck'].append(text)
    elif 'を得る' in text or 'を加算する' in text or '+１する' in text or '+２する' in text:
        patterns['gain_resource'].append(text)
    else:
        patterns['other'].append(text)

# Extract variable patterns
output = {
    'total_simple_abilities': len(unique_simple),
    'patterns': {}
}

for pattern_type, texts in patterns.items():
    if texts:
        # Extract common structure
        output['patterns'][pattern_type] = {
            'count': len(texts),
            'examples': texts[:5]
        }

# Write to file
with open('../data/simple_effects_patterns.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Analyzed {len(unique_simple)} unique simple abilities")
print(f"Found {len([k for k, v in patterns.items() if v])} pattern types")
print(f"Output written to ../data/simple_effects_patterns.json")
