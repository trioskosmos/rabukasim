"""
Analyze cards with 'deck' and 'opponent' keywords missing from parsed logic.
"""

import json
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.ability import AbilityParser


def analyze_gaps(keyword, concept_pattern):
    with open("data/cards.json", encoding="utf-8") as f:
        cards = json.load(f)

    missing_phrases = []

    for card_no, card in cards.items():
        text = card.get("ability", "")
        if keyword not in text:
            continue

        abilities = AbilityParser.parse_ability_text(text)

        # Build long parsed string to check for concept presence
        parsed_str = ""
        for ab in abilities:
            parsed_str += f"[{ab.trigger.name}] "
            for eff in ab.effects:
                parsed_str += f"{eff.effect_type.name} {eff.target.name if eff.target else ''} {eff.params} "

        if not re.search(concept_pattern, parsed_str, re.IGNORECASE):
            # Gap!
            matches = re.findall(rf"([^。]{{0,15}}{keyword}[^。]{{0,15}})", text)
            for m in matches:
                missing_phrases.append(m)

    from collections import Counter

    counts = Counter(missing_phrases)
    print(f"\n=== COMMON MISSING '{keyword.upper()}' PHRASES ===")
    for phrase, count in counts.most_common(15):
        print(f"{count:3}: {phrase}")


if __name__ == "__main__":
    analyze_gaps("デッキ", "DECK")
    analyze_gaps("相手", "OPPONENT")
