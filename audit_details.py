"""Detailed audit of condition, cost, and effect types with examples"""
import json

# Load the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track types with examples
condition_examples = {}
cost_examples = {}
effect_examples = {}

def extract_with_examples(obj, path="", examples_dict=None, type_key='type', action_key='action'):
    """Recursively extract types with examples"""
    if isinstance(obj, dict):
        if type_key in obj and examples_dict is not None:
            type_value = obj[type_key]
            if type_value not in examples_dict:
                examples_dict[type_value] = []
            examples_dict[type_value].append({
                'path': path,
                'data': obj,
                'full_text': data['unique_abilities'][int(path.split('[')[1].split(']')[0])].get('full_text', '') if 'unique_abilities' in path else ''
            })
        elif action_key in obj and examples_dict is not None:
            action_value = obj[action_key]
            if isinstance(action_value, str):
                if action_value not in examples_dict:
                    examples_dict[action_value] = []
                examples_dict[action_value].append({
                    'path': path,
                    'data': obj,
                    'full_text': data['unique_abilities'][int(path.split('[')[1].split(']')[0])].get('full_text', '') if 'unique_abilities' in path else ''
                })
            elif isinstance(action_value, dict) and 'action' in action_value:
                nested_action = action_value['action']
                if isinstance(nested_action, str):
                    if nested_action not in examples_dict:
                        examples_dict[nested_action] = []
                    examples_dict[nested_action].append({
                        'path': path,
                        'data': obj,
                        'full_text': data['unique_abilities'][int(path.split('[')[1].split(']')[0])].get('full_text', '') if 'unique_abilities' in path else ''
                    })
        for key, value in obj.items():
            extract_with_examples(value, f"{path}.{key}" if path else key, examples_dict, type_key, action_key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extract_with_examples(item, f"{path}[{i}]", examples_dict, type_key, action_key)

# Process each ability
for i, ability in enumerate(data['unique_abilities']):
    # Extract conditions
    if 'effect' in ability:
        extract_with_examples(ability['effect'], f"unique_abilities[{i}].effect", condition_examples, 'type', None)
    
    # Extract costs
    if 'cost' in ability:
        extract_with_examples(ability['cost'], f"unique_abilities[{i}].cost", cost_examples, 'type', None)
    
    # Extract effects
    if 'effect' in ability:
        extract_with_examples(ability['effect'], f"unique_abilities[{i}].effect", effect_examples, None, 'action')

# Print detailed audit
print("=" * 80)
print("CONDITION TYPES AUDIT")
print("=" * 80)
for cond_type, examples in sorted(condition_examples.items()):
    print(f"\n{cond_type} ({len(examples)} occurrences):")
    # Show first example with fields
    if examples:
        example = examples[0]['data']
        print(f"  Example fields: {list(example.keys())}")
        print(f"  Example data: {json.dumps(example, ensure_ascii=False, indent=2)[:200]}...")
        print(f"  Full text: {examples[0]['full_text'][:150]}...")

print("\n" + "=" * 80)
print("COST TYPES AUDIT")
print("=" * 80)
for cost_type, examples in sorted(cost_examples.items()):
    print(f"\n{cost_type} ({len(examples)} occurrences):")
    # Show first example with fields
    if examples:
        example = examples[0]['data']
        print(f"  Example fields: {list(example.keys())}")
        print(f"  Example data: {json.dumps(example, ensure_ascii=False, indent=2)[:200]}...")
        print(f"  Full text: {examples[0]['full_text'][:150]}...")

print("\n" + "=" * 80)
print("EFFECT ACTION TYPES AUDIT")
print("=" * 80)
for action_type, examples in sorted(effect_examples.items()):
    print(f"\n{action_type} ({len(examples)} occurrences):")
    # Show first example with fields
    if examples:
        example = examples[0]['data']
        print(f"  Example fields: {list(example.keys())}")
        print(f"  Example data: {json.dumps(example, ensure_ascii=False, indent=2)[:200]}...")
        print(f"  Full text: {examples[0]['full_text'][:150]}...")
