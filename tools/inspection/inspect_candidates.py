import json

# Make sure we can import engine modules if needed, but raw json is safer for "reading"
# integer enum mapping
EFFECT_MAP = {
    0: "DRAW",
    1: "ADD_BLADES",
    2: "ADD_HEARTS",
    6: "BOOST_SCORE",
    8: "BUFF_POWER",
    13: "ENERGY_CHARGE",
    30: "ADD_TO_HAND",
}
TRIGGER_MAP = {1: "ON_PLAY", 2: "LIVE_START", 3: "LIVE_SUCCESS"}


def main():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    db = data["member_db"]
    candidates = ["PL!N-bp1-001-P", "PL!N-bp1-005-P", "PL!N-bp4-013-N", "PL!-bp4-011-N"]

    for cid, card in db.items():
        if card["card_no"] in candidates:
            print(f"=== {card['card_no']} : {card['name']} ===")
            print(f"Blades: {card.get('blades', 0)}")
            print(json.dumps(card, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
