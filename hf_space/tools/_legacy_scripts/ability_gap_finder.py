import json
import os
import sys

# Add project root to path to import game modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.ability import AbilityParser, EffectType


def find_gaps(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    gaps = []

    # Keywords that suggest complex logic we might be missing
    complex_keywords = [
        "代わりに",  # "Instead of" (Replacement effects)
        "なるとき",  # "When becoming X" (State transitions)
        "同時",  # "Simultaneously"
        "選ばれ",  # "Chosen/Selected" (Passive/Active choice complexity)
        "でない",  # "Is not" (Negation logic gaps)
        "ではない",
        "上限",  # "Limit"
        "追加で",  # "Additionally"
        "できない",  # "Cannot" (Rule overrides)
        "無視して",  # "Ignoring" (Cost/Rule circumvention)
    ]

    for card_no, data in cards.items():
        text = data.get("ability", "")
        if not text:
            continue

        abilities = AbilityParser.parse_ability_text(text)

        # 1. Parsing Failures (Empty results for non-empty text)
        if not abilities:
            gaps.append({"no": card_no, "text": text, "reason": "Parsing Failure (No abilities extracted)"})
            continue

        # 2. Meta-Rule Gaps (Only meta-rules found for descriptive text)
        all_meta = all(all(e.effect_type == EffectType.META_RULE for e in a.effects) for a in abilities)
        if all_meta:
            gaps.append({"no": card_no, "text": text, "reason": "Meta-Rule Only (Engine logic likely missing)"})
            continue

        # 3. Keyword Suspicions (Parsed but contains complex keywords)
        found_keywords = []
        for kw in complex_keywords:
            if kw in text:
                # Check if the keyword is actually handled by the parsed effects
                handled = False
                for ability in abilities:
                    for effect in ability.effects:
                        # Cluster 4: Replacement
                        if kw == "代わりに" and effect.effect_type == EffectType.REPLACE_EFFECT:
                            handled = True
                        # Cluster 3: Restrictions
                        elif kw == "できない" and effect.effect_type == EffectType.RESTRICTION:
                            handled = True
                        elif kw == "できない" and effect.effect_type == EffectType.IMMUNITY:  # Some 'cannot be chosen'
                            handled = True

                if not handled:
                    found_keywords.append(kw)

        if found_keywords:
            gaps.append({"no": card_no, "text": text, "reason": f"Complex Keyword Match: {', '.join(found_keywords)}"})

    return gaps


if __name__ == "__main__":
    json_path = "data/cards.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        sys.exit(1)

    gaps = find_gaps(json_path)

    # Categorize and print
    report = {}
    for g in gaps:
        reason = g["reason"]
        if reason not in report:
            report[reason] = []
        report[reason].append(g)

    print(f"Total gaps found: {len(gaps)}")
    for reason, items in report.items():
        print(f"\n--- {reason} ({len(items)} cards) ---")
        # Print first 5 examples
        for item in items[:5]:
            print(f"[{item['no']}] {item['text']}")
        if len(items) > 5:
            print(f"... and {len(items) - 5} more")

    # Output to file for permanent record
    with open("ability_gap_report.txt", "w", encoding="utf-8") as f:
        f.write("UNCATEGORIZED LOGIC GAPS REPORT\n")
        f.write("=============================\n")
        for reason, items in report.items():
            f.write(f"\n{reason}:\n")
            for item in items:
                f.write(f"- [{item['no']}] {item['text']}\n")
