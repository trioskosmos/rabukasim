import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)


def search_cond(cond_type):
    found = []
    for db_name in ["member_db", "live_db"]:
        for card in data.get(db_name, {}).values():
            for ab in card.get("abilities", []):
                for cond in ab.get("conditions", []):
                    if cond.get("type") == cond_type:
                        found.append(card["card_no"])
    return found


target_conds = [15, 22]
for tc in target_conds:
    f = search_cond(tc)
    print(f"ConditionType {tc} in ANY abilities: {len(f)} cards")
    if f:
        print(f"Example cards: {f[:5]}")
