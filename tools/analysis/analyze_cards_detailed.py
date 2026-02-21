"""
Automated card-by-card analysis tool.
Reads each card, attempts to parse, documents exact requirements.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from game.ability import AbilityParser

# Track what we find
effect_usage = {}
condition_usage = {}
trigger_usage = {}
unique_patterns = []


def analyze_card(card_no, name, ability_text):
    """Analyze a single card and return structured data."""
    result = {
        "card_no": card_no,
        "name": name,
        "ability_text": ability_text,
        "parsed_abilities": [],
        "missing_handlers": [],
        "notes": [],
    }

    try:
        abilities = AbilityParser.parse_ability_text(ability_text)

        for ability in abilities:
            parsed = {
                "trigger": ability.trigger.name if ability.trigger else None,
                "effects": [(e.effect_type.name, e.value, e.params) for e in ability.effects],
                "conditions": [(c.type.name, c.params) for c in ability.conditions],
                "costs": [(cost.type.name, cost.value) for cost in ability.costs],
            }
            result["parsed_abilities"].append(parsed)

            # Track usage
            if ability.trigger:
                trigger_usage[ability.trigger.name] = trigger_usage.get(ability.trigger.name, 0) + 1

            for effect in ability.effects:
                effect_usage[effect.effect_type.name] = effect_usage.get(effect.effect_type.name, 0) + 1

            for cond in ability.conditions:
                condition_usage[cond.type.name] = condition_usage.get(cond.type.name, 0) + 1

    except Exception as e:
        result["notes"].append(f"Parse error: {str(e)}")

    return result


def main():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = list(data.values())
    cards_with_abilities = [c for c in cards if c.get("ability", "")]

    print(f"Analyzing {len(cards_with_abilities)} cards with abilities...\n")

    # Analyze first 100 cards in detail
    analysis_results = []
    for i, card in enumerate(cards_with_abilities[:100], 1):
        result = analyze_card(card.get("card_no", f"Unknown-{i}"), card.get("name", "Unknown"), card.get("ability", ""))
        analysis_results.append(result)

        if i % 25 == 0:
            print(f"Processed {i}/100 cards...")

    # Output summary
    print(f"\n{'=' * 80}")
    print("ANALYSIS SUMMARY")
    print(f"{'=' * 80}\n")

    print("Top Effect Types:")
    for effect, count in sorted(effect_usage.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {effect}: {count}")

    print("\nTop Condition Types:")
    for cond, count in sorted(condition_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {cond}: {count}")

    print("\nTop Trigger Types:")
    for trig, count in sorted(trigger_usage.items(), key=lambda x: x[1], reverse=True):
        print(f"  {trig}: {count}")

    # Write detailed JSON report
    with open("analysis_detailed_100cards.json", "w", encoding="utf-8") as out:
        json.dump(
            {
                "total_analyzed": len(analysis_results),
                "effect_usage": effect_usage,
                "condition_usage": condition_usage,
                "trigger_usage": trigger_usage,
                "cards": analysis_results,
            },
            out,
            ensure_ascii=False,
            indent=2,
        )

    print("\nDetailed analysis written to: analysis_detailed_100cards.json")


if __name__ == "__main__":
    main()
