#!/usr/bin/env python3
"""
Analyze abilities containing 'バトンタッチ' (batontouch) to understand their representation.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

# Load cards.json to find abilities with batontouch
cards_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards.json")
with open(cards_file, 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Search for abilities containing バトンタッチ
batontouch_abilities = []

for card in cards:
    if 'abilities' in card:
        for ability in card['abilities']:
            ability_text = ability.get('text', '')
            if 'バトンタッチ' in ability_text:
                batontouch_abilities.append({
                    'card_id': card.get('id'),
                    'card_name': card.get('name', ''),
                    'ability_id': ability.get('id'),
                    'ability_text': ability_text,
                    'trigger_id': ability.get('trigger_id'),
                    'trigger_icon': ability.get('trigger_icon', '')
                })

# Prepare output
output_lines = []
output_lines.append(f"Found {len(batontouch_abilities)} abilities containing 'バトンタッチ'")
output_lines.append("=" * 80)

# Display sample abilities
output_lines.append(f"\nSample abilities (first 5):")
for i, ab in enumerate(batontouch_abilities[:5]):
    output_lines.append(f"\n{i+1}. Card: {ab['card_name']} (ID: {ab['card_id']})")
    output_lines.append(f"   Trigger: {ab['trigger_icon']} (ID: {ab['trigger_id']})")
    output_lines.append(f"   Text: {ab['ability_text']}")

# Analyze trigger types
trigger_counts = Counter()
for ab in batontouch_abilities:
    trigger_counts[ab['trigger_icon']] += 1

output_lines.append(f"\n\nTrigger distribution:")
for trigger, count in trigger_counts.most_common():
    output_lines.append(f"  {trigger}: {count}")

# Analyze text patterns
output_lines.append(f"\n\nText pattern analysis:")
text_samples = []
for ab in batontouch_abilities:
    text_samples.append(ab['ability_text'])

# Find common phrases
phrase_counts = defaultdict(int)
for text in text_samples:
    words = text.split()
    for i in range(len(words) - 1):
        phrase = ' '.join(words[i:i+2])
        if 'バトンタッチ' in phrase:
            phrase_counts[phrase] += 1

output_lines.append(f"\nCommon phrases with 'バトンタッチ':")
for phrase, count in sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True):
    output_lines.append(f"  '{phrase}': {count}")

# Check how they're represented in abilities_extracted.json
output_lines.append(f"\n\nChecking representation in abilities_extracted.json...")
extracted_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\abilities_extracted.json")
with open(extracted_file, 'r', encoding='utf-8') as f:
    extracted_data = json.load(f)

# Search for batontouch in extracted data
def search_batontouch(obj, path=""):
    results = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            results.extend(search_batontouch(value, f"{path}.{key}" if path else key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(search_batontouch(item, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if 'バトンタッチ' in obj:
            results.append((path, obj))
    return results

batontouch_matches = search_batontouch(extracted_data)
output_lines.append(f"Found {len(batontouch_matches)} occurrences of 'バトンタッチ' in abilities_extracted.json")

if batontouch_matches:
    output_lines.append(f"\nSample occurrences (first 20):")
    for path, text in batontouch_matches[:20]:
        output_lines.append(f"  Path: {path}")
        output_lines.append(f"  Text: {text[:150]}...")

# Save to file
output_file = Path(r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\batontouch_analysis.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"Results saved to {output_file}")
print(f"Found {len(batontouch_abilities)} abilities with batontouch")
print(f"Found {len(batontouch_matches)} occurrences in abilities_extracted.json")
