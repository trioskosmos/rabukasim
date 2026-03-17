#!/usr/bin/env python3
"""Analyze consolidated pseudocode to identify gaps vs parser."""

import json
import re

# Load consolidated abilities
with open("data/consolidated_abilities.json", "r", encoding="utf-8") as f:
    consolidated = json.load(f)

# Collect all unique pseudocode patterns
effects = set()
conditions = set()
triggers = set()

# Full analysis of all abilities
for ability_text, pseudo in consolidated.items():
    if not pseudo:
        continue
    lines = pseudo.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("EFFECT:"):
            effect_part = line[7:].strip()
            match = re.match(r"(\w+)", effect_part)
            if match:
                effects.add(match.group(1))
        elif line.startswith("CONDITION:"):
            cond_part = line[10:].strip()
            match = re.match(r"(\w+)", cond_part)
            if match:
                conditions.add(match.group(1))
        elif line.startswith("TRIGGER:"):
            trig_part = line[8:].strip()
            match = re.match(r"(\w+)", trig_part)
            if match:
                triggers.add(match.group(1))

print("=" * 60)
print("CONSOLIDATED PSEUDOCODE ANALYSIS")
print("=" * 60)
print(f"\nTotal abilities in consolidated DB: {len(consolidated)}")
print(f"\nUnique Effects found: {len(effects)}")
print("Effects:", sorted(effects))
print(f"\nUnique Conditions found: {len(conditions)}")
print("Conditions:", sorted(conditions))
print(f"\nUnique Triggers found: {len(triggers)}")
print("Triggers:", sorted(triggers))

# Now load the parser to see what it supports
print("\n" + "=" * 60)
print("LOADING PARSER PATTERNS...")
print("=" * 60)

# Load effect patterns from parser
import sys

sys.path.insert(0, "compiler")
from patterns.conditions import CONDITION_PATTERNS
from patterns.effects import EFFECT_PATTERNS
from patterns.triggers import TRIGGER_PATTERNS

parser_effects = set()
for p in EFFECT_PATTERNS:
    if hasattr(p, "output_type") and p.output_type:
        # Extract the EffectType enum name
        match = re.search(r"EffectType\.(\w+)", str(p.output_type))
        if match:
            parser_effects.add(match.group(1))

parser_conditions = set()
for p in CONDITION_PATTERNS:
    if hasattr(p, "output_type") and p.output_type:
        match = re.search(r"ConditionType\.(\w+)", str(p.output_type))
        if match:
            parser_conditions.add(match.group(1))

parser_triggers = set()
for p in TRIGGER_PATTERNS:
    if hasattr(p, "output_type") and p.output_type:
        match = re.search(r"TriggerType\.(\w+)", str(p.output_type))
        if match:
            parser_triggers.add(match.group(1))

print(f"\nParser Effect Types: {len(parser_effects)}")
print(sorted(parser_effects))
print(f"\nParser Condition Types: {len(parser_conditions)}")
print(sorted(parser_conditions))
print(f"\nParser Trigger Types: {len(parser_triggers)}")
print(sorted(parser_triggers))

# Compare
print("\n" + "=" * 60)
print("GAP ANALYSIS")
print("=" * 60)

missing_effects = effects - parser_effects
print(f"\nEffects in pseudocode but NOT in parser ({len(missing_effects)}):")
for e in sorted(missing_effects):
    print(f"  - {e}")

missing_conditions = conditions - parser_conditions
print(f"\nConditions in pseudocode but NOT in parser ({len(missing_conditions)}):")
for c in sorted(missing_conditions):
    print(f"  - {c}")

missing_triggers = triggers - parser_triggers
print(f"\nTriggers in pseudocode but NOT in parser ({len(missing_triggers)}):")
for t in sorted(missing_triggers):
    print(f"  - {t}")
