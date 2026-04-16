#!/usr/bin/env python3
"""
Comprehensive final check of all abilities and opcodes
"""
import json
from collections import defaultdict

# Load abilities
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['unique_abilities']

print("="*80)
print("COMPREHENSIVE FINAL CHECK - ALL ABILITIES AND OPCODES")
print("="*80)
print(f"Total abilities to analyze: {len(abilities)}")

# Statistics
total_abilities = len(abilities)
total_ops = 0
unknown_ops = 0
zone_unresolved = 0
card_unresolved = 0
icon_unresolved = 0
grammar_used = 0
grammar_ignored = 0
opcode_mismatches = 0

# Operation categories
op_categories = defaultdict(int)

# Detailed issues
issues_by_type = defaultdict(list)

for i, ability in enumerate(abilities, 1):
    full_text = ability['full_text']
    semantic = ability.get('semantic', {})
    var_mappings = ability.get('variable_mappings', {})
    
    # Check main action
    action = semantic.get('action', {})
    main_op = action.get('operation', 'unknown')
    main_vars = action.get('variables', {})
    
    # Check sequential operations
    seq_ops = semantic.get('sequential_operations', [])
    total_ops += len(seq_ops)
    
    for op in seq_ops:
        op_name = op.get('operation', 'unknown')
        op_text = op.get('text', '')
        op_vars = op.get('variables', {})
        grammar = op.get('grammar_analysis', {})
        verb_type = grammar.get('verb_type', 'unknown')
        zone_rel = grammar.get('zone_relationships', {})
        
        op_categories[op_name] += 1
        
        # Check for unknown operations
        if op_name == 'unknown':
            unknown_ops += 1
            issues_by_type['unknown_ops'].append(f"Ability {i}: '{op_text}' classified as unknown")
        
        # Check for grammar analysis usage
        if verb_type != 'unknown':
            grammar_used += 1
        else:
            grammar_ignored += 1
        
        # Check for opcode/grammar mismatches
        if op_name == 'zone_condition' and verb_type in ['add', 'movement', 'draw']:
            opcode_mismatches += 1
            issues_by_type['opcode_mismatches'].append(f"Ability {i}: '{op_name}' vs verb '{verb_type}' for '{op_text}'")
        
        # Check variable resolution in sequential ops
        for var_key, var_value in op_vars.items():
            if isinstance(var_value, str) and var_value.startswith('[') and var_value.endswith(']'):
                if 'zone' in var_key.lower():
                    zone_unresolved += 1
                elif 'icon' in var_key.lower():
                    icon_unresolved += 1
                elif 'card' in var_key.lower():
                    card_unresolved += 1
    
    # Check variable_mappings resolution
    for key, value in var_mappings.items():
        if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
            if 'zone' in key.lower():
                zone_unresolved += 1
            elif 'icon' in key.lower():
                icon_unresolved += 1
            elif 'card' in key.lower():
                card_unresolved += 1

print("\n" + "="*80)
print("STATISTICS SUMMARY")
print("="*80)
print(f"Total abilities: {total_abilities}")
print(f"Total sequential operations: {total_ops}")
print(f"Average operations per ability: {total_ops/total_abilities:.2f}")
print(f"\nOperation categories:")
for op, count in sorted(op_categories.items(), key=lambda x: -x[1]):
    print(f"  {op}: {count} ({count/total_ops*100:.1f}%)")

print("\n" + "="*80)
print("QUALITY METRICS")
print("="*80)
print(f"Unknown operations: {unknown_ops}/{total_ops} ({unknown_ops/total_ops*100:.1f}%)")
print(f"Opcode/grammar mismatches: {opcode_mismatches}")
print(f"Grammar analysis used: {grammar_used}/{total_ops} ({grammar_used/total_ops*100:.1f}%)")
print(f"Grammar analysis ignored: {grammar_ignored}/{total_ops} ({grammar_ignored/total_ops*100:.1f}%)")

print("\n" + "="*80)
print("VARIABLE RESOLUTION STATUS")
print("="*80)
print(f"Zone variables unresolved: {zone_unresolved}")
print(f"Card variables unresolved: {card_unresolved}")
print(f"Icon variables unresolved: {icon_unresolved}")

print("\n" + "="*80)
print("DETAILED ISSUES")
print("="*80)
for issue_type, issues in issues_by_type.items():
    print(f"\n{issue_type}: {len(issues)} issues")
    for issue in issues[:5]:  # Show first 5
        print(f"  - {issue}")
    if len(issues) > 5:
        print(f"  ... and {len(issues)-5} more")

print("\n" + "="*80)
print("SAMPLE ABILITY ANALYSIS (First 5)")
print("="*80)
for i, ability in enumerate(abilities[:5], 1):
    full_text = ability['full_text'][:60] + "..."
    semantic = ability.get('semantic', {})
    action = semantic.get('action', {})
    main_op = action.get('operation', 'unknown')
    seq_ops = semantic.get('sequential_operations', [])
    
    print(f"\n{i}. {full_text}")
    print(f"   Main operation: {main_op}")
    print(f"   Sequential operations: {len(seq_ops)} steps")
    for op in seq_ops[:3]:
        print(f"     - {op.get('operation', 'unknown')}: {op.get('text', '')[:40]}")

print("\n" + "="*80)
print("FINAL ASSESSMENT")
print("="*80)
if unknown_ops/total_ops < 0.1 and opcode_mismatches == 0:
    print("✓ Opcode classification: EXCELLENT")
elif unknown_ops/total_ops < 0.2:
    print("△ Opcode classification: GOOD (minor improvements needed)")
else:
    print("✗ Opcode classification: NEEDS IMPROVEMENT")

if zone_unresolved == 0:
    print("✓ Variable resolution: COMPLETE")
elif zone_unresolved < 50:
    print("△ Variable resolution: PARTIAL (zones need fixing)")
else:
    print("✗ Variable resolution: BROKEN (zones completely unresolved)")

if grammar_used/total_ops > 0.8:
    print("✓ Grammar analysis integration: EXCELLENT")
elif grammar_used/total_ops > 0.5:
    print("△ Grammar analysis integration: GOOD")
else:
    print("✗ Grammar analysis integration: NEEDS IMPROVEMENT")

print("\n" + "="*80)
print("GAME ENGINE READINESS")
print("="*80)
if unknown_ops/total_ops < 0.1 and opcode_mismatches == 0 and zone_unresolved == 0:
    print("✓ READY FOR GAME ENGINE")
else:
    print("✗ NOT READY FOR GAME ENGINE")
    if zone_unresolved > 0:
        print("  - BLOCKER: Variable resolution incomplete")
    if unknown_ops/total_ops > 0.1:
        print("  - BLOCKER: Too many unknown operations")
    if opcode_mismatches > 0:
        print("  - BLOCKER: Opcode/grammar mismatches")
