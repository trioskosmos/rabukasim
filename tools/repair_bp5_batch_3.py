import json

def repair_batch_3():
    filename = "data/manual_pseudocode.json"
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Dictionary for E-series and Live cards
    repairs = {
        # --- Live Cards ---
        "019-L": {
            "": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=0\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "S": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=1\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "N": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=2\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "SP": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=3\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "HS": "TRIGGER: ON_LIVE_START\nEFFECT: REDUCE_HEART_REQ(2) {HEART_TYPE=4, PER_CARD=\"SUCCESS_LIVE_GROUP_4\"} -> SELF"
        },
        "020-L": {
            "": "TRIGGER: ON_LIVE_START\nCONDITION: CENTER_HAS_GROUP {GROUP_ID=0}\nEFFECT: REDUCE_HEART_REQ_DYNAMIC(COUNT_HEARTS_TYPE_3 / 2) {HEART_TYPE=0, MAX=3} -> SELF",
            "S": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: OVER_HEARTS {MIN=3}\nEFFECT: RESET_OVER_HEARTS; BOOST_SCORE(1) -> SELF",
            "N": "TRIGGER: ON_LIVE_START\nEFFECT: SELECT_MODE(1) -> PLAYER\n  OPTION: アクティブ | EFFECT: ACTIVATE_MEMBER(1) {FILTER=\"WAIT\"}; ADD_BLADES(1) -> TARGET\n  OPTION: ウェイト | EFFECT: TAP_OPPONENT(1) {FILTER=\"BLADE_LE_3\"}\n\nTRIGGER: ON_LIVE_SUCCESS\nEFFECT: DRAW(1)", # Simplified Victory Road
            "SP": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=3\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "HS": "TRIGGER: ON_LIVE_START\nCONDITION: COUNT_STAGE {FILTER=\"COST_GE_10, GROUP_ID=4\", MIN=2}\nEFFECT: BOOST_SCORE(1) -> SELF"
        },
        "021-L": {
            "": "TRIGGER: ON_LIVE_START\nCONDITION: COUNT_STAGE {MIN=1}\nEFFECT: DRAW(1); DISCARD_HAND(1) -> PLAYER_AND_OPPONENT\nCONDITION: COUNT_STAGE {MIN=2}\nEFFECT: ADD_HEARTS(1) {HEART_TYPE=3, DURATION=\"UNTIL_LIVE_END\"}\nCONDITION: COUNT_STAGE {MIN=3, UNIQUE_NAMES=TRUE}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "S": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=1\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "N": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=2\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "SP": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=3\"}\nEFFECT: BOOST_SCORE(1) -> SELF",
            "HS": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=4\"}\nEFFECT: BOOST_SCORE(1) -> SELF"
        },
        "022-L": {
             "": "TRIGGER: ON_LIVE_START\nEFFECT: BOOST_SCORE(2) {PER_CARD=\"SUCCESS_LIVE\"} -> SELF\nEFFECT: INCREASE_HEART_REQ(1) {PER_CARD=\"SUCCESS_LIVE\", HEART_TYPES=[1,3,6,0]} -> SELF"
        },
        "023-L": {
             "SP": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: TOTAL_SUCCESS_LIVE {MIN=2}\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=1}\nEFFECT: BOOST_SCORE(2) -> SELF",
             "S": "TRIGGER: ON_LIVE_START\nCONDITION: COUNT_STAGE {FILTER=\"GROUP_ID=1\", MIN=1} AND COUNT_STAGE {FILTER=\"GROUP_ID=7\", MIN=1}\nCONDITION: TOTAL_COST {MIN=20}\nEFFECT: REORDER_DECK_TOP(4) {FILTER=\"GROUP_ID=ANY=[1,7]\", FROM=\"DISCARD\"}"
        },
        "024-L": {
            "SP": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR COUNT_STAGE {MIN=1, FILTER=\"GROUP_ID=3\"}\nEFFECT: BOOST_SCORE(1) -> SELF"
        },
        "025-L": {
            "SP": "TRIGGER: ON_LIVE_SUCCESS\nCOST: PAY_ENERGY_DYNAMIC(4, MULTIPLIER=X)\nEFFECT: BOOST_SCORE(X) -> SELF"
        },
        "027-L": {
            "SP": "TRIGGER: ON_LIVE_SUCCESS\nCOST: PLACE_ENERGY_WAIT(1) (Optional)\nEFFECT: DRAW(1) -> OPPONENT",
            "N": "TRIGGER: ON_LIVE_START\nCONDITION: TOTAL_SUCCESS_LIVE {MIN=2}\nCONDITION: UNIQUE_NAMES_COUNT {MIN=3}\nEFFECT: BOOST_SCORE(1) -> SELF"
        },
        "029-L": {
            "N": "TRIGGER: ON_LIVE_START\nCONDITION: COUNT_STAGE {NAME=\"中須かすみ\", MIN=1}\nEFFECT: LOOK_DECK(4)\nEFFECT: SELECT_CARD {NAME=\"中須かすみ\"} -> CHOICE\nEFFECT: ADD_HEARTS(1) {HEART_TYPE=CHOICE_COLORS} -> MEMBER {NAME=\"中須かすみ\"}\nEFFECT: DISCARD_REMAINDER"
        },
        "030-L": {
             "N": "TRIGGER: ON_ABILITY_RESOLVE (Live Start Only)\nCONDITION: NOT_HAS_HEART\nEFFECT: ADD_ALL_HEARTS(1) {DURATION=\"UNTIL_LIVE_END\"}\n\nTRIGGER: ON_ABILITY_RESOLVE (Live Success Only)\nEFFECT: DRAW(1)"
        },
        "001-L": {
             "LL": "TRIGGER: ON_LIVE_SUCCESS\nCONDITION: YELL_REVEALED {FILTER=\"TYPE_LIVE\", MIN=2} OR HAS_HEART_TYPES {MIN_TYPES=5} OR ANY_MEMBER_MOVED_THIS_TURN\nEFFECT: BOOST_SCORE(1) -> SELF"
        }
    }

    # Programmatic repair for E-series (Skill-less)
    e_logic = {
        "E01": 0, "E02": 1, "E03": 2, "E04": 3, "E05": 4, "E06": 5, "E07": 6, "E08": 7, "E09": 8
    }
    # BP5 E-series maps E01-E06 to specific hearts, and E07-E09 to Blades/Scores usually.
    # Actually most E-cards in BP5 are just "Skill-less" with a specific heart.
    
    prefixes = {"":0, "S":1, "N":2, "SP":3, "HS":4}

    for card_no in list(data.keys()):
        if "bp5" not in card_no: continue
        parts = card_no.split("-")
        if len(parts) < 3: continue
        prefix_part = parts[0].replace("PL!", "")
        num_part = parts[2]
        
        # Repair Live Cards
        live_key = num_part + "-L"
        if num_part.endswith("L") and num_part in repairs:
             if prefix_part in repairs[num_part]:
                  data[card_no]["pseudocode"] = repairs[num_part][prefix_part]
        
        # Repair E-series
        if num_part.startswith("E"):
             # E01-E06 are almost always hearts 0-5
             if num_part in e_logic:
                  h_type = e_logic[num_part]
                  if h_type <= 6:
                       data[card_no]["pseudocode"] = f"TRIGGER: CONSTANT\nEFFECT: ADD_HEARTS(1) {{HEART_TYPE={h_type}}} -> SELF"
                  else:
                       data[card_no]["pseudocode"] = "TRIGGER: CONSTANT\nEFFECT: ADD_BLADES(1) -> SELF"
             
             # Special cases for E07-E09 (usually blades or score boosts)
             if num_part == "E09":
                  data[card_no]["pseudocode"] = "TRIGGER: CONSTANT\nEFFECT: BOOST_SCORE(1) -> SELF"
             if num_part == "E08" and prefix_part == "": # Hanayo
                  data[card_no]["pseudocode"] = "TRIGGER: CONSTANT\nEFFECT: BOOST_SCORE(1) -> SELF"

    # Additional manual fixes for collisions found in audit
    manual_overrides = {
        "PL!-bp5-005-AR": "TRIGGER: ON_PLAY\nCONDITION: SUCCESS_LIVE_SCORE_TOTAL {GE=6}\nEFFECT: PLACE_ENERGY_WAIT(1) {ACTIVE=TRUE} -> PLAYER",
        "PL!N-bp5-005-SEC": "TRIGGER: ON_LEAVES\nCONDITION: BATON_TOUCH {FILTER=\"GROUP_ID=2, NOT_HAS_BLADE_HEART, COST_GE_10\"}\nEFFECT: ACTIVATE_ENERGY(2)\nCONDITION: BATON_TOUCH {FILTER=\"GROUP_ID=2, NOT_HAS_BLADE_HEART, COST_GE_15\"}\nEFFECT: DRAW(1)",
    }
    for k, v in manual_overrides.items():
        if k in data: data[k]["pseudocode"] = v

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    repair_batch_3()
