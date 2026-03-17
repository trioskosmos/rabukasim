import json


def fix_last_error():
    filename = "data/manual_pseudocode.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Fix PL!N-bp4-018-N
    if "PL!N-bp4-018-N" in data:
        data["PL!N-bp4-018-N"]["pseudocode"] = (
            "TRIGGER: ON_PLAY\n"
            "TRIGGER: ON_POSITION_CHANGE\n"
            'EFFECT: RECOVER_MEMBER(1) {FILTER="Liella!", FROM="DISCARD"} -> CARD_HAND'
        )
        print("Fixed PL!N-bp4-018-N")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    fix_last_error()
