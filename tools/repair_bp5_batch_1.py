import json


def repair_batch_1():
    filename = "data/manual_pseudocode.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dictionary of specific logic for BP5 001-015
    # Entries: card_suffix (e.g. "-bp5-001") -> {series_prefix: pseudocode}
    # Series: μ's="", Aqours="S", Nijigasaki="N", Liella="SP", Hasuno="HS"

    repairs = {
        # --- 001 ---
        "001": {
            "": (  # Honoka
                "TRIGGER: ON_LIVE_SUCCESS\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                "EFFECT: LOOK_DECK_DYNAMIC_SCORE(2) -> CARD_HAND, DISCARD_REMAINDER"
            ),
            "S": (  # Chika
                "TRIGGER: ON_PLAY\n"
                'CONDITION: BATON_TOUCH {FILTER="NOT_ABILITY"}\n'
                "EFFECT: DRAW(1)\n\n"
                "TRIGGER: CONSTANT\n"
                'EFFECT: REDUCE_COST(1) {FILTER="NOT_ABILITY"} -> PLAYER'
            ),
            "N": (  # Ayumu
                "TRIGGER: ON_REVEAL (Once per turn)\n"
                "CONDITION: YELL_REVEALED_UNIQUE_COLORS {MIN=3}\n"
                'EFFECT: ADD_HEARTS(1) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}\n\n'
                "TRIGGER: ON_REVEAL (Once per turn)\n"
                "CONDITION: YELL_REVEALED_UNIQUE_COLORS {MIN=6}\n"
                'EFFECT: GRANT_ABILITY(SELF, "TRIGGER: CONSTANT\\nEFFECT: BOOST_SCORE(1) -> PLAYER") {DURATION="UNTIL_LIVE_END"}'
            ),
            "SP": (  # Kanon
                "TRIGGER: ON_PLAY\n"
                "TRIGGER: ON_LIVE_START\n"
                "COST: PAY_ENERGY(1) (Optional)\n"
                "EFFECT: SELECT_MODE(1) -> PLAYER\n"
                '  OPTION: ウェイト | EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}\n'
                "  OPTION: ドロー | EFFECT: DRAW(1)\n\n"
                "TRIGGER: ACTIVATED (Once per turn)\n"
                'COST: SELECT_SELF_OR_DISCARD {CHOICE=["TAP_SELF", "DISCARD_HAND(1)"]}\n'
                "EFFECT: ACTIVATE_ENERGY(1)"
            ),
            "HS": (  # Kaho
                "TRIGGER: ON_PLAY\n"
                'EFFECT: MOVE_TO_DISCARD(4) {FROM="DECK_TOP"}\n'
                'CONDITION: DISCARDED_CARDS {FILTER="TYPE_LIVE", MIN=1}\n'
                'EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}\n\n'
                "TRIGGER: ACTIVATED (Once per turn)\n"
                "COST: PAY_ENERGY(2); REVEAL_HAND_LIVE(1) -> OPPONENT\n"
                'EFFECT: RECOVER_LIVE(1) {FILTER="SAME_NAME_AS_REVEALED"} -> CARD_HAND'
            ),
        },
        # --- 002 ---
        "002": {
            "": (  # Eli
                "TRIGGER: ON_PLAY\n"
                "COST: TAP_SELF; DISCARD_HAND(1) (Optional)\n"
                'EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=0, COST_GE_9"}; MOVE_TO_HAND(1); DISCARD_REMAINDER'
            ),
            "S": (  # Riko
                "TRIGGER: ON_LIVE_START (Center Only)\n"
                'CONDITION: SYNC_COST {AREA="SIDE_AREAS"}\n'
                'EFFECT: TAP_OPPONENT(ALL) {FILTER="BLADE_LE_3"}'
            ),
            "N": (  # Kasumi
                'TRIGGER: CONSTANT\nCONDITION: MOST_HEARTS {AREA="BOTH_STAGE"}\nEFFECT: BOOST_SCORE(1) -> PLAYER'
            ),
            "SP": (  # Keke
                "TRIGGER: ACTIVATED (Once per turn)\n"
                'CONDITION: AREA="LEFT_SIDE"\n'
                "COST: TAP_SELF\n"
                "EFFECT: DRAW(3); DISCARD_HAND(2)\n"
                'CONDITION: DISCARDED_CARDS {FILTER="NOT_HAS_BLADE_HEART", MIN=1}\n'
                "EFFECT: ACTIVATE_SELF\n"
                'CONDITION: DISCARDED_CARDS {FILTER="NOT_HAS_BLADE_HEART", MIN=2}\n'
                'EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}'
            ),
            "HS": (  # Sayaka
                "TRIGGER: CONSTANT\n"
                "CONDITION: UNIQUE_COST_COUNT {MIN=3}\n"
                "EFFECT: ADD_HEARTS(1) {HEART_TYPE=5}; ADD_BLADES(1) -> SELF\n\n"
                "TRIGGER: ACTIVATED (Once per turn)\n"
                "COST: PAY_ENERGY(2)\n"
                'EFFECT: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2"} -> EMPTY_SLOT'
            ),
        },
        # --- 003 ---
        "003": {
            "": (  # Kotori
                "TRIGGER: CONSTANT\n"
                "CONDITION: UNIQUE_NAMES_COUNT {MIN=3}\n"
                "EFFECT: ADD_HEARTS(1) {HEART_TYPE=3} -> SELF\n\n"
                "TRIGGER: ACTIVATED (Once per turn)\n"
                "COST: PAY_ENERGY(2); DISCARD_HAND(1)\n"
                'CONDITION: DISCARDED_CARDS {FILTER="GROUP_ID=0"}\n'
                'EFFECT: DRAW_MEMBER_FROM_DECK(2) {FILTER="ANY", LOOK=4}\n'
                'CONDITION: NOT_DISCARDED_CARDS {FILTER="GROUP_ID=0"}\n'
                "EFFECT: RECOVER_LIVE(1) -> CARD_HAND"
            ),
            "S": (  # Kanan
                "TRIGGER: ON_PLAY\n"
                'COST: DISCARD_HAND(2) {FILTER="NOT_HAS_BLADE_HEART"} (Optional)\n'
                'EFFECT: RECOVER_LIVE(COUNT_DISCARDED) {FILTER="GROUP_ID=1"} -> CARD_HAND'
            ),
            "N": (  # Shizuku
                "TRIGGER: ACTIVATED (Once per turn)\n"
                "COST: DISCARD_HAND(1)\n"
                "EFFECT: PAY_ENERGY(TARGET_SCORE) (Optional)\n"
                'EFFECT: RECOVER_LIVE(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND'
            ),
            "SP": (  # Chisato
                "TRIGGER: CONSTANT\n"
                'EFFECT: REDUCE_COST(2) {FILTER="GROUP_ID=3, COST_EQ_10"} -> PLAYER\n\n'
                "TRIGGER: ON_LIVE_START (Center Only)\n"
                'EFFECT: ACTIVATE_MEMBER(ALL) {FILTER="GROUP_ID=3"}; ACTIVATE_ENERGY(ALL)'
            ),
            "HS": (  # Rurino
                "TRIGGER: ON_LEAVES\n"
                "EFFECT: POSITION_CHANGE(1) (Optional) -> PLAYER\n\n"
                "TRIGGER: ON_LIVE_START\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                'EFFECT: ADD_HEARTS(1) {HEART_TYPE=0} -> MEMBER {FILTER="SAME_GROUP_AS_DISCARDED"}'
            ),
        },
        # --- 004 ---
        "004": {
            "": (  # Umi
                "TRIGGER: ACTIVATED (Once per turn)\n"
                "COST: PAY_ENERGY(4); REDUCE_COST_PER_GROUP(1)\n"
                'EFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_10"} -> OPPONENT\n\n'
                "TRIGGER: ON_REVEAL (Once per turn)\n"
                'CONDITION: YELL_REVEALED {FILTER="NOT_BLADE_HEART", MIN=3}\n'
                'EFFECT: ADD_HEARTS(1) -> SELF {DURATION="UNTIL_LIVE_END"}'
            ),
            "S": (  # Dia
                "TRIGGER: ON_PLAY\n"
                "EFFECT: SELECT_MODE(1) -> PLAYER\n"
                '  OPTION: ブレード追加 | EFFECT: ADD_BLADES(1) -> OTHER_MEMBER {FILTER="GROUP_ID=1"}\n'
                "  OPTION: ポジションチェンジ | EFFECT: MOVE_MEMBER(1) {FILTER=\"Unit='Saint Snow'\"} -> AREA_CHOICE"
            ),
            "N": (  # Karin
                "TRIGGER: ON_PLAY\n"
                "TRIGGER: ON_LIVE_START\n"
                "COST: TAP_SELF (Optional)\n"
                'EFFECT: TAP_OPPONENT(1) {FILTER="BLADE=4"} -> OPPONENT'
            ),
            "SP": (  # Sumire
                "TRIGGER: ON_POSITION_CHANGE (Once per turn)\n"
                "CONDITION: IS_SELF_MOVE_OR_ENERGY_PLACED\n"
                'EFFECT: DRAW(1); ADD_HEARTS(1) {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}'
            ),
            "HS": (  # Ginko
                "TRIGGER: CONSTANT\n"
                'CONDITION: COUNT_STAGE {FILTER="COST_GE_4, NOT_UNIT_CERISE_BOUQUET", MULTIPLIER=2}\n'
                "EFFECT: ADD_BLADES(SELF, MULTIPLIER)"
            ),
        },
        # --- 005 ---
        "005": {
            "": (  # Rin
                "TRIGGER: ON_PLAY\nCONDITION: SCORE_TOTAL {MIN=6}\nEFFECT: PLACE_ENERGY_WAIT(1) {ACTIVE=TRUE} -> PLAYER"
            ),
            "S": (  # You
                "TRIGGER: ON_LIVE_START\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                "EFFECT: HEART_SELECT(1) {CHOICES=[3, 4, 5]} -> CHOICE\n"
                'EFFECT: ADD_HEARTS(1) {HEART_TYPE=CHOICE} -> MEMBER {FILTER="NOT_GROUP_AQOURS, PLAYED_THIS_TURN"}'
            ),
            "N": (  # Ai
                "TRIGGER: ON_LEAVES\n"
                'CONDITION: BATON_TOUCH {FILTER="GROUP_ID=2, NOT_HAS_BLADE_HEART, COST_GE_10"}\n'
                "EFFECT: ACTIVATE_ENERGY(2)\n"
                'CONDITION: BATON_TOUCH {FILTER="GROUP_ID=2, NOT_HAS_BLADE_HEART, COST_GE_15"}\n'
                "EFFECT: DRAW(1)"
            ),
            "SP": (  # Ren
                "TRIGGER: ACTIVATED (Once per turn)\n"
                'COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}\n'
                'EFFECT: ADD_BLADES(COUNT_MEMBER_LIELLA_DISCARDED) -> SELF {DURATION="UNTIL_LIVE_END"}\n\n'
                "TRIGGER: ON_MOVE_TO_DISCARD\n"
                "CONDITION: MAIN_PHASE\n"
                "COST: PAY_ENERGY(1) (Optional)\n"
                'EFFECT: RECOVER_MEMBER(1) {FILTER="SELECTED_DISCARD"} -> CARD_HAND'
            ),
            "HS": (  # Kozue
                "TRIGGER: ON_LIVE_START\n"
                'COST: DISCARD_HAND(1) {FILTER="UNIT_DOLLCHESTRA"} (Optional)\n'
                'EFFECT: SELECT_MEMBER(1) {FILTER="UNIT_DOLLCHESTRA"} -> TARGET\n'
                'EFFECT: SET_COST(SELF, TARGET_BASE_COST_MINUS_1) {DURATION="UNTIL_LIVE_END"}\n'
                "CONDITION: COST_GE {VALUE=10}\n"
                'EFFECT: ADD_HEARTS(1) {HEART_TYPE=5, DURATION="UNTIL_LIVE_END"}'
            ),
        },
        # --- 006 ---
        "006": {
            "": (  # Maki
                "TRIGGER: ON_LIVE_START\nCONDITION: SUCCESS_LIVE_COUNT {MIN=2}\nEFFECT: DRAW(1)"
            ),
            "S": (  # Yoshiko
                "TRIGGER: ON_PLAY\n"
                "COST: TAP_SELF; DISCARD_HAND(1) (Optional)\n"
                'EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=1, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER'
            ),
            "N": (  # Kanata
                "TRIGGER: CONSTANT\n"
                "EFFECT: NOT_ACTIVATE_DURING_PHASE\n\n"
                "TRIGGER: ON_LIVE_SUCCESS\n"
                "CONDITION: COUNT_STAGE {MIN=2}\n"
                "EFFECT: TAP_SELF"
            ),
            "SP": (  # Kinako
                "TRIGGER: ACTIVATED (Once per turn)\n"
                'COST: MOVE_TO_DISCARD(3) {FROM="DECK_TOP"}\n'
                "EFFECT: POSITION_CHANGE(SELF)"
            ),
            "HS": (  # Hime
                "TRIGGER: ON_LIVE_START\n"
                'COST: DISCARD_HAND(2) {FILTER="SAME_GROUP"} (Optional)\n'
                'EFFECT: ADD_HEARTS(2) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}'
            ),
        },
        # --- 007 ---
        "007": {
            "": (  # Nozomi
                "TRIGGER: ON_PLAY\n"
                'CONDITION: BATON_TOUCH {FILTER="COST_LT_SELF"}\n'
                "EFFECT: DISCARD_UNTIL(3) -> PLAYER_AND_OPPONENT; DRAW_UNTIL(3) -> PLAYER_AND_OPPONENT"
            ),
            "S": (  # Hanamaru
                "TRIGGER: ON_LIVE_SUCCESS\n"
                "EFFECT: LOOK_DECK(4)\n"
                'EFFECT: MOVE_TO_HAND(1) {FILTER="HEARTS_GE_2, HEART_TYPE=4"}; DISCARD_REMAINDER'
            ),
            "N": (  # Setsuna
                "TRIGGER: ON_LIVE_START\n"
                "CONDITION: SUCCESS_LIVE_COUNT_EQUAL_OPPONENT\n"
                'EFFECT: ADD_HEARTS(2) {HEART_TYPE=2, DURATION="UNTIL_LIVE_END"}\n\n'
                "TRIGGER: ON_LIVE_SUCCESS\n"
                "CONDITION: EXTRA_HEARTS {MIN=1}\n"
                "EFFECT: DRAW(2); DISCARD_HAND(1)"
            ),
            "SP": (  # Mei
                "TRIGGER: ON_PLAY\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                "EFFECT: LOOK_DECK(5); REVEAL_PER_GROUP(1)\n"
                "EFFECT: MOVE_TO_HAND(3) (Optional); DISCARD_REMAINDER"
            ),
            "HS": (  # Lilienfelt
                "TRIGGER: ON_PLAY\n"
                "COST: DISCARD_HAND(2) (Optional)\n"
                'EFFECT: RECOVER_LIVE(1) {FILTER="UNIT_EDELNOTE"} -> CARD_HAND\n\n'
                "TRIGGER: CONSTANT\n"
                'CONDITION: COUNT_STAGE {FILTER="UNIT_EDELNOTE", NOT_SELF, MIN=1}\n'
                "EFFECT: ADD_BLADES(2) -> SELF"
            ),
        },
        # --- 008 ---
        "008": {
            "": (  # Hanayo
                "TRIGGER: CONSTANT\nCONDITION: SCORE_TOTAL {MIN=6}\nEFFECT: ADD_HEARTS(2) {HEART_TYPE=3} -> SELF"
            ),
            "S": (  # Mari
                "TRIGGER: CONSTANT\nCONDITION: OPP_EXTRA_HEARTS {MIN=2}\nEFFECT: BOOST_SCORE(1) -> PLAYER"
            ),
            "N": (  # Emma
                'TRIGGER: ACTIVATED (Once per turn)\nCOST: PLACE_UNDER(1) {FROM="ENERGY"}\nEFFECT: ACTIVATE_ENERGY(2)'
            ),
            "SP": (  # Shiki
                "TRIGGER: ON_PLAY\n"
                "COST: TAP_SELF; DISCARD_HAND(1) (Optional)\n"
                'EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=3, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER'
            ),
            "HS": (  # Izumi
                "TRIGGER: ON_PLAY\n"
                "COST: TAP_SELF; DISCARD_HAND(1) (Optional)\n"
                'EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=4, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER'
            ),
        },
        # --- 009 ---
        "009": {
            "": (  # Nico
                "TRIGGER: ACTIVATED (Once per turn)\n"
                "COST: DISCARD_HAND(2)\n"
                'EFFECT: RECOVER_LIVE(1) {FILTER="HEARTS_GE_3, HEART_TYPE=6"} -> CARD_HAND'
            ),
            "S": (  # Ruby
                "TRIGGER: ON_PLAY\n"
                "COST: PAY_ENERGY(1) (Optional)\n"
                "EFFECT: RECOVER_MEMBER(1) {FILTER=\"Unit='Saint Snow'\"} -> CARD_HAND\n"
                "CONDITION: RECOVERED_CARDS {MIN=1}\n"
                'EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}'
            ),
            "N": (  # Rina
                "TRIGGER: ON_PLAY\n"
                "COST: TAP_SELF; DISCARD_HAND(1) (Optional)\n"
                'EFFECT: LOOK_DECK(5) {FILTER="GROUP_ID=2, COST_GE_9, TYPE_MEMBER"}; MOVE_TO_HAND(1); DISCARD_REMAINDER'
            ),
            "SP": (  # Natsumi
                "TRIGGER: ON_LIVE_START\n"
                "EFFECT: LOOP(5)\n"
                '  COST: MOVE_TO_DISCARD(1) {FROM="DECK_TOP"} (Optional)\n'
                '  EFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}\n'
                '  CONDITION: DISCARDED_CARDS {FILTER="TYPE_LIVE"}\n'
                "  EFFECT: TAP_SELF; BREAK_LOOP"
            ),
            "HS": (  # Kaho (009 PR)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1); DISCARD_HAND(1)"
            ),
        },
        # --- 010 ---
        "010": {
            "": (  # Nozomi (010 PR)
                "TRIGGER: ON_PLAY\nCOST: DISCARD_HAND(1) (Optional)\nEFFECT: DRAW(2)"
            ),
            "S": (  # Ruby (010 PR)
                "TRIGGER: ON_PLAY\n"
                "COST: PAY_ENERGY(1) (Optional)\n"
                "EFFECT: RECOVER_MEMBER(1) {FILTER=\"Unit='Saint Snow'\"} -> CARD_HAND"
            ),
            "N": (  # Kasumi (010 PR)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1); DISCARD_HAND(1)"
            ),
            "SP": (  # Wien Margarete
                'TRIGGER: ON_PLAY\nEFFECT: POSITION_CHANGE_ALL {FILTER="AREA=CENTER"}'
            ),
            "HS": (  # Kaho (010 PR)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1); DISCARD_HAND(1)"
            ),
        },
        # --- 011 ---
        "011": {
            "": (  # Eli (011 N)
                "TRIGGER: ON_LIVE_START\n"
                "EFFECT: HEART_SELECT(1) {CHOICES=[4, 5, 6]} -> CHOICE\n"
                'EFFECT: ADD_HEARTS(SUCCESS_LIVE_COUNT) {HEART_TYPE=CHOICE, DURATION="UNTIL_LIVE_END"}'
            ),
            "S": (  # You (011 N)
                "TRIGGER: ON_PLAY\nCONDITION: SCORE_TOTAL {MIN=3}\nEFFECT: DRAW(1)"
            ),
            "N": (  # Mia Taylor
                "TRIGGER: ON_PLAY\n"
                "EFFECT: SELECT_MODE(1) -> PLAYER\n"
                "  OPTION: ユニーク名 | CONDITION: UNIQUE_NAMES_LIVE_DISCARD {MIN=3}; EFFECT: RECOVER_LIVE(1) -> CARD_HAND\n"
                "  OPTION: ユニークグループ | CONDITION: UNIQUE_GROUPS_LIVE_DISCARD {MIN=3}; EFFECT: RECOVER_LIVE(2) -> CARD_HAND"
            ),
            "SP": (  # Tomari Onitsuka
                "TRIGGER: CONSTANT\n"
                'CONDITION: AREA="LEFT_SIDE"\n'
                "EFFECT: ADD_HEARTS(3) {HEART_TYPE=2}\n\n"
                "TRIGGER: CONSTANT\n"
                'CONDITION: AREA="CENTER"\n'
                "EFFECT: ADD_HEARTS(3) {HEART_TYPE=3}\n\n"
                "TRIGGER: CONSTANT\n"
                'CONDITION: AREA="RIGHT_SIDE"\n'
                "EFFECT: ADD_HEARTS(3) {HEART_TYPE=5}"
            ),
            "HS": (  # Rurino (011 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
        },
        # --- 012 ---
        "012": {
            "": (  # Rin (012 N)
                "TRIGGER: ON_PLAY\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                'EFFECT: LOOK_DECK(4); MOVE_TO_HAND(1) {FILTER="TYPE_MEMBER, HEART_TYPE_ANY=[2,3]"}; DISCARD_REMAINDER'
            ),
            "S": (  # Yoshiko (012 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1); DISCARD_HAND(1)"
            ),
            "N": (  # Lanzhu Zhong
                "TRIGGER: ACTIVATED (Once per turn)\n"
                'COST: MOVE_UNDER_SELF(1) {FROM="ENERGY"}\n'
                'EFFECT: DRAW(1); ADD_HEARTS(1) {HEART_TYPE=1, DURATION="UNTIL_LIVE_END"}\n\n'
                "TRIGGER: ON_LIVE_SUCCESS\n"
                "CONDITION: SCORE_TOTAL_GE_OPPONENT\n"
                "EFFECT: PLACE_ENERGY_WAIT(COUNT_UNDER_SELF + 1) -> PLAYER"
            ),
            "SP": (  # Natsumi Onitsuka (012 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "HS": (  # Hime (012 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
        },
        # --- 013 ---
        "013": {
            "": (  # Umi (013 N)
                'TRIGGER: ON_PLAY\nEFFECT: TAP_OPPONENT(1) {FILTER="COST_LE_4"}'
            ),
            "S": (  # Dia (013 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1); DISCARD_HAND(1)"
            ),
            "N": (  # Shioriko (013 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "SP": (  # Wien Margarete (013 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "HS": (  # Ginko (013 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
        },
        # --- 014 ---
        "014": {
            "": (  # Rin (014 N)
                "TRIGGER: ON_PLAY\n"
                "COST: DISCARD_HAND(1) (Optional)\n"
                'EFFECT: LOOK_DECK(4); MOVE_TO_HAND(1) {FILTER="TYPE_MEMBER, HEART_TYPE_ANY=[5,6]"}; DISCARD_REMAINDER'
            ),
            "S": (  # Chisato (014 N)
                "TRIGGER: ON_PLAY\nCONDITION: ANY_MEMBER_MOVED_THIS_TURN\nEFFECT: DRAW(1)"
            ),
            "N": (  # Lanzhu (014 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "SP": (  # Kinako (014 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "HS": (  # Hime (014 N)
                'TRIGGER: ON_POSITION_CHANGE (Once per turn)\nEFFECT: ADD_BLADES(1) -> SELF {DURATION="UNTIL_LIVE_END"}'
            ),
        },
        # --- 015 ---
        "015": {
            "": (  # Maki (015 N)
                "TRIGGER: ON_PLAY\nCONDITION: SUCCESS_LIVE_SCORE_TOTAL {MIN=3}\nEFFECT: DRAW(1)"
            ),
            "S": (  # Yohane (015 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
            "N": (  # Shizuku (015 N)
                "TRIGGER: ON_LIVE_START\n"
                "CONDITION: HAS_HEART_TYPES {ALL=[1,2,3,4,5,6]}\n"
                'EFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}'
            ),
            "SP": (  # Sumire (015 N)
                'TRIGGER: ON_PLAY (Center Only)\nEFFECT: ADD_BLADES(2) -> SELF {DURATION="UNTIL_LIVE_END"}'
            ),
            "HS": (  # Lilienfelt (015 N)
                "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
            ),
        },
    }

    prefixes = {"": 0, "S": 1, "N": 2, "SP": 3, "HS": 4}

    # Apply repairs systematically
    for card_no in list(data.keys()):
        if "bp5" not in card_no:
            continue

        # Determine series and number
        found = False
        parts = card_no.split("-")
        if len(parts) < 3:
            continue

        # e.g. PL!N-bp5-001-AR
        prefix_part = parts[0].replace("PL!", "")
        set_part = parts[1]
        num_part = parts[2]

        if num_part in repairs:
            group_repairs = repairs[num_part]
            if prefix_part in group_repairs:
                logic = group_repairs[prefix_part]
                # Inject correct GROUP_ID if missing or wrong
                expected_group = prefixes.get(prefix_part, 99)
                # Note: We don't force GROUP_ID if logic is completely custom,
                # but many filters need it.
                data[card_no]["pseudocode"] = logic
                found = True

    # Batch 1 (010-015) - Adding logic simplified for these
    # ... more specific entries if needed ...

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    repair_batch_1()
