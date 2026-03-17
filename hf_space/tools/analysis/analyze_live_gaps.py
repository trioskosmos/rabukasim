"""
Analyze cards with 'live' keywords missing from parsed logic.
Identifies common phrases being missed by the parser.
"""

import json
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.ability import AbilityParser


def analyze_live_gaps():
    with open("data/cards.json", encoding="utf-8") as f:
        cards = json.load(f)

    missing_patterns = []

    for card_no, card in cards.items():
        text = card.get("ability", "")
        if "ライブ" not in text:
            continue

        abilities = AbilityParser.parse_ability_text(text)

        # Look for live-related triggers/effects
        has_live = False
        for ab in abilities:
            if "LIVE" in ab.trigger.name:
                has_live = True
            for eff in ab.effects:
                if "LIVE" in eff.effect_type.name:
                    has_live = True
                if "live" in str(eff.params).lower():
                    has_live = True

        if not has_live:
            # Found a gap! Capture the surrounding context of 'ライブ'
            # Find all occurrences of ライブ and surrounding text
            matches = re.findall(r"([^。]{0,15}ライブ[^。]{0,15})", text)
            for m in matches:
                missing_patterns.append(m)

    # Count frequency of missing phrases
    from collections import Counter

    counts = Counter(missing_patterns)

    print("=== COMMON MISSING 'LIVE' PHRASES ===")
    for phrase, count in counts.most_common(20):
        print(f"{count:3}: {phrase}")


if __name__ == "__main__":
    analyze_live_gaps()
