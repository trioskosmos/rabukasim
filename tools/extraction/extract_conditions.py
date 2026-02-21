import json

with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

cond_to_cards = {}


def process_db(db):
    for card in db.values():
        for ability in card.get("abilities", []):
            for cond in ability.get("conditions", []):
                c_type = cond.get("type") or cond.get("condition_type")
                if c_type is not None:
                    if c_type not in cond_to_cards:
                        cond_to_cards[c_type] = []
                    cond_to_cards[c_type].append(card["card_no"])


process_db(data.get("member_db", {}))
process_db(data.get("live_db", {}))

print("ConditionType mappings:")
for ct in sorted(cond_to_cards.keys()):
    cards = list(set(cond_to_cards[ct]))[:5]  # Show first 5
    print(f"{ct}: {cards}")
