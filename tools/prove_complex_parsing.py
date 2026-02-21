import json
import os
import sys

# Fix encoding for Windows console (just in case)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.parser_v2 import AbilityParserV2


def prove_it():
    # Load cards
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "cards_compiled.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    cards = []
    sections = ["member_db", "live_db"]
    for section in sections:
        for cid, c in data.get(section, {}).items():
            if "abilities" in c and c["abilities"]:
                texts = [a.get("raw_text", "") for a in c["abilities"] if a.get("raw_text")]
                if texts:
                    text = "\n".join(texts)
                    cards.append((c.get("card_no", cid), text))

    # Sort by length (complexity proxy)
    cards.sort(key=lambda x: len(x[1]), reverse=True)

    parser = AbilityParserV2()

    print(f"Total cards loaded: {len(cards)}")
    print("=" * 80)
    print("PROOF OF COMPLEX PARSING: TOP CARDS")
    print("=" * 80)

    # Select diverse complex targets
    # 1. Longest text
    targets = cards[:3]

    # 2. Known complex logic (Modal, Logic Chains) from previous report
    specific_ids = ["LL-bp1-001-R＋", "PL!-bp3-007-P", "PL!-bp3-004-SEC"]
    for sid in specific_ids:
        found = next((c for c in cards if c[0] == sid), None)
        if found and found not in targets:
            targets.append(found)

    for card_no, text in targets:
        print(f"\n>>> CARD: {card_no}")
        print(f"Raw Text Length: {len(text)}")
        preview = text.replace("\n", " ")
        print(f"Text: {preview[:100]}..." if len(preview) > 100 else preview)
        print("-" * 40)

        try:
            abilities = parser.parse(text)
            if not abilities:
                print("  [NO ABILITIES PARSED]")

            for i, ab in enumerate(abilities):
                print(f"  [Ability {i + 1}] Trigger: {ab.trigger.name}")

                # Modifiers/Flags
                flags = []
                if ab.is_once_per_turn:
                    flags.append("OPT")
                if flags:
                    print(f"    Flags: {', '.join(flags)}")

                # Costs
                if ab.costs:
                    costs_str = []
                    for c in ab.costs:
                        c_desc = f"{c.type.name}"
                        if c.value > 1:
                            c_desc += f"({c.value})"
                        if c.params:
                            c_desc += f" {c.params}"
                        costs_str.append(c_desc)
                    print(f"    Costs: {', '.join(costs_str)}")

                # Conditions
                if ab.conditions:
                    for c in ab.conditions:
                        print(f"    Cond:  {c.type.name} {c.params if c.params else ''}")

                # Effects
                if ab.effects:
                    for eff in ab.effects:
                        eff_desc = f"{eff.effect_type.name} (val={eff.value})"
                        if eff.target.name != "SELF":
                            eff_desc += f" -> {eff.target.name}"
                        if eff.params:
                            eff_desc += f" {eff.params}"
                        print(f"    Effect: {eff_desc}")

                        # Show modal details
                        if eff.modal_options:
                            print(f"      MODAL BRANCHES: {len(eff.modal_options)}")
                            for idx, opt in enumerate(eff.modal_options):
                                opt_summary = " + ".join([e.effect_type.name for e in opt])
                                print(f"        Option {idx + 1}: {opt_summary}")

        except Exception as e:
            print(f"  !! CRASH !! {e}")
            import traceback

            traceback.print_exc()
        print("=" * 80)


if __name__ == "__main__":
    with open("proof.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        prove_it()
        sys.stdout = sys.__stdout__
