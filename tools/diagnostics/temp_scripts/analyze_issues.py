#!/usr/bin/env python3
"""Analyze issues in extracted abilities."""

import json
import re
import sys
from pathlib import Path

# Default file or take from command line
if len(sys.argv) > 1:
    input_file = sys.argv[1]
else:
    input_file = 'c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_extracted.json'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

issues = {
    'empty_logic': [],
    'japanese_fragments': [],
    'duplicates': [],
    'encoding_issues': [],
    'character_names_not_translated': []
}

for ability in data['abilities']:
    jp = ability['source_ability_texts'][0]['jp']
    logic = ability['source_ability_texts'][0]['logic']
    card = ability['source_ability_texts'][0]['cards'][0] if ability['source_ability_texts'][0]['cards'] else 'NO_CARD'
    
    # Check for empty logic
    if not logic or logic.strip() == '':
        issues['empty_logic'].append((card, jp[:80]))
    
    # Check for Japanese fragments (hiragana/katakana/kanji)
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', logic):
        issues['japanese_fragments'].append((card, logic[:100]))
    
    # Check for duplicate lines
    lines = logic.split('\n')
    seen = set()
    dups = []
    for line in lines:
        norm = line.replace('optional ', '').strip()
        if norm in seen:
            dups.append(line)
        seen.add(norm)
    if dups:
        issues['duplicates'].append((card, dups))
    
    # Check for encoding artifacts (replacement char)
    if '\ufffd' in jp:
        issues['encoding_issues'].append((card, jp[:80]))
    
    # Character name patterns not translated
    if '「' in logic or '『' in logic:
        issues['character_names_not_translated'].append((card, logic[:100]))

print('=== EMPTY LOGIC ===')
for card, jp in issues['empty_logic'][:5]:
    print(f'{card}: {jp}...')

print()
print(f'=== JAPANESE FRAGMENTS ({len(issues["japanese_fragments"])} total) ===')
for card, logic in issues['japanese_fragments'][:5]:
    print(f'{card}: {logic}...')

print()
print(f'=== DUPLICATES ({len(issues["duplicates"])} total) ===')
for card, dups in issues['duplicates'][:5]:
    print(f'{card}: {dups}')

print()
print(f'=== ENCODING ISSUES ({len(issues["encoding_issues"])} total) ===')
for card, jp in issues['encoding_issues'][:5]:
    print(f'{card}: {jp}...')

print()
print(f'=== CHARACTER NAMES NOT TRANSLATED ({len(issues["character_names_not_translated"])} total) ===')
for card, logic in issues['character_names_not_translated'][:5]:
    print(f'{card}: {logic}...')
