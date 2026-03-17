import os
import sys
from collections import defaultdict

# Ensure project root is in path
sys.path.append(os.getcwd())

from tools.master_validator import MasterValidator


def main():
    print("Analyzing Cards with MasterValidator...")
    # Use MasterValidator to get all scores, tiers, and reconstruction data
    validator = MasterValidator("data/cards.json")
    validator.run()

    # Grouping structure: {EffectType: [Cards]}
    grouped_cards = defaultdict(list)

    # Access internal reports mapping
    # structure of report: {card_no: {'name': ..., 'text': ..., 'recon': ..., 'tier': ..., 'score': ..., 'faq': ..., 'gaps': ...}}
    reports = validator.reports_by_card

    # Re-group by effect type (heuristically from the EffectType enum present in 'recon' or re-parsing)
    # Since validator already parsed everything, we can iterate reports.
    # However, reports doesn't explicitly list EffectTypes in a list.
    # We'll rely on the original loader for grouping purposes, or just list numerically if the user prefers.
    # The existing script grouped by EffectType, which is useful. Let's maintain that but iterate the REPORTS effectively.

    # To get effect types efficiently, we might need to re-parse or store them in validator.
    # Validator stores 'recon' string, but not raw effect objects.
    # Let's rely on the validator execution which already instantiated AbilityParser.
    # Actually, MasterValidator.run() modifies self.reports_by_card but discards the Ability objects.
    # We can perform a lightweight re-parse just for grouping, or modify Validator to store EffectTypes.
    # Given the constraint of not editing Validator too much right now, let's just re-parse for grouping.

    from game.ability import AbilityParser

    print("Grouping cards...")
    for card_no, report in reports.items():
        if "error" in report:
            grouped_cards["Parse Errors"].append(card_no)
            continue

        text = report.get("text", "")
        if not text:
            grouped_cards["No Ability"].append(card_no)
            continue

        try:
            abilities = AbilityParser.parse_ability_text(text)
            effect_types = set()
            for ab in abilities:
                for eff in ab.effects:
                    effect_types.add(eff.effect_type.name)
                for modal_opt in ab.modal_options:
                    for eff in modal_opt:
                        effect_types.add(eff.effect_type.name)

            if not effect_types:
                grouped_cards["Meta/Passive Only"].append(card_no)

            for etype in effect_types:
                grouped_cards[etype].append(card_no)
        except:
            grouped_cards["Parse Errors"].append(card_no)

    # Sort categories
    categories = sorted(grouped_cards.keys())

    os.makedirs("docs", exist_ok=True)

    # Load official game cards to get FAQ-injected abilities
    from game.data_loader import CardDataLoader

    print("Loading Cards with FAQ logic...")
    loader = CardDataLoader("data/cards.json")
    members, lives, _ = loader.load()
    all_game_cards = {**members, **lives}

    output_path = "docs/full_card_abilities.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Full Card Ability Gallery\n\n")
        f.write("> **Format**: Card Name (ID) | Tier | Score\n")
        f.write("> **Legend**: 📚 has FAQ, ⚠️ has Semantic Gaps\n\n")

        # TOC
        f.write("## Table of Contents\n")
        for cat in categories:
            count = len(grouped_cards[cat])
            f.write(f"- [{cat} ({count})](#{cat.lower().replace('_', '-')})\n")
        f.write("\n---\n\n")

        for cat in categories:
            f.write(f"## {cat}\n")
            f.write(f"**Total Count**: {len(grouped_cards[cat])}\n\n")

            # Sort cards by ID in category
            # grouped_cards[cat] is a list of card_no strings
            cat_card_nos = sorted(grouped_cards[cat])

            for cno in cat_card_nos:
                r = reports.get(cno, {})
                name = r.get("name", "Unknown")
                text = r.get("text", "").replace("\n", "<br>")
                recon = r.get("recon", "No reconstruction available")
                tier = r.get("tier", "D")
                score = r.get("score", 0)
                faq = r.get("faq", [])
                gaps = r.get("gaps", [])

                # Header Line
                icons = ""
                if faq:
                    icons += " 📚"
                if gaps:
                    icons += " ⚠️"

                f.write(f"### {cno}: {name} {icons}\n")
                f.write(f"- **Tier**: {tier} (Score: {score})\n")
                f.write(f"- **Ability**: `{text}`\n")
                f.write(f"- **Parsed**: {recon}\n")

                # Check for FAQ Overrides in official card objects
                game_card = all_game_cards.get(cno)
                if game_card and game_card.abilities:
                    overrides = []
                    for ab in game_card.abilities:
                        if "FAQ Override" in ab.raw_text:
                            # Reconstruct the override effect text
                            overrides.append(ab.reconstruct_text())

                    if overrides:
                        f.write("- **FAQ Overrides** (Injected Rules):\n")
                        for ov in overrides:
                            f.write(f"  - `{ov}`\n")

                if faq:
                    f.write("- **FAQ**:\n")
                    for q in faq:
                        f.write(f"  - Q: {q.get('question', '-')}\n")
                        f.write(f"  - A: {q.get('answer', '-')}\n")

                if gaps:
                    f.write(f"- **Gaps**: {', '.join(gaps)}\n")

                f.write("\n---\n")

    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()
