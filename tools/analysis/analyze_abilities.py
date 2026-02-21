"""
Analyze ability coverage across all cards.
Counts effect types and condition types to prioritize testing.
"""

import json
import os
import sys
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.parser import AbilityParser


def analyze_abilities():
    # Load card data
    with open("data/cards_compiled.json", encoding="utf-8") as f:
        data = json.load(f)

    cards = {}
    if "member_db" in data:
        cards.update(data["member_db"])
    if "live_db" in data:
        cards.update(data["live_db"])

    effect_counter = Counter()
    trigger_counter = Counter()
    condition_counter = Counter()
    parsed_count = 0
    failed_count = 0
    cards_with_abilities = 0

    for card_id, card in cards.items():
        # Check for compiled abilities first
        abilities_data = card.get("abilities", [])
        if not abilities_data:
            continue

        cards_with_abilities += 1
        # Convert dict abilities back to objects for analysis if needed,
        # or just analyze the dict structure.
        # But analyze_abilities uses AbilityParser.parse_ability_text
        # Let's use the raw ability_text if available.
        ability_text = card.get("ability_text", "")
        if not ability_text:
            continue

        abilities = AbilityParser.parse_ability_text(ability_text)

        if not abilities:
            failed_count += 1
            continue

        parsed_count += 1

        for ability in abilities:
            trigger_counter[ability.trigger.name] += 1

            for cond in ability.conditions:
                condition_counter[cond.type.name] += 1

            for effect in ability.effects:
                effect_counter[effect.effect_type.name] += 1

    print("=" * 60)
    print("ABILITY COVERAGE ANALYSIS")
    print("=" * 60)
    print(f"\nCards with abilities: {cards_with_abilities}")
    print(f"Successfully parsed: {parsed_count}")
    print(f"Failed to parse: {failed_count}")
    print(f"Parse rate: {parsed_count / cards_with_abilities * 100:.1f}%")

    print("\n--- EFFECT TYPES (by frequency) ---")
    for effect, count in effect_counter.most_common(20):
        print(f"  {effect:25} {count:4} cards")

    print("\n--- TRIGGER TYPES ---")
    for trigger, count in trigger_counter.most_common():
        print(f"  {trigger:25} {count:4} abilities")

    print("\n--- CONDITION TYPES ---")
    for cond, count in condition_counter.most_common():
        print(f"  {cond:25} {count:4} conditions")

    return effect_counter, trigger_counter, condition_counter


if __name__ == "__main__":
    analyze_abilities()
