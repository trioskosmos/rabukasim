import json
import os
import sys
from collections import Counter

# Add project root to sys.path
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import EffectType


def analyze_meta_rules():
    json_path = "data/manual_pseudocode.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    parser = AbilityParserV2()
    meta_rules = []

    for card_id, entry in data.items():
        if "pseudocode" not in entry:
            continue

        try:
            abilities = parser.parse(entry["pseudocode"])
            for ability in abilities:
                for eff in ability.effects:
                    if eff.effect_type == EffectType.META_RULE and "raw_effect" in eff.params:
                        meta_rules.append(eff.params["raw_effect"])
        except:
            continue

    counts = Counter(meta_rules)
    print("\n--- Unique META_RULE effects (unhandled by engine) ---")
    for name, count in counts.most_common():
        print(f"{name: <30} : {count} occurrences")


if __name__ == "__main__":
    analyze_meta_rules()
