import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import ConditionType, EffectType, TriggerType


def lint_pseudocode():
    json_path = "data/manual_pseudocode.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    parser = AbilityParserV2()
    errors = []

    print(f"Linting {len(data)} cards...")

    for card_id, entry in data.items():
        if "pseudocode" not in entry:
            continue

        text = entry["pseudocode"]
        try:
            abilities = parser.parse(text)
            for i, ability in enumerate(abilities):
                # Check for Trigger NONE (unless it's an empty block, which shouldn't happen)
                if ability.trigger == TriggerType.NONE:
                    errors.append(f"[{card_id}] Ability {i}: Trigger is NONE")

                # Check for effects falling back to META_RULE
                for j, eff in enumerate(ability.effects):
                    if eff.effect_type == EffectType.META_RULE and "raw_effect" in eff.params:
                        errors.append(
                            f"[{card_id}] Ability {i} Effect {j}: Unhandled Effect '{eff.params['raw_effect']}'"
                        )

                for j, cond in enumerate(ability.conditions):
                    if cond.type == ConditionType.NONE:
                        # Ignore specific heuristics
                        raw = cond.params.get("raw_cond", "")
                        if raw in ["IS_MAIN_PHASE", "MAIN_PHASE", "ON_YELL", "ON_YELL_SUCCESS"]:
                            continue

                        errors.append(f"[{card_id}] Ability {i} Condition {j}: Unhandled Condition '{raw}'")

        except Exception as e:
            errors.append(f"[{card_id}] PARSE ERROR: {e}")

    if errors:
        print(f"\nFound {len(errors)} potential issues:")
        for err in errors[:50]:  # Limit output
            print(f"  {err}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
    else:
        print("\nNo issues found!")


if __name__ == "__main__":
    lint_pseudocode()
