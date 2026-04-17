"""Audit all condition, cost, and effect types in abilities_extracted_from_cards.json"""
import json
from collections import defaultdict

# Load the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track all types
condition_types = defaultdict(list)
cost_types = defaultdict(list)
effect_actions = defaultdict(list)

def extract_condition_types(obj, path=""):
    """Recursively extract condition types"""
    if isinstance(obj, dict):
        if 'type' in obj and 'condition' in path:
            condition_types[obj['type']].append(path)
        for key, value in obj.items():
            extract_condition_types(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extract_condition_types(item, f"{path}[{i}]")

def extract_cost_types(obj, path=""):
    """Recursively extract cost types"""
    if isinstance(obj, dict):
        if 'type' in obj and 'cost' in path:
            cost_types[obj['type']].append(path)
        for key, value in obj.items():
            extract_cost_types(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extract_cost_types(item, f"{path}[{i}]")

def extract_effect_actions(obj, path=""):
    """Recursively extract effect actions"""
    if isinstance(obj, dict):
        if 'action' in obj and 'effect' in path:
            action_value = obj['action']
            if isinstance(action_value, str):
                effect_actions[action_value].append(path)
            elif isinstance(action_value, dict):
                # For nested action dicts, use a string representation as key
                action_key = str(action_value.get('action', 'nested_dict'))
                effect_actions[action_key].append(path)
        for key, value in obj.items():
            extract_effect_actions(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extract_effect_actions(item, f"{path}[{i}]")

# Process each ability
for i, ability in enumerate(data['unique_abilities']):
    # Extract conditions
    if 'effect' in ability:
        extract_condition_types(ability['effect'], f"unique_abilities[{i}].effect")
    
    # Extract costs
    if 'cost' in ability:
        extract_cost_types(ability['cost'], f"unique_abilities[{i}].cost")
    
    # Extract effects
    if 'effect' in ability:
        extract_effect_actions(ability['effect'], f"unique_abilities[{i}].effect")

# Print results
print("=" * 80)
print("CONDITION TYPES")
print("=" * 80)
for cond_type, paths in sorted(condition_types.items()):
    print(f"{cond_type}: {len(paths)} occurrences")

print("\n" + "=" * 80)
print("COST TYPES")
print("=" * 80)
for cost_type, paths in sorted(cost_types.items()):
    print(f"{cost_type}: {len(paths)} occurrences")

print("\n" + "=" * 80)
print("EFFECT ACTION TYPES")
print("=" * 80)
for action_type, paths in sorted(effect_actions.items()):
    print(f"{action_type}: {len(paths)} occurrences")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total unique condition types: {len(condition_types)}")
print(f"Total unique cost types: {len(cost_types)}")
print(f"Total unique effect action types: {len(effect_actions)}")
