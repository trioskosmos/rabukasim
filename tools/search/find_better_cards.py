import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compiler.parser_legacy import AbilityParser as LegacyParser  # Use the backup

from compiler.parser_v2 import AbilityParserV2


def find_better_cards():
    # Load cards
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "cards_compiled.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    legacy = LegacyParser()
    v2 = AbilityParserV2()

    better_found = []

    # Check a sample of cards
    cards_checked = 0
    for section in ["member_db"]:
        for cid, card in data.get(section, {}).items():
            text = ""
            if "abilities" in card and card["abilities"]:
                texts = [a.get("raw_text", "") for a in card["abilities"] if a.get("raw_text")]
                if texts:
                    text = "\n".join(texts)

            if not text:
                continue

            try:
                l_res = legacy.parse_ability_text(text)
                v_res = v2.parse(text)

                l_score = sum(len(a.effects) + len(a.conditions) + len(a.costs) for a in l_res)
                v_score = sum(len(a.effects) + len(a.conditions) + len(a.costs) for a in v_res)

                if v_score > l_score:
                    better_found.append(
                        {
                            "id": card.get("card_no", cid),
                            "text": text,
                            "legacy_count": l_score,
                            "v2_count": v_score,
                            "details": [e.effect_type.name for a in v_res for e in a.effects],
                        }
                    )
            except:
                continue

            cards_checked += 1
            if len(better_found) >= 5:
                break
        if len(better_found) >= 5:
            break

    print(json.dumps(better_found, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    find_better_cards()
