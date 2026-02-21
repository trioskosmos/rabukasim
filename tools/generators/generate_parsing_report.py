"""
Generate a parsing verification report.
For each card, shows:
- Card ID and name
- Original ability text
- Parsed abilities (triggers, conditions, costs, effects)
- FAQ Q&A text (if any)
- Any parsing gaps/unknowns

Output: tests/parsing_verification_report.md
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.ability import Ability, AbilityParser


def ability_to_string(ability: Ability) -> str:
    """Convert parsed ability to readable string."""
    lines = []

    # Trigger
    lines.append(f"  **Trigger:** {ability.trigger.name}")

    # Costs
    if ability.costs:
        cost_strs = []
        for c in ability.costs:
            opt = " (optional)" if c.is_optional else ""
            cost_strs.append(f"{c.type.name}={c.value}{opt}")
        lines.append(f"  **Costs:** {', '.join(cost_strs)}")

    # Conditions
    if ability.conditions:
        cond_strs = []
        for c in ability.conditions:
            neg = "NOT " if c.is_negated else ""
            cond_strs.append(f"{neg}{c.type.name} {c.params}")
        lines.append(f"  **Conditions:** {', '.join(cond_strs)}")

    # Effects
    if ability.effects:
        for e in ability.effects:
            params_str = f" {e.params}" if e.params else ""
            target_str = f" → {e.target.name}" if e.target else ""
            lines.append(f"  **Effect:** {e.effect_type.name} (value={e.value}){target_str}{params_str}")

    return "\n".join(lines)


def generate_report():
    # Load cards
    with open("data/cards.json", encoding="utf-8") as f:
        cards = json.load(f)

    report_lines = [
        "# Ability Parsing Verification Report",
        "",
        "This report shows each card's ability text and how it is parsed by the game engine.",
        "Use this to verify that all abilities are correctly interpreted.",
        "",
        "---",
        "",
    ]

    stats = {"total_cards": 0, "with_abilities": 0, "parsed_ok": 0, "parse_failed": 0, "with_faq": 0}

    failed_cards = []

    for card_no, card in cards.items():
        ability_text = card.get("ability", "")
        card_type = card.get("type", "")
        faq = card.get("faq", [])

        stats["total_cards"] += 1

        if not ability_text:
            continue

        stats["with_abilities"] += 1
        if faq:
            stats["with_faq"] += 1

        # Parse abilities
        abilities = AbilityParser.parse_ability_text(ability_text)

        # Build card section
        report_lines.append(f"## {card_no}: {card.get('name', 'Unknown')}")
        report_lines.append(f"Type: {card_type}")
        report_lines.append("")

        # Original text
        report_lines.append("### Original Ability Text")
        report_lines.append("```")
        report_lines.append(ability_text.replace("\n", "\n"))
        report_lines.append("```")
        report_lines.append("")

        # Parsed result
        report_lines.append("### Parsed Abilities")
        if abilities:
            stats["parsed_ok"] += 1
            for i, abi in enumerate(abilities, 1):
                report_lines.append(f"**Ability {i}:**")
                report_lines.append(ability_to_string(abi))
                report_lines.append("")
        else:
            stats["parse_failed"] += 1
            report_lines.append("⚠️ **PARSE FAILED** - No abilities extracted")
            report_lines.append("")
            failed_cards.append((card_no, card.get("name", ""), ability_text[:100]))

        # FAQ
        if faq:
            report_lines.append("### FAQ")
            for q in faq:
                report_lines.append(f"**Q:** {q.get('question', '')[:200]}...")
                report_lines.append(f"**A:** {q.get('answer', '')[:200]}...")
                report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

    # Summary at top
    summary = [
        "# Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total cards | {stats['total_cards']} |",
        f"| Cards with abilities | {stats['with_abilities']} |",
        f"| Successfully parsed | {stats['parsed_ok']} |",
        f"| Parse failed | {stats['parse_failed']} |",
        f"| Cards with FAQ | {stats['with_faq']} |",
        f"| Parse rate | {stats['parsed_ok'] / max(1, stats['with_abilities']) * 100:.1f}% |",
        "",
        "---",
        "",
    ]

    # Write report
    with open("tests/parsing_verification_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary + report_lines))

    # Write failed cards separately
    with open("tests/parsing_failures.txt", "w", encoding="utf-8") as f:
        f.write("# Cards that failed to parse\n\n")
        for card_no, name, text in failed_cards:
            f.write(f"{card_no}: {name}\n")
            f.write(f"  Text: {text}...\n\n")

    print("Report generated: tests/parsing_verification_report.md")
    print("Parse failures: tests/parsing_failures.txt")
    print("\nStats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    generate_report()
