#!/usr/bin/env python3
"""Analyze consolidated pseudocode - standalone version."""

import json
import re
from collections import defaultdict

# Load consolidated abilities
with open('data/consolidated_abilities.json', 'r', encoding='utf-8') as f:
    consolidated = json.load(f)

# Collect all unique pseudocode patterns
effects = set()
conditions = set()
triggers = set()

# Full analysis of all abilities
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

# Extract EFFECT_ALIASES
effect_alias_match = re.search(r'EFFECT_ALIASES\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
all_effect_aliases = {}
if effect_alias_match:
    for line in effect_alias_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*"(\w+)"', line)
        if m:
            all_effect_aliases[m.group(1)] = m.group(2)

# Extract EFFECT_ALIASES_WITH_PARAMS  
effect_alias_params_match = re.search(r'EFFECT_ALIASES_WITH_PARAMS\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
if effect_alias_params_match:
    for line in effect_alias_params_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*\(("[^"]+")', line)
        if m:
            all_effect_aliases[m.group(1)] = m.group(2).strip('"')

# Extract CONDITION_ALIASES
cond_alias_match = re.search(r'CONDITION_ALIASES\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
all_condition_aliases = {}
if cond_alias_match:
    for line in cond_alias_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*\(("[^"]+")', line)
        if m:
            all_condition_aliases[m.group(1)] = m.group(2).strip('"')

# Extract TRIGGER_ALIASES
trigger_alias_match = re.search(r'TRIGGER_ALIASES\s*=\s*\{([^}]+)\}', parser_code, re.DOTALL)
all_trigger_aliases = {}
if trigger_alias_match:
    for line in trigger_alias_match.group(1).split('\n'):
        m = re.match(r'\s*"(\w+)":\s*"(\w+)"', line)
        if m:
            all_trigger_aliases[m.group(1)] = m.group(2)

print("=" * 60)
print("EFFECT ALIASES IN PARSER")
print("=" * 60)
print(f"Total effect aliases: {len(all_effect_aliases)}")
print(sorted(all_effect_aliases.keys())[:30])

# Now load effect patterns from parser to get canonical types
import sys
sys.path.insert(0, 'compiler')
from patterns.effects import EFFECT_PATTERNS

parser_effects = set()
for p in EFFECT_PATTERNS:
    if hasattr(p, 'output_type') and p.output_type:
        match = re.search(r'EffectType\.(\w+)', str(p.output_type))
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
    if hasattr(p, 'output_type') and p.output_type:
        match = re.search(r'ConditionType\.(\w+)', str(p.output_type))
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
    if hasattr(p, 'output_type') and p.output_type:
        match = re.search(r'TriggerType\.(\w+)', str(p.output_type))
        if match:
            parser_triggers.add(match.group(1))

# Add aliases
parser_triggers_with_aliases = parser_triggers.copy()
for alias, canonical in all_trigger_aliases.items():
    parser_triggers_with_aliases.add(canonical)

print(f"\nParser effect types (with patterns): {len(parser_effects_with_aliases)}")
print(f"Parser condition types (with patterns): {len(parser_conditions_with_aliases)}")
print(f"Parser trigger types (with patterns): {len(parser_triggers_with_aliases)}")

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

# Let's check how many abilities use these missing items
print("\n" + "=" * 60)
print("USAGE COUNT OF MISSING ITEMS")
print("=" * 60)

effect_usage = defaultdict(int)
condition_usage = defaultdict(int)
trigger_usage = defaultdict(int)

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
        elif line.startswith('CONDITION:'):
            cond_part = line[10:].strip()
            match = re.match(r'(\w+)', cond_part)
            if match:
                c = match.group(1)
                if c in missing_conditions:
                    condition_usage[c] += 1
        elif line.startswith('TRIGGER:'):
            trig_part = line[8:].strip()
            match = re.match(r'(\w+)', trig_part)
            if match:
                t = match.group(1)
                if t in missing_triggers:
                    trigger_usage[t] += 1

print("\nMissing effects usage count:")
for e, count in sorted(effect_usage.items(), key=lambda x: -x[1])[:30]:
    print(f"  {e}: {count} abilities")

print("\nMissing conditions usage count:")
for c, count in sorted(condition_usage.items(), key=lambda x: -x[1])[:30]:
    print(f"  {c}: {count} abilities")

print("\nMissing triggers usage count:")
for t, count in sorted(trigger_usage.items(), key=lambda x: -x[1]):
    print(f"  {t}: {count} abilities")

# Now let's also check if these are handled by opcodes in the engine rather than the parser
# by looking at what opcodes actually exist
print("\n" + "=" * 60)
print("CHECKING OPCODES MAP")
print("=" * 60)

# Read the opcode map to see what's already defined
with open('docs/spec/opcode_map.md', 'r', encoding='utf-8') as f:
    opcode_content = f.read()

# Extract effect opcodes
effect_opcode_match = re.search(r'##\s+Opcodes\s+Mapping.*?(?=##|\Z)', opcode_content, re.DOTALL)
defined_opcodes = set()
if effect_opcode_match:
    for line in effect_opcode_match.group(0).split('\n'):
        m = re.search(r'\|\s*\d+\s+\|\s+(\w+)\s+\|', line)
        if m:
            defined_opcodes.add(m.group(1))

print(f"Defined opcodes in engine: {len(defined_opcodes)}")
print(sorted(defined_opcodes)[:30])

# Which missing items have opcodes defined?
effects_with_opcodes = missing_effects & defined_opcodes
effects_without_opcodes = missing_effects - defined_opcodes

print(f"\nMissing effects that HAVE opcodes defined: {len(effects_with_opcodes)}")
print(sorted(effects_with_opcodes))

print(f"\nMissing effects that DON'T have opcodes: {len(effects_without_opcodes)}")
print(sorted(effects_without_opcodes)[:30])
