"""Simple audit of condition, cost, and effect types"""
import json

# Load the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Collect type statistics
condition_stats = {}
cost_stats = {}
effect_stats = {}

def collect_types(obj, type_dict, key='type'):
    if isinstance(obj, dict):
        if key in obj:
            t = obj[key]
            # Convert dict to string representation for dict actions
            if isinstance(t, dict):
                t = str(t)
            if t not in type_dict:
                type_dict[t] = {'count': 0, 'examples': []}
            type_dict[t]['count'] += 1
            if len(type_dict[t]['examples']) < 3:
                type_dict[t]['examples'].append(obj)
        for v in obj.values():
            collect_types(v, type_dict, key)
    elif isinstance(obj, list):
        for item in obj:
            collect_types(item, type_dict, key)

# Process each ability
for ability in data['unique_abilities']:
    if 'effect' in ability:
        collect_types(ability['effect'], condition_stats, 'type')
        collect_types(ability['effect'], effect_stats, 'action')
    if 'cost' in ability:
        collect_types(ability['cost'], cost_stats, 'type')

print("=" * 80)
print("CONDITION TYPES (showing fields)")
print("=" * 80)
for t, stats in sorted(condition_stats.items()):
    print(f"\n{t} ({stats['count']} occurrences)")
    if stats['examples']:
        print(f"  Fields: {list(stats['examples'][0].keys())}")

print("\n" + "=" * 80)
print("COST TYPES (showing fields)")
print("=" * 80)
for t, stats in sorted(cost_stats.items()):
    print(f"\n{t} ({stats['count']} occurrences)")
    if stats['examples']:
        print(f"  Fields: {list(stats['examples'][0].keys())}")

print("\n" + "=" * 80)
print("EFFECT ACTION TYPES (showing fields)")
print("=" * 80)
for t, stats in sorted(effect_stats.items()):
    print(f"\n{t} ({stats['count']} occurrences)")
    if stats['examples']:
        print(f"  Fields: {list(stats['examples'][0].keys())}")
