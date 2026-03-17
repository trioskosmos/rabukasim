import json
from pathlib import Path


def count_affected():
    path = Path("data/cards_compiled.json")
    if not path.exists():
        print("Compiled cards not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    affected = []
    # EffectType.LOOK_AND_CHOOSE = 27
    # TargetType.CARD_HAND = 6

    for card_id, card in data.get("member_db", {}).items():
        is_351 = str(card_id) == "351"
        for ab in card.get("abilities", []):
            for eff in ab.get("effects", []):
                if is_351:
                    print(f"DEBUG [351]: keys={list(eff.keys())}, values={list(eff.values())}")
                etype = eff.get("effect_type", eff.get("type"))
                etarget = eff.get("target")
                if etype == 27 and etarget == 6:
                    affected.append(card.get("card_no", card_id))
                    break

    print(f"Total affected cards: {len(affected)}")
    if affected:
        print(f"Sample: {', '.join(affected[:15])}")


if __name__ == "__main__":
    count_affected()
