import json
import os
import sys
from dataclasses import asdict

# Ensure engine is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compiler.parser import AbilityParser


def patch_cards():
    cards_path = os.path.join("engine", "data", "cards_compiled.json")
    print(f"Loading {cards_path}...")

    with open(cards_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    targets = ["PL!HS-bp1-005-R", "PL!HS-bp1-005-P"]
    found_count = 0

    # Access member_db
    member_db = data.get("member_db", {})
    print(f"Member DB entries: {len(member_db)}")

    for cid_str, card in member_db.items():
        if card.get("card_no") in targets:
            print(f"Patching {card['card_no']} (ID {cid_str}) using AbilityParser...")

            # Use specific text that we know works with the fixed parser
            # The card likely has multiple abilities (lines/sentences), we focus on the first one
            # or just reparsed the whole text if available.

            raw_text = card.get("abilities", [{}])[0].get("raw_text", "")
            if not raw_text:
                # Fallback text if missing
                raw_text = "{{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く"

            print(f"Parsing text: {raw_text}")
            new_abilities = AbilityParser.parse_ability_text(raw_text)

            # Serialize for JSON
            abilities_json = [asdict(ab) for ab in new_abilities]

            # Update card
            card["abilities"] = abilities_json
            found_count += 1

    if found_count > 0:
        with open(cards_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully patched {found_count} cards with fixed parser output.")
    else:
        print("No target cards found to patch.")


if __name__ == "__main__":
    patch_cards()
