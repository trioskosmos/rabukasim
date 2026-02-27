#!/usr/bin/env python3
"""Analyze consolidated pseudocode - final comprehensive analysis."""

import json
import re
from collections import defaultdict

# Load consolidated pseudocode
with open('data/consolidated_abilities.json', 'r', encoding='utf-8') as f:
    consolidated = json.load(f)

# Load cards compiled to get card-to-ability mapping
with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Build ability_text -> cards mapping
ability_to_cards = defaultdict(list)
for card_id, card_data in cards.items():
    ability_text = card_data.get('ability', '')
    if ability_text:
        ability_to_cards[ability_text].append(card_id)

print(f"Loaded {len(cards)} cards")
print(f"Loaded {len(consolidated)} unique ability pseudocodes")

# Collect all unique pseudocode patterns
effects = set()
conditions = set()
triggers = set()

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
                effects.add(match.group(1))
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
import sys
sys.path.insert(0, 'compiler')
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
print("MISSING EFFECTS WITH AFFECTED CARDS (sorted by usage)")
print("=" * 80)

# Calculate usage counts
effect_usage = defaultdict(int)
effect_cards = defaultdict(set)

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
                if e in missing_effects:
                    effect_usage[e] += 1
                    for card in ability_to_cards.get(ability_text, []):
                        effect_cards[e].add(card)

# Sort by usage count
for effect in sorted(missing_effects, key=lambda x: -effect_usage[x]):
    cards = effect_cards.get(effect, set())
    if cards:
        print(f"\n{effect} ({effect_usage[effect]} abilities, {len(cards)} cards):")
        sample_cards = sorted(list(cards))[:10]
        for c in sample_cards:
            print(f"  - {c}")
        if len(cards) > 10:
            print(f"  ... and {len(cards) - 10} more")

print("\n" + "=" * 80)
print("MISSING CONDITIONS WITH AFFECTED CARDS (top 20 by usage)")
print("=" * 80)

condition_usage = defaultdict(int)
condition_cards = defaultdict(set)

for ability_text, pseudo in consolidated.items():
    if not pseudo:
        continue
    lines = pseudo.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('CONDITION:'):
            cond_part = line[10:].strip()
            match = re.match(r'(\w+)', cond_part)
            if match:
                c = match.group(1)
                if c in missing_conditions:
                    condition_usage[c] += 1
                    for card in ability_to_cards.get(ability_text, []):
                        condition_cards[c].add(card)

for cond in sorted(missing_conditions, key=lambda x: -condition_usage[x])[:20]:
    cards = condition_cards.get(cond, set())
    if cards:
        print(f"\n{cond} ({condition_usage[cond]} abilities, {len(cards)} cards):")
        sample_cards = sorted(list(cards))[:10]
        for c in sample_cards:
            print(f"  - {c}")
        if len(cards) > 10:
            print(f"  ... and {len(cards) - 10} more")

print("\n" + "=" * 80)
print("MISSING TRIGGERS WITH AFFECTED CARDS")
print("=" * 80)

trigger_usage = defaultdict(int)
trigger_cards = defaultdict(set)

for ability_text, pseudo in consolidated.items():
    if not pseudo:
        continue
    lines = pseudo.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('TRIGGER:'):
            trig_part = line[8:].strip()
            match = re.match(r'(\w+)', trig_part)
            if match:
                t = match.group(1)
                if t in missing_triggers:
                    trigger_usage[t] += 1
                    for card in ability_to_cards.get(ability_text, []):
                        trigger_cards[t].add(card)

for trigger in sorted(missing_triggers, key=lambda x: -trigger_usage[x]):
    cards = trigger_cards.get(trigger, set())
    if cards:
        print(f"\n{trigger} ({trigger_usage[trigger]} abilities, {len(cards)} cards):")
        sample_cards = sorted(list(cards))[:10]
        for c in sample_cards:
            print(f"  - {c}")
        if len(cards) > 10:
            print(f"  ... and {len(cards) - 10} more")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nTotal effects in pseudocode: {len(effects)}")
print(f"Parser supports (with aliases): {len(parser_effects_with_aliases)}")
print(f"Missing effects: {len(missing_effects)}")

print(f"\nTotal conditions in pseudocode: {len(conditions)}")
print(f"Parser supports (with aliases): {len(parser_conditions_with_aliases)}")
print(f"Missing conditions: {len(missing_conditions)}")

print(f"\nTotal triggers in pseudocode: {len(triggers)}")
print(f"Parser supports (with aliases): {len(parser_triggers_with_aliases)}")
print(f"Missing triggers: {len(missing_triggers)}")

# Count unique cards affected
all_affected_cards = set()
for cards in effect_cards.values():
    all_affected_cards.update(cards)
for cards in condition_cards.values():
    all_affected_cards.update(cards)
for cards in trigger_cards.values():
    all_affected_cards.update(cards)

print(f"\nTotal unique cards affected by missing parser support: {len(all_affected_cards)}")
