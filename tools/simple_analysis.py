#!/usr/bin/env python3
"""
Simple analysis of abilities to identify key issues
"""
import json
import random

# Load abilities
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['unique_abilities']

# Sort by full_text length
sorted_by_length = sorted(abilities, key=lambda x: len(x['full_text']), reverse=True)

# Get samples
longest = sorted_by_length[:10]
shortest = sorted_by_length[-10:]
middle_start = len(sorted_by_length) // 2
middle_abilities = sorted_by_length[middle_start:middle_start+100]
random_abilities = random.sample(middle_abilities, min(10, len(middle_abilities)))

# Track issues
total_unknown_ops = 0
total_unresolved_vars = 0
total_zone_unresolved = 0
total_card_unresolved = 0
parentheses_issues = 0

def analyze_ability(ability, label):
    global total_unknown_ops, total_unresolved_vars, total_zone_unresolved, total_card_unresolved, parentheses_issues
    
    issues = []
    
    # Check variable resolution
    var_mappings = ability.get('variable_mappings', {})
    if '[zone]' not in var_mappings or isinstance(var_mappings.get('[zone]'), str) and var_mappings['[zone]'] == '[zone]':
        issues.append("Zone not resolved")
        total_zone_unresolved += 1
    
    if '[card]' not in var_mappings or isinstance(var_mappings.get('[card]'), str) and var_mappings['[card]'] == '[card]':
        issues.append("Card not resolved")
        total_card_unresolved += 1
    
    # Check sequential operations
    semantic = ability.get('semantic', {})
    seq_ops = semantic.get('sequential_operations', [])
    
    unknown_count = 0
    unresolved_count = 0
    
    for op in seq_ops:
        operation = op.get('operation', 'unknown')
        step = op.get('step', '?')
        text = op.get('text', '')
        
        if operation == 'unknown':
            unknown_count += 1
            total_unknown_ops += 1
        
        # Check for parentheses issues
        if text.strip() in ['(', ')', 'その後', '。', '、']:
            issues.append(f"Step {step}: Invalid fragment '{text}'")
            parentheses_issues += 1
        
        # Check variable resolution
        variables = op.get('variables', {})
        for var_key, var_value in variables.items():
            if isinstance(var_value, str) and var_value.startswith('[') and var_value.endswith(']'):
                unresolved_count += 1
                total_unresolved_vars += 1
    
    if unknown_count > 0:
        issues.append(f"{unknown_count} unknown operations")
    
    if unresolved_count > 0:
        issues.append(f"{unresolved_count} unresolved variables")
    
    return issues

print("ABILITY ANALYSIS REPORT")
print("="*80)

# Analyze all samples
all_samples = [('LONGEST', longest), ('SHORTEST', shortest), ('RANDOM', random_abilities)]

for category, sample_abilities in all_samples:
    print(f"\n{category} ABILITIES ({len(sample_abilities)} total)")
    print("-"*80)
    
    for i, ability in enumerate(sample_abilities, 1):
        issues = analyze_ability(ability, f"{category}-{i}")
        print(f"{i}. {ability['full_text'][:60]}...")
        if issues:
            print(f"   Issues: {', '.join(issues)}")
        else:
            print(f"   OK")

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"Total abilities analyzed: {len(longest) + len(shortest) + len(random_abilities)}")
print(f"Zone variables unresolved: {total_zone_unresolved}")
print(f"Card variables unresolved: {total_card_unresolved}")
print(f"Total unknown operations: {total_unknown_ops}")
print(f"Total unresolved variables: {total_unresolved_vars}")
print(f"Parentheses/parsing issues: {parentheses_issues}")

print("\n" + "="*80)
print("KEY ISSUES IDENTIFIED")
print("="*80)
print("1. ZONE VARIABLE NOT RESOLVED - Phase 1 incomplete")
print("2. CARD VARIABLE NOT RESOLVED - Phase 1 incomplete")
print("3. MANY UNKNOWN OPERATIONS - Phase 2 incomplete")
print("4. PARENTHESES PARSING ISSUES - Complex abilities split incorrectly")
print("5. GRAMMAR ANALYSIS NOT USED - Phase 3 not integrated into classification")
