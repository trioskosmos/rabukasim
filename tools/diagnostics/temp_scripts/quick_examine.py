#!/usr/bin/env python3
import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("EXAMINING ABILITIES FOR EXTRACTION GAPS\n")

# Find specific patterns
samples = []
for ability in data['abilities']:
    source = ability['source_ability_texts'][0]
    logic = source['logic']
    jp = source['jp']
    cards = source['cards']
    card = cards[0] if cards else 'UNKNOWN'
    
    # Look for score mentions
    if 'score' in jp.lower() and 'score' not in logic.lower():
        samples.append(('SCORE_NOT_EXTRACTED', card, jp[:100], logic[:80]))
    
    # Look for cost comparisons
    elif 'lower cost' in jp.lower() and 'lower cost' not in logic.lower():
        samples.append(('COST_COMPARISON', card, jp[:100], logic[:80]))
    
    # Look for reveal effects
    elif 'revealed' in jp.lower() and 'revealed' not in logic.lower():
        samples.append(('REVEAL_EFFECT', card, jp[:100], logic[:80]))
    
    # Look for multi-trigger abilities
    elif jp.count('{{') >= 2 and '/' not in jp and logic.count('\n') < 2:
        samples.append(('MULTI_TRIGGER?', card, jp[:100], logic[:80]))
    
    if len(samples) >= 10:
        break

for i, (issue, card, jp, logic) in enumerate(samples, 1):
    print(f"{i}. [{issue}] {card}")
    print(f"   JP: {jp}...")
    print(f"   LOGIC: {logic}...")
    print()

print(f"Found {len(samples)} examples of potential extraction gaps")
