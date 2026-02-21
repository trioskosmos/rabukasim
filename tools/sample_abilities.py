"""
Sample diverse card abilities for manual pattern analysis.
Extracts representative cards from each tier and groups by characteristics.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.ability import AbilityParser


def load_cards():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        # cards.json is a dict of card_no -> card_data
        return list(data.values())


def sample_abilities():
    cards = load_cards()

    # Group by characteristics
    by_trigger = defaultdict(list)
    by_effect_count = defaultdict(list)
    unique_patterns = []

    print(f"Total cards: {len(cards)}\n")
    print("=" * 80)

    for card in cards:
        # Handle both dict and object-like access
        if isinstance(card, dict):
            ability_text = card.get("ability", "")
            card_name = card.get("name", "Unknown")
            card_no = card.get("card_no", "Unknown")
        else:
            ability_text = getattr(card, "ability", "")
            card_name = getattr(card, "name", "Unknown")
            card_no = getattr(card, "card_no", "Unknown")

        if not ability_text:
            continue

        # Parse the ability
        try:
            abilities = AbilityParser.parse_ability_text(ability_text)
            if not abilities:
                continue

            ability = abilities[0]  # First ability

            # Categorize by trigger
            trigger_name = ability.trigger.name if ability.trigger else "NONE"
            by_trigger[trigger_name].append(
                {"name": card_name, "card_no": card_no, "text": ability_text, "parsed": ability}
            )

            # Categorize by effect complexity
            effect_count = len(ability.effects)
            by_effect_count[effect_count].append(
                {"name": card_name, "card_no": card_no, "text": ability_text, "parsed": ability}
            )

        except Exception as e:
            # Track unparseable abilities
            unique_patterns.append({"name": card_name, "card_no": card_no, "text": ability_text, "error": str(e)})

    # Print samples from each category
    print("\n### SAMPLE BY TRIGGER TYPE ###\n")
    for trigger, cards_list in sorted(by_trigger.items()):
        print(f"\n## {trigger} ({len(cards_list)} cards)")
        # Sample up to 3 examples
        for card_info in cards_list[:3]:
            print(f"\n{card_info['card_no']} - {card_info['name']}")
            print(f"Text: {card_info['text'][:150]}...")
            print(f"Effects: {[e.effect_type.name for e in card_info['parsed'].effects]}")

    print("\n\n### SAMPLE BY EFFECT COMPLEXITY ###\n")
    for count in sorted(by_effect_count.keys(), reverse=True):
        if count <= 1:
            continue
        cards_list = by_effect_count[count]
        print(f"\n## {count} Effects ({len(cards_list)} cards)")
        for card_info in cards_list[:2]:
            print(f"\n{card_info['card_no']} - {card_info['name']}")
            print(f"Text: {card_info['text'][:150]}...")
            effects = card_info["parsed"].effects
            for i, eff in enumerate(effects):
                print(f"  {i + 1}. {eff.effect_type.name} (value={eff.value}, params={eff.params})")

    # Print unparseable
    if unique_patterns:
        print(f"\n\n### UNPARSEABLE / ERROR ({len(unique_patterns)} cards) ###\n")
        for card_info in unique_patterns[:5]:
            print(f"\n{card_info['card_no']} - {card_info['name']}")
            print(f"Text: {card_info['text'][:200]}")
            print(f"Error: {card_info['error']}")


if __name__ == "__main__":
    sample_abilities()
