import json

def final_repair():
    filename = "data/manual_pseudocode.json"
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # --- 1. Fix Group IDs for N/SP prefixes ---
    for card_no, entry in data.items():
        if card_no.startswith("PL!N-"):
            # Nijigasaki should be Group 2
            entry["pseudocode"] = entry["pseudocode"].replace("GROUP_ID=3", "GROUP_ID=2")
            entry["pseudocode"] = entry["pseudocode"].replace("GROUP_ID=4", "GROUP_ID=2")
        elif card_no.startswith("PL!SP-"):
            # Liella should be Group 3
            entry["pseudocode"] = entry["pseudocode"].replace("GROUP_ID=2", "GROUP_ID=3")
            entry["pseudocode"] = entry["pseudocode"].replace("GROUP_ID=4", "GROUP_ID=3")

    # --- 2. Fix 004 Set specifically ---
    # Umi logic (PL!-bp5-004)
    umi_logic = (
        "TRIGGER: ACTIVATED (Once per turn)\n"
        "COST: PAY_ENERGY(4); REDUCE_COST_PER_GROUP(1)\n"
        "EFFECT: TAP_OPPONENT(1) {FILTER=\"COST_LE_10\"} -> OPPONENT\n\n"
        "TRIGGER: ON_REVEAL (Once per turn)\n"
        "CONDITION: YELL_REVEALED {FILTER=\"NOT_BLADE_HEART\", MIN=3}\n"
        "EFFECT: ADD_HEARTS(1) -> SELF"
    )
    # Sumire logic (PL!SP-bp5-004)
    sumire_logic = (
        "TRIGGER: ON_POSITION_CHANGE (Once per turn)\n"
        "CONDITION: IS_SELF_MOVE_OR_ENERGY_PLACED\n"
        "EFFECT: DRAW(1); ADD_HEARTS(1) {HEART_TYPE=2, DURATION=\"UNTIL_LIVE_END\"}"
    )
    # Karin logic (PL!N-bp5-004)
    karin_logic = (
        "TRIGGER: ON_PLAY\n"
        "TRIGGER: ON_LIVE_START\n"
        "COST: TAP_SELF (Optional)\n"
        "EFFECT: TAP_OPPONENT(1) {FILTER=\"BLADE=4\"} -> OPPONENT"
    )
    # Ginko logic (PL!HS-bp5-004)
    ginko_logic = (
        "TRIGGER: CONSTANT\n"
        "CONDITION: COUNT_STAGE {FILTER=\"COST_GE_4, NOT_UNIT_CERISE_BOUQUET\", MULTIPLIER=2}\n"
        "EFFECT: ADD_BLADES(SELF, MULTIPLIER)"
    )
    # Dia logic (PL!S-bp5-004)
    dia_logic = (
        "TRIGGER: ON_PLAY\n"
        "EFFECT: SELECT_MODE(1) -> PLAYER\n"
        "  OPTION: ブレード追加 | EFFECT: ADD_BLADES(1) -> OTHER_MEMBER {FILTER=\"GROUP_ID=1\"}\n"
        "  OPTION: ポジションチェンジ | EFFECT: MOVE_MEMBER(1) {FILTER=\"Unit='Saint Snow'\"} -> AREA_CHOICE"
    )

    for card_no in data:
        if "bp5-004" in card_no:
            if card_no.startswith("PL!-"): data[card_no]["pseudocode"] = umi_logic
            elif card_no.startswith("PL!SP-"): data[card_no]["pseudocode"] = sumire_logic
            elif card_no.startswith("PL!N-"): data[card_no]["pseudocode"] = karin_logic
            elif card_no.startswith("PL!HS-"): data[card_no]["pseudocode"] = ginko_logic
            elif card_no.startswith("PL!S-"): data[card_no]["pseudocode"] = dia_logic

    # --- 3. Final specific fixes for the sentinels that were broken ---
    # Emma (PL!N-bp3-008-P) - Correcting the Group 3 to 2 fix (already handled by step 1, but let's be sure)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    final_repair()
