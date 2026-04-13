#!/usr/bin/env python3
import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== CHARACTER NAMES ANALYSIS ===\n")

# 1. Character names in select patterns
print("1. CHARACTER NAMES IN SELECTION:")
count = 0
for ability in data['abilities']:
    logic = ability['source_ability_texts'][0]['logic']
    if 'select member card with' in logic and 'name ' in logic:
        card = ability['source_ability_texts'][0]['cards'][0]
        print(f"  {card}: {logic[:120]}...")
        count += 1
        if count >= 5:
            break

# 2. Baton touch with character/unit names
print("\n2. BATON TOUCH PATTERNS:")
count = 0
for ability in data['abilities']:
    logic = ability['source_ability_texts'][0]['logic']
    if 'baton touch from' in logic.lower():
        card = ability['source_ability_texts'][0]['cards'][0]
        print(f"  {card}: {logic[:120]}...")
        count += 1
        if count >= 5:
            break

# 3. Group filters in selection
print("\n3. GROUP FILTERS IN SELECTION:")
count = 0
for ability in data['abilities']:
    logic = ability['source_ability_texts'][0]['logic']
    if 'select live card with group' in logic:
        card = ability['source_ability_texts'][0]['cards'][0]
        print(f"  {card}: {logic[:120]}...")
        count += 1
        if count >= 5:
            break

# 4. Problems - character names that didn't translate
print("\n4. POTENTIAL ISSUES - LOOKING FOR JAPANESE FRAGMENTS WITH NAMES:")
count = 0
for ability in data['abilities']:
    logic = ability['source_ability_texts'][0]['logic']
    cards = ability['source_ability_texts'][0]['cards']
    
    # Look for logic that has both English and garbled text
    if any(x in logic for x in ['member', 'name', 'group']):
        if any(ord(c) > 0x3000 for c in logic):  # Has Japanese range chars
            if len(cards) > 0:
                print(f"  {cards[0]}: {logic[:100]}...")
                count += 1
                if count >= 5:
                    break

print("\n=== DONE ===")
