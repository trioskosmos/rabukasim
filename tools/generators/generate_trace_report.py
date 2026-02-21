import json
import os

# Frontend Translation Map (Based on ability_translator.js)
# This maps the integer opcodes from the backend to human-readable keys used in the frontend.
EffectType = {
    0: "DRAW",
    1: "ADD_BLADES",
    2: "ADD_HEARTS",
    3: "REDUCE_COST",
    4: "LOOK_DECK",
    5: "RECOVER_LIVE",
    6: "BOOST_SCORE",
    7: "RECOVER_MEMBER",
    8: "BUFF_POWER",
    9: "IMMUNITY",
    10: "MOVE_MEMBER",
    11: "SWAP_CARDS",
    12: "SEARCH_DECK",
    13: "ENERGY_CHARGE",
    14: "NEGATE_EFFECT",
    15: "ORDER_DECK",
    16: "META_RULE",
    17: "SELECT_MODE",
    18: "MOVE_TO_DECK",
    19: "TAP_OPPONENT",
    20: "PLACE_UNDER",
    21: "RESTRICTION",
    22: "BATON_TOUCH_MOD",
    23: "SET_SCORE",
    24: "SWAP_ZONE",
    25: "TRANSFORM_COLOR",
    26: "REVEAL_CARDS",
    27: "LOOK_AND_CHOOSE",
    28: "CHEER_REVEAL",
    29: "ACTIVATE_MEMBER",
    30: "ADD_TO_HAND",
    31: "SET_BLADES",
    32: "SET_HEARTS",
    33: "FORMATION_CHANGE",
    34: "REPLACE_EFFECT",
    35: "TRIGGER_REMOTE",
    36: "REDUCE_HEART_REQ",
    37: "COLOR_SELECT",
    38: "MODIFY_SCORE_RULE",
    39: "PLAY_MEMBER_FROM_HAND",
    40: "TAP_MEMBER",
    41: "MOVE_TO_DISCARD",
    42: "GRANT_ABILITY",
    43: "INCREASE_HEART_COST",
    44: "REDUCE_YELL_COUNT",
    45: "PLAY_MEMBER_FROM_DISCARD",
    46: "PAY_ENERGY",
    47: "SELECT_MEMBER",
    48: "DRAW_UNTIL",
    49: "SELECT_PLAYER",
    50: "SELECT_LIVE",
    51: "REVEAL_UNTIL",
    52: "INCREASE_COST",
    53: "PREVENT_PLAY_TO_SLOT",
    54: "SWAP_AREA",
    55: "TRANSFORM_HEART",
    56: "SELECT_CARDS",
    57: "OPPONENT_CHOOSE",
    58: "PLAY_LIVE_FROM_DISCARD",
    59: "REDUCE_LIVE_SET_LIMIT",
    72: "PREVENT_ACTIVATE",
    81: "ACTIVATE_ENERGY",
    99: "FLAVOR_ACTION",
}

# Mapping for Trigger Types
TriggerType = {
    0: "NONE",
    1: "ON_PLAY",
    2: "ON_LIVE_START",
    3: "ON_LIVE_SUCCESS",
    4: "TURN_START",
    5: "TURN_END",
    6: "CONSTANT",
    7: "ON_ACTIVATE",
    8: "ON_LEAVES",
    9: "ON_REVEAL",
    10: "ON_POSITION_CHANGE",
}

# Simplified Description Templates (English) to simulate frontend rendering
DescTemplates = {
    "DRAW": "Draw {val} card(s)",
    "ADD_BLADES": "Gain {val} Blade(s)",
    "ADD_HEARTS": "Gain {val} Heart(s)",
    "REDUCE_COST": "Cost -{val}",
    "LOOK_DECK": "Look at top {val}",
    "RECOVER_LIVE": "Retrieve {val} Live(s)",
    "BOOST_SCORE": "Score +{val}",
    "RECOVER_MEMBER": "Retrieve {val} Member(s)",
    "BUFF_POWER": "Power +{val}",
    "IMMUNITY": "Immune to effects",
    "MOVE_MEMBER": "Move Member",
    "SWAP_CARDS": "Swap Hand cards",
    "SEARCH_DECK": "Search Deck",
    "ENERGY_CHARGE": "Charge {val} Energy",
    "ACTIVATE_MEMBER": "Activate Ability",
    "ADD_TO_HAND": "Add to Hand",
    "SET_BLADES": "Set Blades to {val}",
    "SET_HEARTS": "Set Hearts to {val}",
    "FORMATION_CHANGE": "Formation Change",
    "REORDER_DECK": "Reorder Deck",
    "PLAY_MEMBER_FROM_HAND": "Play from Hand",
    "TAP_MEMBER": "Tap Member",
    "ACTIVATE_ENERGY": "Activate Energy",
    "UNKNOWN": "Opcode {op}",
}


def decode_bytecode(bytecode):
    """
    Rudimentary decoder to map opcode sequences to human-readable strings.
    This is not a full VM, just a tracer.
    """
    decoded = []
    i = 0
    while i < len(bytecode):
        op = bytecode[i]

        # Opcodes >= 200 are typically conditions or control flow in specific ranges
        # Opcodes < 200 are typically effects
        if op < 200:
            op_name = EffectType.get(op, f"OP_{op}")
            # Try to grab a value if it looks like a parameter follows
            # This is heuristic-based since we don't have the full schema here
            val = "?"
            if i + 1 < len(bytecode):
                # Most simple effects take 1 arg. Validating if next is a small int helps.
                if bytecode[i + 1] < 10000:
                    val = str(bytecode[i + 1])

            template = DescTemplates.get(op_name, DescTemplates["UNKNOWN"])
            desc = template.format(val=val, op=op)

            decoded.append({"opcode": op, "name": op_name, "description_estimate": desc})
        else:
            decoded.append(
                {"opcode": op, "name": "CONDITION_OR_CONTROL", "description_estimate": f"Control/Cond Op: {op}"}
            )

        # Simple step forward. A real decompiler would need to know arg counts.
        # For tracing purposes, we just list the opcodes found.
        i += 1

    return decoded


def main():
    compiled_path = "data/cards_compiled.json"
    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Cards to specifically trace (based on previous user context)
    target_card_nos = ["PL!-bp3-001-P", "PL!HS-bp1-004-P", "PL!N-bp1-002-P"]

    report_data = {"generated_at": "2026-01-31T12:00:00Z", "cards": []}

    print("Generating trace report...")
    for card_no in target_card_nos:
        # Find card in member_db
        card_data = None
        for cid, c in db.get("member_db", {}).items():
            if c.get("card_no") == card_no:
                card_data = c
                break

        if not card_data:
            print(f"Warning: Card {card_no} not found in DB.")
            continue

        print(f"Tracing {card_no}...")
        card_entry = {"card_no": card_no, "name": card_data.get("name", "Unknown"), "abilities": []}

        abilities = card_data.get("abilities", [])
        for idx, ability in enumerate(abilities):
            trigger_id = ability.get("trigger", 0)
            trigger_name = TriggerType.get(trigger_id, f"TRIG_{trigger_id}")
            bytecode = ability.get("bytecode", [])

            trace = decode_bytecode(bytecode)

            card_entry["abilities"].append(
                {
                    "index": idx,
                    "trigger_id": trigger_id,
                    "trigger_name": trigger_name,
                    "trace": trace,
                    "raw_bytecode": bytecode,
                }
            )

        report_data["cards"].append(card_entry)

    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    report_file = "reports/trace_report_latest.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"Report saved to {report_file}")


if __name__ == "__main__":
    main()
