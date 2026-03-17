"""
Analyze which parsed abilities are missing implementation in game_state.py
"""

import json
import os
import re
from collections import Counter

# Load parsed abilities
with open("docs/full_ability_coverage.json", "r", encoding="utf-8") as f:
    coverage = json.load(f)

# Collect all parsed effect types, conditions, and costs
all_effects = []
all_conditions = []
all_costs = []
all_triggers = []

for card in coverage["with_ability"]:
    if card["parsed"]:
        all_effects.extend(card["parsed"]["effects"])
        all_conditions.extend(card["parsed"]["conditions"])
        all_costs.extend(card["parsed"]["costs"])
        all_triggers.extend(card["parsed"]["triggers"])

effect_counts = Counter(all_effects)
condition_counts = Counter(all_conditions)
cost_counts = Counter(all_costs)
trigger_counts = Counter(all_triggers)

# Now read game engine files to find implemented effects
engine_path = "engine/game"
implementation_code = ""

for root, dirs, files in os.walk(engine_path):
    for file in files:
        if file.endswith(".py"):
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                implementation_code += f.read() + "\n"

# Find all EffectType checks in implementation code
implemented_effects = set(re.findall(r"EffectType\.(\w+)", implementation_code))
implemented_conditions = set(re.findall(r"ConditionType\.(\w+)", implementation_code))
implemented_costs = set(re.findall(r"AbilityCostType\.(\w+)", implementation_code))

# Compare
parsed_effects = set(effect_counts.keys())
parsed_conditions = set(condition_counts.keys())
parsed_costs = set(cost_counts.keys())

missing_effects = parsed_effects - implemented_effects
missing_conditions = parsed_conditions - implemented_conditions
missing_costs = parsed_costs - implemented_costs

print("=" * 80)
print("ABILITY IMPLEMENTATION GAP ANALYSIS")
print("=" * 80)

print("\n## EFFECTS")
print(f"Total Unique Effects Parsed: {len(parsed_effects)}")
print(f"Effects Implemented in game_state.py: {len(implemented_effects)}")
print(f"Missing Implementations: {len(missing_effects)}")

if missing_effects:
    print("\n### Missing Effect Implementations:")
    for effect in sorted(missing_effects):
        count = effect_counts[effect]
        print(f"  - {effect:30s} (used in {count:4d} abilities)")
else:
    print("\n✓ All effects are implemented!")

print("\n## CONDITIONS")
print(f"Total Unique Conditions Parsed: {len(parsed_conditions)}")
print(f"Conditions Implemented in game_state.py: {len(implemented_conditions)}")
print(f"Missing Implementations: {len(missing_conditions)}")

if missing_conditions:
    print("\n### Missing Condition Implementations:")
    for cond in sorted(missing_conditions):
        count = condition_counts[cond]
        print(f"  - {cond:30s} (used in {count:4d} abilities)")
else:
    print("\n✓ All conditions are implemented!")

print("\n## COSTS")
print(f"Total Unique Costs Parsed: {len(parsed_costs)}")
print(f"Costs Implemented in game_state.py: {len(implemented_costs)}")
print(f"Missing Implementations: {len(missing_costs)}")

if missing_costs:
    print("\n### Missing Cost Implementations:")
    for cost in sorted(missing_costs):
        count = cost_counts[cost]
        print(f"  - {cost:30s} (used in {count:4d} abilities)")
else:
    print("\n✓ All costs are implemented!")

print("\n## SUMMARY")
print(f"Total Missing Implementations: {len(missing_effects) + len(missing_conditions) + len(missing_costs)}")

# Save detailed report
report = {
    "effects": {
        "parsed": list(parsed_effects),
        "implemented": list(implemented_effects),
        "missing": list(missing_effects),
        "counts": dict(effect_counts),
    },
    "conditions": {
        "parsed": list(parsed_conditions),
        "implemented": list(implemented_conditions),
        "missing": list(missing_conditions),
        "counts": dict(condition_counts),
    },
    "costs": {
        "parsed": list(parsed_costs),
        "implemented": list(implemented_costs),
        "missing": list(missing_costs),
        "counts": dict(cost_counts),
    },
}

with open("docs/implementation_gaps.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("\nDetailed report saved to: docs/implementation_gaps.json")
