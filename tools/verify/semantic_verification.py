"""
Semantic Verification Tool

Generates a report showing card text alongside parsed effects for manual review.
Groups cards by effect type so you can verify similar abilities are parsed consistently.

Output: tests/semantic_verification_report.md
"""

import json
import os
import sys
from collections import defaultdict

sys.path.append(os.getcwd())

from engine.models.ability import Ability
from compiler.parser_v2 import parse_ability_text


def generate_semantic_report():
    with open("data/cards.json", encoding="utf-8") as f:
        cards = json.load(f)

    # Group by effect type
    effect_groups = defaultdict(list)

    for card_no, card in cards.items():
        ability_text = card.get("ability", "")
        if not ability_text:
            continue

        abilities = parse_ability_text(ability_text)
        if not abilities:
            continue

        for ability in abilities:
            for effect in ability.effects:
                effect_groups[effect.effect_type.name].append(
                    {
                        "card_no": card_no,
                        "name": card.get("name", "Unknown"),
                        "text": ability_text,
                        "trigger": ability.trigger.name,
                        "conditions": [f"{c.type.name} {c.params}" for c in ability.conditions],
                        "effect_value": effect.value,
                        "effect_target": effect.target.name if effect.target else None,
                        "effect_params": effect.params,
                    }
                )

    # Generate report
    lines = [
        "# Semantic Verification Report",
        "",
        "Cards grouped by effect type. Review each group to verify parsed effects match card text.",
        "",
    ]

    # Summary table
    lines.append("## Effect Type Summary")
    lines.append("| Effect Type | Count | Sample Card |")
    lines.append("|-------------|-------|-------------|")
    for etype in sorted(effect_groups.keys(), key=lambda k: -len(effect_groups[k])):
        count = len(effect_groups[etype])
        sample = effect_groups[etype][0]["name"] if effect_groups[etype] else "-"
        lines.append(f"| {etype} | {count} | {sample} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed sections - show first 5 cards per effect type
    for etype in sorted(effect_groups.keys(), key=lambda k: -len(effect_groups[k])):
        cards_list = effect_groups[etype]
        lines.append(f"## {etype} ({len(cards_list)} cards)")
        lines.append("")

        for card_info in cards_list[:5]:  # First 5 samples
            lines.append(f"### {card_info['card_no']}: {card_info['name']}")
            lines.append(f"**Trigger:** {card_info['trigger']}")
            if card_info["conditions"]:
                lines.append(f"**Conditions:** {', '.join(card_info['conditions'])}")
            lines.append(f"**Effect Value:** {card_info['effect_value']}")
            if card_info["effect_target"]:
                lines.append(f"**Target:** {card_info['effect_target']}")
            if card_info["effect_params"]:
                lines.append(f"**Params:** `{card_info['effect_params']}`")
            lines.append("")
            lines.append("**Original Text:**")
            lines.append("```")
            lines.append(card_info["text"][:200] + ("..." if len(card_info["text"]) > 200 else ""))
            lines.append("```")
            lines.append("")

        if len(cards_list) > 5:
            lines.append(f"*...and {len(cards_list) - 5} more cards with this effect*")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Write report
    with open("tests/semantic_verification_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Report generated: tests/semantic_verification_report.md")
    print(f"\nEffect types found: {len(effect_groups)}")
    for etype in sorted(effect_groups.keys(), key=lambda k: -len(effect_groups[k]))[:10]:
        print(f"  {etype}: {len(effect_groups[etype])} cards")


if __name__ == "__main__":
    generate_semantic_report()
