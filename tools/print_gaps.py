import json
import os
import sys

# Add project root to path to import game modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.ability import AbilityParser, EffectType


def analyze_gaps(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    report = [
        "# Ability Gap Analysis\n",
        "This report identifies card abilities that are either failing to parse or require complex logic not yet implemented in the game engine.\n",
    ]

    gaps_by_reason = {}

    complex_keywords = [
        ("代わりに", "Replacement Effect (instead of)"),
        ("なるとき", "State-Triggered Effect (when becoming X)"),
        ("同時", "Simultaneous Effects"),
        ("できない", "Restriction (cannot)"),
        ("無視して", "Rule Circumvention (ignoring costs/rules)"),
        ("カード1枚につき", "Count-based Multipliers (per X cards)"),  # Check if handled
    ]

    for card_no, data in cards.items():
        text = data.get("ability", "")
        if not text:
            continue

        abilities = AbilityParser.parse_ability_text(text)

        reason = None
        if not abilities:
            reason = "Parsing Failure"
        else:
            all_meta = all(all(e.effect_type == EffectType.META_RULE for e in a.effects) for a in abilities)
            if all_meta:
                reason = "Meta-Rule / Reminder Text Only"
            else:
                for kw, label in complex_keywords:
                    if kw in text:
                        reason = f"Complex Pattern: {label}"
                        break

        if reason:
            if reason not in gaps_by_reason:
                gaps_by_reason[reason] = []
            gaps_by_reason[reason].append((card_no, text))

    for reason, items in gaps_by_reason.items():
        report.append(f"\n## {reason} ({len(items)} cards)\n")
        # Show top 5 for each
        for card_no, text in items[:5]:
            report.append(f"- **{card_no}**: {text}\n")
        if len(items) > 5:
            report.append(f"- ... and {len(items) - 5} more.\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(report)


if __name__ == "__main__":
    analyze_gaps(
        "data/cards.json",
        "C:\\Users\\trios\\.gemini\\antigravity\\brain\\977c35e4-a902-4010-b6ca-33e286754a5a\\gap_analysis.md",
    )
