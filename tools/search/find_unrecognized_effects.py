"""
Identify effect names that are falling back to META_RULE.
This analyzes the raw_effect param stored in compiled abilities.
"""

import json
from collections import Counter

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    db = json.load(f)

print("=== UNRECOGNIZED EFFECT NAMES ===")
raw_effects = Counter()

for card_id, card in db["member_db"].items():
    for ab in card.get("abilities", []):
        for eff in ab.get("effects", []):
            if eff.get("effect_type") == "META_RULE":
                raw_effect = eff.get("params", {}).get("raw_effect", "UNKNOWN")
                raw_effects[raw_effect] += 1

for card_id, card in db["live_db"].items():
    for ab in card.get("abilities", []):
        for eff in ab.get("effects", []):
            if eff.get("effect_type") == "META_RULE":
                raw_effect = eff.get("params", {}).get("raw_effect", "UNKNOWN")
                raw_effects[raw_effect] += 1

print(f"\nTotal unique unrecognized effect names: {len(raw_effects)}")
print(f"Total occurrences: {sum(raw_effects.values())}")
print("\nTop 30 unrecognized effect names:")
for name, count in raw_effects.most_common(30):
    print(f"  {name}: {count}")
