"""Analyze all semantic action types in abilities_extracted_from_cards.json."""

import json
from collections import Counter

with open("data/abilities_extracted_from_cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)

actions_counter = Counter()
cost_types_counter = Counter()
condition_types_counter = Counter()

for ability in data["unique_abilities"]:
    # Count effect actions
    for action in ability.get("effect", {}).get("actions", []):
        if isinstance(action, str):
            action_name = action
        elif isinstance(action, dict):
            action_name = action.get("action", "")
            if isinstance(action_name, dict):
                action_name = "unknown_dict"
        else:
            action_name = "unknown"
        actions_counter[action_name] += 1
    
    # Count cost types
    if ability.get("cost"):
        cost_type = ability["cost"].get("type", "unknown")
        cost_types_counter[cost_type] += 1
    
    # Count condition types
    if ability.get("effect", {}).get("condition"):
        cond_type = ability["effect"]["condition"].get("type", "unknown")
        condition_types_counter[cond_type] += 1

print("=== SEMANTIC ACTION TYPES (effect.actions) ===")
for action, count in actions_counter.most_common():
    print(f"{action}: {count}")

print("\n=== COST TYPES ===")
for cost_type, count in cost_types_counter.most_common():
    print(f"{cost_type}: {count}")

print("\n=== CONDITION TYPES ===")
for cond_type, count in condition_types_counter.most_common():
    print(f"{cond_type}: {count}")
