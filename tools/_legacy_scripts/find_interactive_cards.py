import json
import os
import sys

# Opcodes
O_SELECT_MODE = 30
O_LOOK_AND_CHOOSE = 41
O_COLOR_SELECT = 45
O_ORDER_DECK = 28
O_SELECT_CARDS = 74
O_OPPONENT_CHOOSE = 75

INTERACTIVE_OPS = {
    O_SELECT_MODE: "SELECT_MODE",
    O_LOOK_AND_CHOOSE: "LOOK_AND_CHOOSE",
    O_COLOR_SELECT: "COLOR_SELECT",
    O_ORDER_DECK: "ORDER_DECK",
    O_SELECT_CARDS: "SELECT_CARDS",
    O_OPPONENT_CHOOSE: "OPPONENT_CHOOSE",
}


def scan():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    db = {}
    if "member_db" in data:
        db.update(data["member_db"])
    if "live_db" in data:
        db.update(data["live_db"])

    print(f"Scanning {len(db)} cards...")

    found = []

    for cid, card in db.items():
        abilities = card.get("abilities", [])
        for i, ab in enumerate(abilities):
            bytecode = ab.get("bytecode", [])
            for op in bytecode:
                if op in INTERACTIVE_OPS:
                    found.append(
                        {
                            "id": cid,
                            "card_no": card.get("card_no"),
                            "name": card.get("name"),
                            "opcode": INTERACTIVE_OPS[op],
                            "ability_idx": i,
                        }
                    )
                    break  # One interactive op is enough to list it

    print(f"Found {len(found)} interactive cards.")
    for item in found[:20]:
        print(f"[{item['card_no']}] {item['name']} - {item['opcode']}")

    # Save to file
    with open("reports/interactive_cards.json", "w", encoding="utf-8") as f:
        json.dump(found, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    scan()
