#!/usr/bin/env python3
"""Analyze consolidated pseudocode - improved version with alias checking."""

import json
import re
from collections import defaultdict

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

# Now load the parser aliases
import sys

sys.path.insert(0, "compiler")
from parser_v2 import CONDITION_ALIASES, EFFECT_ALIASES, EFFECT_ALIASES_WITH_PARAMS, TRIGGER_ALIASES

# Build a full mapping of aliases to canonical names
all_effect_aliases = {}
for alias, canonical in EFFECT_ALIASES.items():
    all_effect_aliases[alias] = canonical
for alias, (canonical, params) in EFFECT_ALIASES_WITH_PARAMS.items():
    all_effect_aliases[alias] = canonical

all_condition_aliases = {}
for alias, (canonical, params) in CONDITION_ALIASES.items():
    all_condition_aliases[alias] = canonical

all_trigger_aliases = {}
for alias, canonical in TRIGGER_ALIASES.items():
    all_trigger_aliases[alias] = canonical

print("=" * 60)
print("EFFECT ALIASES IN PARSER")
print("=" * 60)
print(f"Total effect aliases: {len(all_effect_aliases)}")
print(sorted(all_effect_aliases.keys()))

# Now load effect patterns from parser to get canonical types
from patterns.effects import EFFECT_PATTERNS

parser_effects = set()
for p in EFFECT_PATTERNS:
    if hasattr(p, "output_type") and p.output_type:
        match = re.search(r"EffectType\.(\w+)", str(p.output_type))
        if match:
            parser_effects.add(match.group(1))

# Add aliases as valid too
parser_effects_with_aliases = parser_effects.copy()
for alias, canonical in all_effect_aliases.items():
    parser_effects_with_aliases.add(canonical)

# Load condition patterns
from patterns.conditions import CONDITION_PATTERNS

parser_conditions = set()
for p in CONDITION_PATTERNS:
    if hasattr(p, "output_type") and p.output_type:
        match = re.search(r"ConditionType\.(\w+)", str(p.output_type))
        if match:
            parser_conditions.add(match.group(1))

# Add aliases
parser_conditions_with_aliases = parser_conditions.copy()
for alias, canonical in all_condition_aliases.items():
    parser_conditions_with_aliases.add(canonical)

# Load trigger patterns
from patterns.triggers import TRIGGER_PATTERNS

parser_triggers = set()
for p in TRIGGER_PATTERNS:
    if hasattr(p, "output_type") and p.output_type:
        match = re.search(r"TriggerType\.(\w+)", str(p.output_type))
        if match:
            parser_triggers.add(match.group(1))

# Add aliases
parser_triggers_with_aliases = parser_triggers.copy()
for alias, canonical in all_trigger_aliases.items():
    parser_triggers_with_aliases.add(canonical)

print("\n" + "=" * 60)
print("REFINED GAP ANALYSIS (with aliases)")
print("=" * 60)

# Now check what's truly missing
missing_effects = effects - parser_effects_with_aliases
print(f"\nEffects in pseudocode but NOT in parser ({len(missing_effects)}):")
for e in sorted(missing_effects):
    print(f"  - {e}")

missing_conditions = conditions - parser_conditions_with_aliases
print(f"\nConditions in pseudocode but NOT in parser ({len(missing_conditions)}):")
for c in sorted(missing_conditions):
    print(f"  - {c}")

missing_triggers = triggers - parser_triggers_with_aliases
print(f"\nTriggers in pseudocode but NOT in parser ({len(missing_triggers)}):")
for t in sorted(missing_triggers):
    print(f"  - {t}")

# Now check if these are real opcode gaps or just pseudocode syntax issues
print("\n" + "=" * 60)
print("ANALYZING IF MISSING ITEMS NEED NEW OPCODES")
print("=" * 60)

# Check which missing effects look like they're using the engine opcode system
# vs which are custom pseudocode syntax

# Some items might be VALUE computations or COUNT operations that don't need opcodes
# Let's categorize them

print("\n--- LIKELY ALIASES/EDGE CASES (probably don't need new opcodes) ---")
# These are likely aliases that weren't caught or are edge cases
edge_case_effects = [
    e for e in missing_effects if "SELECT" in e or "CHOICE" in e or "COUNT" in e or e in ["IF", "LOOP", "CONDITION"]
]
print(f"Potential edge case effects ({len(edge_case_effects)}): {sorted(edge_case_effects)}")

edge_case_conditions = [
    c for c in missing_conditions if "COUNT" in c or "SUM" in c or c in ["FILTER", "OR", "ZONE_EQ", "AREA", "AREA_IN"]
]
print(f"Potential edge case conditions ({len(edge_case_conditions)}): {sorted(edge_case_conditions)}")

# The real gaps - things that look like they need opcodes
real_gap_effects = missing_effects - set(edge_case_effects)
print(f"\n--- REAL EFFECT GAPS (need opcodes or parser support) ({len(real_gap_effects)}) ---")
for e in sorted(real_gap_effects):
    print(f"  - {e}")

real_gap_conditions = missing_conditions - set(edge_case_conditions)
print(f"\n--- REAL CONDITION GAPS ({len(real_gap_conditions)}) ---")
for c in sorted(real_gap_conditions):
    print(f"  - {c}")

# Let's also check how many abilities use these missing items
print("\n" + "=" * 60)
print("USAGE COUNT OF MISSING ITEMS")
print("=" * 60)

effect_usage = defaultdict(int)
condition_usage = defaultdict(int)
trigger_usage = defaultdict(int)

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
                e = match.group(1)
                if e in real_gap_effects:
                    effect_usage[e] += 1
        elif line.startswith("CONDITION:"):
            cond_part = line[10:].strip()
            match = re.match(r"(\w+)", cond_part)
            if match:
                c = match.group(1)
                if c in real_gap_conditions:
                    condition_usage[c] += 1
        elif line.startswith("TRIGGER:"):
            trig_part = line[8:].strip()
            match = re.match(r"(\w+)", trig_part)
            if match:
                t = match.group(1)
                if t in missing_triggers:
                    trigger_usage[t] += 1

print("\nReal gap effects usage count:")
for e, count in sorted(effect_usage.items(), key=lambda x: -x[1])[:20]:
    print(f"  {e}: {count} abilities")

print("\nReal gap conditions usage count:")
for c, count in sorted(condition_usage.items(), key=lambda x: -x[1])[:20]:
    print(f"  {c}: {count} abilities")

print("\nMissing triggers usage count:")
for t, count in sorted(trigger_usage.items(), key=lambda x: -x[1]):
    print(f"  {t}: {count} abilities")
