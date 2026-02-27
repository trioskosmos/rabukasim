#!/usr/bin/env python3
"""Analyze consolidated pseudocode - detailed analysis with card mapping."""

import json
import re
from collections import defaultdict

# Load consolidated abilities (with card info)
# Need to reload to get card info from the markdown or another source

# First, let's get the card mapping from the consolidated abilities
# The JSON has ability_text -> pseudocode mapping
# We need to also get card info

# Let's look at how cards are associated
# Looking at the .md file might help
with open('data/consolidated_abilities.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# Parse the markdown to get ability -> cards mapping
ability_to_cards = {}
current_ability = None
current_cards = []

for line in md_content.split('\n'):
    if line.startswith('### Ability'):
        if current_ability:
            ability_to_cards[current_ability] = current_cards
        current_ability = ""
        current_cards = []
    elif line.startswith('**Cards:**'):
        cards_str = line.replace('**Cards:**', '').strip()
        current_cards = [c.strip() for c in cards_str.split(',')]
    elif line.startswith('**Pseudocode:**'):
        pass  # pseudocode follows
    elif line.strip().startswith('TRIGGER:') and current_ability == "":
        # This is where pseudocode starts - capture until ---
        current_ability = "placeholder"

# Actually, let's use a different approach - read the JSON and map back to cards
# by checking the full_ability_coverage.json which has more info

with open('data/full_ability_coverage.json', 'r', encoding='utf-8') as f:
    coverage = json.load(f)

# This has card -> ability mappings
card_to_ability = {}
ability_to_cards = defaultdict(list)

for card_id, data in coverage.items():
    ability_text = data.get('ability_text', '')
    if ability_text:
        card_to_ability[card_id] = ability_text
        ability_to_cards[ability_text].append(card_id)

print(f"Loaded {len(card_to_ability)} cards with abilities")

# Now load consolidated pseudocode
with open('data/consolidated_abilities.json', 'r', encoding='utf-8') as f:
    consolidated = json.load(f)

# Collect all unique pseudocode patterns
effects = set()
conditions = set()
triggers = set()
ability_effects = defaultdict(set)  # which abilities use which effects

for ability_text, pseudo in consolidated.items():
    if not pseudo:
        continue
    lines = pseudo.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('EFFECT:'):
            effect_part = line[7:].strip()
            match = re.match(r'(\w+)', effect_part)
            if match:
                e = match.group(1)
                effects.add(e)
                ability_effects[e].add(ability_text)
        elif line.startswith('CONDITION:'):
            cond_part = line[10:].strip()
            match = re.match(r'(\w+)', cond_part)
            if match:
                conditions.add(match.group(1))
        elif line.startswith('TRIGGER:'):
            trig_part = line[8:].strip()
            match = re.match(r'(\w+)', trig_part)
            if match:
                triggers.add(match.group(1))

# Now load the parser to get what's supported
import sys
sys.path.insert(0, 'compiler')

# Read parser_v2.py to extract aliases
with open('compiler/parser_v2.py', 'r', encoding='utf-8') as f:
    parser_code = f.read()

# Extract aliases
effect_alias_match = re.search(r'EFFECT_ALIASES\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
all_effect_aliases = {}
if effect_alias_match:
    for line in effect_alias_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*"(\w+)"', line)
        if m:
            all_effect_aliases[m.group(1)] = m.group(2)

effect_alias_params_match = re.search(r'EFFECT_ALIASES_WITH_PARAMS\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
if effect_alias_params_match:
    for line in effect_alias_params_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*\(("[^"]+")', line)
        if m:
            all_effect_aliases[m.group(1)] = m.group(2).strip('"')

cond_alias_match = re.search(r'CONDITION_ALIASES\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
all_condition_aliases = {}
if cond_alias_match:
    for line in cond_alias_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*\(("[^"]+")', line)
        if m:
            all_condition_aliases[m.group(1)] = m.group(2).strip('"')

trigger_alias_match = re.search(r'TRIGGER_ALIASES\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
all_trigger_aliases = {}
if trigger_alias_match:
    for line in trigger_alias_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*"(\w+)"', line)
        if m:
            all_trigger_aliases[m.group(1)] = m.group(2)

# Load patterns
from patterns.effects import EFFECT_PATTERNS
from patterns.conditions import CONDITION_PATTERNS
from patterns.triggers import TRIGGER_PATTERNS

parser_effects = set()
for p in EFFECT_PATTERNS:
    if hasattr(p, 'output_type') and p.output_type:
        match = re.search(r'EffectType\.(\w+)', str(p.output_type))
        if match:
            parser_effects.add(match.group(1))

parser_effects_with_aliases = parser_effects.copy()
for alias, canonical in all_effect_aliases.items():
    parser_effects_with_aliases.add(canonical)

parser_conditions = set()
for p in CONDITION_PATTERNS:
    if hasattr(p, 'output_type') and p.output_type:
        match = re.search(r'ConditionType\.(\w+)', str(p.output_type))
        if match:
            parser_conditions.add(match.group(1))

parser_conditions_with_aliases = parser_conditions.copy()
for alias, canonical in all_condition_aliases.items():
    parser_conditions_with_aliases.add(canonical)

parser_triggers = set()
for p in TRIGGER_PATTERNS:
    if hasattr(p, 'output_type') and p.output_type:
        match = re.search(r'TriggerType\.(\w+)', str(p.output_type))
        if match:
            parser_triggers.add(match.group(1))

parser_triggers_with_aliases = parser_triggers.copy()
for alias, canonical in all_trigger_aliases.items():
    parser_triggers_with_aliases.add(canonical)

# Get missing items
missing_effects = effects - parser_effects_with_aliases
missing_conditions = conditions - parser_conditions_with_aliases
missing_triggers = triggers - parser_triggers_with_aliases

# Find cards for each missing effect
print("=" * 80)
print("MISSING EFFECTS WITH AFFECTED CARDS")
print("=" * 80)

for effect in sorted(missing_effects):
    # Find all abilities using this effect
    relevant_abilities = []
    for ability_text, pseudo in consolidated.items():
        if pseudo and f'EFFECT: {effect}' in pseudo or f'EFFECT: {effect}(' in pseudo:
            relevant_abilities.append(ability_text)
    
    # Get all cards with these abilities
    cards = set()
    for ab in relevant_abilities:
        for card_id in ability_to_cards.get(ab, []):
            cards.add(card_id)
    
    if cards:
        print(f"\n{effect} ({len(cards)} cards):")
        # Show sample cards
        sample_cards = sorted(list(cards))[:10]
        for c in sample_cards:
            print(f"  - {c}")
        if len(cards) > 10:
            print(f"  ... and {len(cards) - 10} more")

print("\n" + "=" * 80)
print("MISSING CONDITIONS WITH AFFECTED CARDS")
print("=" * 80)

for cond in sorted(missing_conditions)[:20]:  # Limit to top 20
    relevant_abilities = []
    for ability_text, pseudo in consolidated.items():
        if pseudo and f'CONDITION: {cond}' in pseudo or f'CONDITION: {cond}(' in pseudo:
            relevant_abilities.append(ability_text)
    
    cards = set()
    for ab in relevant_abilities:
        for card_id in ability_to_cards.get(ab, []):
            cards.add(card_id)
    
    if cards:
        print(f"\n{cond} ({len(cards)} cards):")
        sample_cards = sorted(list(cards))[:10]
        for c in sample_cards:
            print(f"  - {c}")
        if len(cards) > 10:
            print(f"  ... and {len(cards) - 10} more")

print("\n" + "=" * 80)
print("MISSING TRIGGERS WITH AFFECTED CARDS")
print("=" * 80)

for trigger in sorted(missing_triggers):
    relevant_abilities = []
    for ability_text, pseudo in consolidated.items():
        if pseudo and f'TRIGGER: {trigger}' in pseudo:
            relevant_abilities.append(ability_text)
    
    cards = set()
    for ab in relevant_abilities:
        for card_id in ability_to_cards.get(ab, []):
            cards.add(card_id)
    
    if cards:
        print(f"\n{trigger} ({len(cards)} cards):")
        sample_cards = sorted(list(cards))[:10]
        for c in sample_cards:
            print(f"  - {c}")
        if len(cards) > 10:
            print(f"  ... and {len(cards) - 10} more")
