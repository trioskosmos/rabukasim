#!/usr/bin/env python3
"""
Analyze abilities to find longest, shortest, and random samples
"""
import json
import random

# Load abilities
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Sort by full_text length
sorted_by_length = sorted(abilities, key=lambda x: len(x['full_text']), reverse=True)

# Get top 10 longest
longest = sorted_by_length[:10]

# Get top 10 shortest
shortest = sorted_by_length[-10:]

# Get 10 random from the middle
middle_start = len(sorted_by_length) // 2
middle_abilities = sorted_by_length[middle_start:middle_start+100]
random_abilities = random.sample(middle_abilities, min(10, len(middle_abilities)))

# Analysis function
def analyze_ability(ability, index):
    print(f"\n{'='*80}")
    print(f"ABILITY #{index}")
    print(f"{'='*80}")
    print(f"Full Text: {ability['full_text']}")
    print(f"Template: {ability['combined_template']}")
    print(f"Card Count: {ability['card_count']}")
    print(f"\nVariable Mappings:")
    for key, value in ability.get('variable_mappings', {}).items():
        print(f"  {key}: {value}")
    
    print(f"\nSemantic Analysis:")
    semantic = ability.get('semantic', {})
    
    # Timing
    if semantic.get('timing'):
        print(f"  Timing: {semantic['timing']}")
    
    # Cost
    if semantic.get('cost'):
        print(f"  Cost: {semantic['cost']}")
    
    # Action
    if semantic.get('action'):
        print(f"  Main Action: {semantic['action']}")
    
    # Sequential Operations
    seq_ops = semantic.get('sequential_operations', [])
    if seq_ops:
        print(f"  Sequential Operations ({len(seq_ops)} steps):")
        for op in seq_ops:
            step = op.get('step', '?')
            operation = op.get('operation', 'unknown')
            print(f"    Step {step}: {operation}")
            print(f"      Text: {op.get('text', 'N/A')}")
            print(f"      Variables: {op.get('variables', {})}")
            if 'grammar_analysis' in op:
                ga = op['grammar_analysis']
                print(f"      Grammar: zone_rel={ga['zone_relationships']}, verb_type={ga['verb_type']}")
    
    # Conditions
    conditions = semantic.get('conditions', [])
    if conditions:
        print(f"  Conditions: {conditions}")
    
    # Issues
    print(f"\nISSUES:")
    issues = []
    
    # Check variable resolution
    var_mappings = ability.get('variable_mappings', {})
    if '[zone]' not in var_mappings or isinstance(var_mappings.get('[zone]'), str) and var_mappings['[zone]'] == '[zone]':
        issues.append("Zone variable not resolved")
    
    if '[card]' not in var_mappings or isinstance(var_mappings.get('[card]'), str) and var_mappings['[card]'] == '[card]':
        issues.append("Card variable not resolved")
    
    # Check sequential operations
    for op in seq_ops:
        operation = op.get('operation', 'unknown')
        step = op.get('step', '?')
        if operation == 'unknown':
            issues.append(f"Step {step}: Unknown operation")
        variables = op.get('variables', {})
        for var_key, var_value in variables.items():
            if isinstance(var_value, str) and var_value.startswith('[') and var_value.endswith(']'):
                issues.append(f"Step {step}: Variable {var_key} not resolved ({var_value})")
    
    if not issues:
        print("  None detected")
    else:
        for issue in issues:
            print(f"  - {issue}")

print("TOP 10 LONGEST ABILITIES")
print("="*80)
for i, ability in enumerate(longest, 1):
    analyze_ability(ability, f"LONG-{i}")

print("\n\nTOP 10 SHORTEST ABILITIES")
print("="*80)
for i, ability in enumerate(shortest, 1):
    analyze_ability(ability, f"SHORT-{i}")

print("\n\nRANDOM 10 ABILITIES")
print("="*80)
for i, ability in enumerate(random_abilities, 1):
    analyze_ability(ability, f"RAND-{i}")

print("\n\nSUMMARY")
print("="*80)
print(f"Total abilities analyzed: {len(longest) + len(shortest) + len(random_abilities)}")
print(f"Longest ability length: {len(longest[0]['full_text'])} characters")
print(f"Shortest ability length: {len(shortest[-1]['full_text'])} characters")
