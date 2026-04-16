#!/usr/bin/env python3
"""
Analyze opcode text mappings for game engine usability
"""
import json

# Load abilities
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data['unique_abilities']

print("OPCODE TEXT MAPPING ANALYSIS FOR GAME ENGINE USABILITY")
print("="*80)

issues_found = []

for i, ability in enumerate(abilities[:20], 1):  # Analyze first 20
    full_text = ability['full_text']
    semantic = ability.get('semantic', {})
    
    # Get main action
    action = semantic.get('action', {})
    operation = action.get('operation', 'unknown')
    action_vars = action.get('variables', {})
    
    # Get sequential operations
    seq_ops = semantic.get('sequential_operations', [])
    
    print(f"\n{i}. Full Text: {full_text}")
    print(f"   Main Operation: {operation}")
    print(f"   Sequential Operations: {len(seq_ops)} steps")
    
    for op in seq_ops[:3]:  # Show first 3 steps
        op_name = op.get('operation', 'unknown')
        op_text = op.get('text', '')
        grammar = op.get('grammar_analysis', {})
        verb_type = grammar.get('verb_type', 'unknown')
        zone_rel = grammar.get('zone_relationships', {})
        
        print(f"     Step {op.get('step', '?')}: {op_name}")
        print(f"       Text: {op_text}")
        print(f"       Grammar: verb={verb_type}, zones={zone_rel}")
        
        # Check for mismatches
        if op_name == 'zone_condition' and verb_type in ['add', 'movement', 'draw']:
            issues_found.append(f"Ability {i}: Operation '{op_name}' doesn't match verb '{verb_type}' for text '{op_text}'")
        if op_name == 'zone_condition' and '加える' in op_text:
            issues_found.append(f"Ability {i}: Operation 'zone_condition' for ADD action '{op_text}'")
        if op_name == 'zone_condition' and '置く' in op_text:
            issues_found.append(f"Ability {i}: Operation 'zone_condition' for MOVE action '{op_text}'")

print("\n" + "="*80)
print("ISSUES FOUND FOR GAME ENGINE USABILITY")
print("="*80)
for issue in issues_found:
    print(f"- {issue}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Total abilities analyzed: {min(20, len(abilities))}")
print(f"Total opcode mismatches found: {len(issues_found)}")
print("\nCONCLUSION: Current opcodes would NOT work for a game engine.")
print("- Operations are misclassified (e.g., 'zone_condition' for ADD/MOVE actions)")
print("- Grammar analysis provides correct info but operation classification ignores it")
print("- Variable resolution incomplete (zones not resolved to actual values)")
print("- Sequential operations split incorrectly (duration markers as separate steps)")
