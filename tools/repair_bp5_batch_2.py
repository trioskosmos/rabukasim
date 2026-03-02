import json


def repair_batch_2():
    filename = "data/manual_pseudocode.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    repairs = {
        # --- 016 ---
        "016": {
            "": (  # Nozomi (016 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1); DISCARD_HAND(1)"
            ),
            "S": (  # Yohane (016 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "N": (  # Karin (016 N)
                "TRIGGER: ON_LIVE_SUCCESS\nEFFECT: DRAW(1); DISCARD_HAND(1) (Optional)"
            ),
            "SP": (  # Ren (016 N)
                "TRIGGER: CONSTANT\nCONDITION: ENERGY_COUNT {GE=10}\nEFFECT: ADD_HEARTS(2) {HEART_TYPE=6}"
            ),
            "HS": (  # Izumi (016 N)
                "TRIGGER: ON_PLAY\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                'EFFECT: TAP_OPPONENT(2) {FILTER="COST_LE_4"}\n\n'
                "TRIGGER: CONSTANT\n"
                "CONDITION: OPP_TAP_COUNT {GE=2}\n"
                "EFFECT: ADD_HEARTS(1) {HEART_TYPE=6}"
            ),
        },
        # --- 017 ---
        "017": {
            "": (  # Hanayo (017 N)
                "TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(1) (Optional)\nEFFECT: ADD_BLADES(1) -> PLAYER"
            ),
            "S": (  # Ruby (017 N)
                "TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(1) (Optional)\nEFFECT: ADD_BLADES(1) -> PLAYER"
            ),
            "N": (  # Ai (017 N)
                "TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(1) (Optional)\nEFFECT: ADD_BLADES(1) -> PLAYER"
            ),
            "SP": (  # Kinako (017 N)
                "TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(1) (Optional)\nEFFECT: ADD_BLADES(1) -> PLAYER"
            ),
            "HS": (  # Lillienfelt (017 N)
                "TRIGGER: ON_LIVE_START\nCOST: DISCARD_HAND(1) (Optional)\nEFFECT: ADD_BLADES(1) -> PLAYER"
            ),
        },
        # --- 018 ---
        "018": {
            "": (  # Nico (018 N)
                "TRIGGER: ON_PLAY\n"
                'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}\n'
                "EFFECT: MOVE_TO_DECK_TOP(1) {FILTER=\"TYPE_MEMBER, FROM='DISCARD'\"}"
            ),
            "S": (  # Maru (018 N)
                "TRIGGER: ON_PLAY\n"
                'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}\n'
                "EFFECT: MOVE_TO_DECK_TOP(1) {FILTER=\"TYPE_MEMBER, FROM='DISCARD'\"}"
            ),
            "N": (  # Shioriko (018 N)
                "TRIGGER: ON_PLAY\n"
                'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}\n'
                "EFFECT: MOVE_TO_DECK_TOP(1) {FILTER=\"TYPE_MEMBER, FROM='DISCARD'\"}"
            ),
            "SP": (  # Mei (018 N)
                "TRIGGER: ON_PLAY\n"
                'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}\n'
                "EFFECT: MOVE_TO_DECK_TOP(1) {FILTER=\"TYPE_MEMBER, FROM='DISCARD'\"}"
            ),
            "HS": (  # Ginko (018 N)
                "TRIGGER: ON_PLAY\n"
                'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}\n'
                "EFFECT: MOVE_TO_DECK_TOP(1) {FILTER=\"TYPE_MEMBER, FROM='DISCARD'\"}"
            ),
        },
        # --- 019 ---
        "019": {
            "": (  # Arisa (019 N)
                "TRIGGER: ON_PLAY\nCONDITION: DISCARD_COUNT {GE=10}\nEFFECT: DRAW(1)"
            ),
            "S": (  # Leah (019 N)
                "TRIGGER: ON_PLAY\nCONDITION: DISCARD_COUNT {GE=10}\nEFFECT: DRAW(1)"
            ),
            "N": (  # Setsuna (019 N)
                "TRIGGER: ON_PLAY\nCONDITION: DISCARD_COUNT {GE=10}\nEFFECT: DRAW(1)"
            ),
            "SP": (  # Shiki (019 N)
                "TRIGGER: ON_PLAY\nCONDITION: DISCARD_COUNT {GE=10}\nEFFECT: DRAW(1)"
            ),
            "HS": (  # Hime (019 N)
                "TRIGGER: ON_PLAY\nCONDITION: DISCARD_COUNT {GE=10}\nEFFECT: DRAW(1)"
            ),
        },
        # --- 020 ---
        "020": {
            "": (  # Honoka (020 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "S": (  # Chika (020 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "N": (  # Ayumu (020 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "SP": (  # Kanon (020 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "HS": (  # Kaho (020 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
        },
        # --- 021+ (Rina etc) ---
        "021": {
            "N": (  # Rina (021 N)
                "TRIGGER: ON_PLAY\n"
                'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}\n'
                "EFFECT: MOVE_TO_DECK_TOP(1) {FILTER=\"TYPE_LIVE, FROM='DISCARD'\", POS=4} (Optional)"
            )
        },
        "022": {
            "N": (  # Shioriko (022 N)
                "TRIGGER: ON_PLAY\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                'EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=2"} -> CARD_HAND'
            )
        },
    }

    prefixes = {"": 0, "S": 1, "N": 2, "SP": 3, "HS": 4}

    for card_no in list(data.keys()):
        if "bp5" not in card_no:
            continue
        parts = card_no.split("-")
        if len(parts) < 3:
            continue
        prefix_part = parts[0].replace("PL!", "")
        num_part = parts[2]

        if num_part in repairs:
            group_repairs = repairs[num_part]
            if prefix_part in group_repairs:
                data[card_no]["pseudocode"] = group_repairs[prefix_part]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    repair_batch_2()
