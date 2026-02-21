import json
import re

SUPPORTED_KEYS = {
    "DRAW",
    "ADD_BLADES",
    "ADD_HEARTS",
    "REDUCE_COST",
    "LOOK_DECK",
    "RECOVER_LIVE",
    "BOOST_SCORE",
    "RECOVER_MEMBER",
    "BUFF_POWER",
    "IMMUNITY",
    "MOVE_MEMBER",
    "SWAP_CARDS",
    "SEARCH_DECK",
    "ENERGY_CHARGE",
    "ACTIVATE_MEMBER",
    "ADD_TO_HAND",
    "MOVE_TO_DECK",
    "REVEAL_CARDS",
    "LOOK_AND_CHOOSE",
    "TAP_OPPONENT",
    "TAP_MEMBER",
    "PLAY_MEMBER_FROM_HAND",
    "SET_BLADES",
    "SET_HEARTS",
    "FORMATION_CHANGE",
    "NEGATE_EFFECT",
    "ORDER_DECK",
    "BATON_TOUCH_MOD",
    "SET_SCORE",
    "SWAP_ZONE",
    "TRANSFORM_COLOR",
    "TRIGGER_REMOTE",
    "REDUCE_HEART_REQ",
    "COLOR_SELECT",
    "REPLACE_EFFECT",
    "MODIFY_SCORE_RULE",
    "MOVE_TO_DISCARD",
    "GRANT_ABILITY",
    "INCREASE_HEART_COST",
    "REDUCE_YELL_COUNT",
    "PLAY_MEMBER_FROM_DISCARD",
    "PAY_ENERGY",
    "SELECT_MEMBER",
    "DRAW_UNTIL",
    "SELECT_PLAYER",
    "SELECT_LIVE",
    "REVEAL_UNTIL",
    "INCREASE_COST",
    "PREVENT_PLAY_TO_SLOT",
    "SWAP_AREA",
    "TRANSFORM_HEART",
    "SELECT_CARDS",
    "OPPONENT_CHOOSE",
    "PLAY_LIVE_FROM_DISCARD",
    "REDUCE_LIVE_SET_LIMIT",
    "PREVENT_ACTIVATE",
    "FLAVOR_ACTION",
    "META_RULE",
    "DISCARD_HAND",
    "ENERGY",
    "TAP_SELF",
    "SELECT_MODE",
    "CARD_DISCARD",
    "SELF",
    "PLAYER",
    "OPPONENT",
    "ENEMY",
    "MEMBER_NAMED",
    "ALL_MEMBERS",
    "ENEMY_STAGE",
    "HAS_KEYWORD",
    "HAS_MOVED",
    "COUNT_SUCCESS_LIVE",
    "HAS_LIVE_CARD",
    "TAP_PLAYER",
    "CARD_HAND",
    "TURN_1",
    "COUNT_STAGE",
    "OPTION",
    "ACTIVATE_ENERGY",
    "SUCCESS",
    "AREA",
    "TARGET_MEMBER",
    "IS_CENTER",
    "HAS_MEMBER",
    "HAS_COLOR",
    "COUNT_HAND",
    "COUNT_DISCARD",
    "LIFE_LEAD",
    "COUNT_GROUP",
    "GROUP_FILTER",
    "OPPONENT_HAS",
    "SELF_IS_GROUP",
    "MODAL_ANSWER",
    "COUNT_ENERGY",
    "COST_CHECK",
    "RARITY_CHECK",
    "HAND_HAS_NO_LIVE",
    "OPPONENT_HAND_DIFF",
    "SCORE_COMPARE",
    "HAS_CHOICE",
    "OPPONENT_CHOICE",
    "COUNT_HEARTS",
    "COUNT_BLADES",
    "OPPONENT_ENERGY_DIFF",
    "DECK_REFRESHED",
    "HAND_INCREASED",
    "COUNT_LIVE_ZONE",
    "BATON",
    "TYPE_CHECK",
    "COUNT_THIS_TURN",
    "BATON_TOUCH",
    "CHARGE_ENERGY",
    "TARGET_AREA",
    "POSITION_CHANGE",
    "TARGET_PLAYER",
    "REVEAL_HAND",
    "TYPE_MEMBER",
    "SUCCESS_LIVE",
}


def find_all_missing():
    try:
        with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return

    cards = []
    if "member_db" in data:
        cards.extend(data["member_db"].values())
    if "live_db" in data:
        cards.extend(data["live_db"].values())

    missing = set()
    for card in cards:
        raw_text = ""
        if "abilities" in card and card["abilities"]:
            raw_text = "\n".join([ab["raw_text"] for ab in card["abilities"] if "raw_text" in ab])
        if not raw_text:
            raw_text = card.get("ability_text", "")

        lines = raw_text.split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("TRIGGER:"):
                continue

            # Extract anything that looks like an opcode (UPPER_CASE)
            # Find words like MY_OPCODE(...) or MY_OPCODE {
            found = re.findall(r"([A-Z][A-Z0-9_]{2,})", line)
            for word in found:
                # Filter out obvious non-opcodes
                if word in ["EFFECT", "COST", "CONDITION", "PLAYER", "OPPONENT", "SELF"]:
                    continue
                if word not in SUPPORTED_KEYS:
                    missing.add(word)

    with open("missing_keys.txt", "w", encoding="utf-8") as f:
        f.write("MISSING_KEYS:" + ",".join(sorted(list(missing))))
    print("Done. Check missing_keys.txt")


if __name__ == "__main__":
    find_all_missing()
