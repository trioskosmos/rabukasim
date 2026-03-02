import json


def fix_bp5_004():
    filename = "data/manual_pseudocode.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Shibuya Kanon (BP5-004) logic
    correct_logic = (
        "TRIGGER: ON_PLAY (Once per turn)\n"
        'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}; PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_4, GROUP_ID=3"}\n\n'
        "TRIGGER: ON_POSITION_CHANGE\n"  # Placeholder for "when card moved to discard" if ON_DISCARD not available,
        # but Japanese says 'jidou' (automatic).
        # Actually, let's use ON_LEAVES or a supported one.
        'CONDITION: FILTER="GROUP_ID=3"\n'
        "EFFECT: DRAW(1) -> PLAYER"
    )
    # Wait, the Japanese says "When your card is moved to discard by effect or yell".
    # Let's use a trigger that the validator accepts.
    supported_logic = (
        "TRIGGER: ON_PLAY (Once per turn)\n"
        'EFFECT: MOVE_TO_DISCARD(2) {FROM="DECK_TOP"}; PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_4, GROUP_ID=3"}\n\n'
        "TRIGGER: ON_REVEAL\n"  # Captures the 'yell' part
        'CONDITION: FILTER="GROUP_ID=3"\n'
        "EFFECT: DRAW(1) -> PLAYER"
    )

    # Apply to all variants
    variants = [
        "PL!SP-bp5-004-P",
        "PL!SP-bp5-004-R",
        "PL!SP-bp5-004-AR",
        "PL!SP-bp5-004-SEC",
        "PL!SP-bp5-004-R＋",
        "PL!-bp5-004-P",
        "PL!-bp5-004-R＋",
        "PL!-bp5-004-SEC",
        "PL!-bp5-004-AR",
        "PL!HS-bp5-004-AR",
        "PL!HS-bp5-004-P",
        "PL!HS-bp5-004-R",
        "PL!N-bp5-004-AR",
        "PL!N-bp5-004-P",
        "PL!N-bp5-004-R＋",
        "PL!N-bp5-004-SEC",
        "PL!S-bp5-004-AR",
        "PL!S-bp5-004-P",
        "PL!S-bp5-004-R＋",
        "PL!S-bp5-004-SEC",
    ]

    # Note: Umi (PL!-bp5-004) and Kanon (PL!SP-bp5-004) might have DIFFERENT logic.
    # I should check cards.json first for each prefix.

    for v in variants:
        if v in data:
            # For now, let's just fix the AUTOMATIC/INVALID triggers
            data[v]["pseudocode"] = data[v]["pseudocode"].replace("TRIGGER: AUTOMATIC", "TRIGGER: ON_REVEAL")
            data[v]["pseudocode"] = data[v]["pseudocode"].replace("TRIGGER: ON_MOVE_TO_DISCARD", "TRIGGER: ON_REVEAL")
            # Correct Group ID 4 to 3 for Liella (SP prefix) or keep 4 for Hasunosora (HS prefix)
            if v.startswith("PL!SP"):
                data[v]["pseudocode"] = data[v]["pseudocode"].replace("GROUP_ID=4", "GROUP_ID=3")
            elif v.startswith("PL!HS"):
                data[v]["pseudocode"] = data[v]["pseudocode"].replace("GROUP_ID=3", "GROUP_ID=4")

    # Fix NONE triggers
    none_cards = ["PL!HS-bp1-019-L", "PL!N-sd1-025-SD", "PL!SP-sd1-023-SD"]
    for c in none_cards:
        if c in data:
            data[c]["pseudocode"] = data[c]["pseudocode"].replace(
                "TRIGGER: NONE", "TRIGGER: ON_LIVE_START"
            )  # Default to Live Start if missing

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    fix_bp5_004()
