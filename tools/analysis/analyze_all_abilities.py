"""
Comprehensive Card Ability Analysis
Generates a report of ALL cards with abilities/FAQs and their implementation status.
"""

import json
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.parser import AbilityParser


def analyze_all_cards():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    cards = {}
    if "member_db" in db:
        cards.update(db["member_db"])
    if "live_db" in db:
        cards.update(db["live_db"])

    results = {"with_ability": [], "with_faq": [], "vanilla": [], "parsing_errors": []}

    for card_id, card_data in cards.items():
        card_type = card_data.get("type", "")

        # Skip energy cards
        if card_type == "エネルギー":
            continue

        has_ability = bool(card_data.get("ability_text"))
        has_faq = bool(card_data.get("faq"))

        entry = {
            "id": card_id,
            "name": card_data.get("name", "Unknown"),
            "type": card_type,
            "ability_text": card_data.get("ability_text", ""),
            "faq_count": len(card_data.get("faq", [])),
            "parsed": None,
            "error": None,
        }

        # Try parsing if has ability
        if has_ability:
            try:
                abilities = AbilityParser.parse_ability_text(entry["ability_text"])
                entry["parsed"] = {
                    "count": len(abilities),
                    "triggers": [a.trigger.name for a in abilities],
                    "effects": [e.effect_type.name for a in abilities for e in a.effects],
                    "conditions": [c.type.name for a in abilities for c in a.conditions],
                    "costs": [cost.type.name for a in abilities for cost in a.costs],
                }
                results["with_ability"].append(entry)
            except Exception as e:
                entry["error"] = str(e)
                results["parsing_errors"].append(entry)
        elif has_faq:
            results["with_faq"].append(entry)
        else:
            results["vanilla"].append(entry)

    return results


def generate_report(results):
    output = []
    output.append("# Comprehensive Card Ability Coverage Report\n")
    output.append(
        f"Generated: {len(results['with_ability']) + len(results['with_faq']) + len(results['vanilla'])} total cards analyzed\n"
    )

    # Summary
    output.append("\n## Summary\n")
    output.append(f"- **Cards with Abilities**: {len(results['with_ability'])}\n")
    output.append(f"- **Cards with FAQ only**: {len(results['with_faq'])}\n")
    output.append(f"- **Vanilla cards** (no ability/FAQ): {len(results['vanilla'])}\n")
    output.append(f"- **Parsing Errors**: {len(results['parsing_errors'])}\n")

    # Cards with abilities
    output.append("\n## Cards with Abilities\n")
    output.append("| Card ID | Name | Type | Triggers | Effects | Conditions | Costs |\n")
    output.append("|---------|------|------|----------|---------|------------|-------|\n")

    for card in sorted(results["with_ability"], key=lambda x: x["id"]):
        parsed = card["parsed"]
        triggers = ", ".join(set(parsed["triggers"]))[:30]
        effects = ", ".join(set(parsed["effects"]))[:40]
        conditions = ", ".join(set(parsed["conditions"]))[:30] if parsed["conditions"] else "-"
        costs = ", ".join(set(parsed["costs"]))[:30] if parsed["costs"] else "-"

        output.append(
            f"| {card['id']} | {card['name']} | {card['type']} | {triggers} | {effects} | {conditions} | {costs} |\n"
        )

    # Cards with FAQ only
    if results["with_faq"]:
        output.append("\n## Cards with FAQ Only (No Abilities)\n")
        output.append("| Card ID | Name | FAQ Count |\n")
        output.append("|---------|------|-----------|\n")
        for card in sorted(results["with_faq"], key=lambda x: x["id"]):
            output.append(f"| {card['id']} | {card['name']} | {card['faq_count']} |\n")

    # Parsing errors
    if results["parsing_errors"]:
        output.append("\n## Parsing Errors\n")
        output.append("| Card ID | Name | Error |\n")
        output.append("|---------|------|-------|\n")
        for card in sorted(results["parsing_errors"], key=lambda x: x["id"]):
            error = card["error"][:60]
            output.append(f"| {card['id']} | {card['name']} | {error} |\n")

    return "".join(output)


if __name__ == "__main__":
    print("Analyzing all cards...")
    results = analyze_all_cards()

    print(f"Found {len(results['with_ability'])} cards with abilities")
    print(f"Found {len(results['with_faq'])} cards with FAQ only")
    print(f"Found {len(results['vanilla'])} vanilla cards")
    print(f"Found {len(results['parsing_errors'])} parsing errors")

    report = generate_report(results)

    with open("docs/full_ability_coverage.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\nReport saved to docs/full_ability_coverage.md")

    # Also save detailed JSON for programmatic access
    import json

    with open("docs/full_ability_coverage.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Detailed JSON saved to docs/full_ability_coverage.json")
