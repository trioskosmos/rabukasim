import json
import os
import sys

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from engine.models.ability import TargetType
from engine.models.opcodes import Opcode


def decompile(bytecode):
    """Decompile a bytecode sequence (list of ints) into pseudocode."""
    if not bytecode:
        return ""

    # Split into instructions (groups of 4)
    instructions = [bytecode[i : i + 4] for i in range(0, len(bytecode), 4)]

    conditions = []
    effects = []
    costs = []

    # Identify instructions
    for instr in instructions:
        if len(instr) < 4:
            continue

        op_val, val, attr, packed_slot = instr

        # Handle Negated Conditions
        is_negated = False
        if op_val >= 1000:
            is_negated = True
            op_val -= 1000

        if op_val == Opcode.NOP:
            continue
        if op_val == Opcode.RETURN:
            break

        # 1. Conditions (200-299)
        if 200 <= op_val <= 299:
            try:
                opcode_name = Opcode(op_val).name
                cond_type_name = opcode_name.replace("CHECK_", "")

                # Unpack comparison and slot
                slot = packed_slot & 0x0F
                comp_val = (packed_slot >> 4) & 0x0F
                comp_map = {0: "GE", 1: "LE", 2: "GT", 3: "LT", 4: "EQ"}
                comp_str = comp_map.get(comp_val, "GE")

                params = []
                if val != 0:
                    params.append(f"MIN={val}" if comp_str == "GE" else f"VALUE={val}")

                if cond_type_name == "COUNT_GROUP":
                    from engine.models.enums import Group

                    try:
                        group_name = Group(attr).to_japanese_name()
                        params.append(f'GROUP="{group_name}"')
                    except:
                        params.append(f"GROUP_ID={attr}")

                if cond_type_name == "HAS_COLOR":
                    colors = {1: "PINK", 2: "RED", 3: "YELLOW", 4: "GREEN", 5: "BLUE", 6: "PURPLE"}
                    params.append(f"COLOR={colors.get(attr, attr)}")

                if comp_str != "GE":
                    params.append(f"COMPARE={comp_str}")

                # Negation
                prefix = "NOT_" if is_negated else ""
                cond_str = f"{prefix}{cond_type_name}"
                if params:
                    cond_str += " {" + ", ".join(params) + "}"
                conditions.append(cond_str)
            except ValueError:
                pass

        # 2. Effects (0-99)
        elif 0 <= op_val <= 99:
            # Special case: COST?
            # In Ability.compile, SWAP_CARDS with slot 1 is used for DISCARD_HAND cost
            if op_val == Opcode.SWAP_CARDS and packed_slot == 1:
                costs.append(f"DISCARD_HAND({val})")
                continue

            try:
                op = Opcode(op_val)
                name = op.name

                # Target
                target_map = {
                    TargetType.SELF: "SELF",
                    TargetType.PLAYER: "PLAYER",
                    TargetType.OPPONENT: "OPPONENT",
                    TargetType.ALL_PLAYERS: "ALL_PLAYERS",
                    TargetType.CARD_HAND: "CARD_HAND",
                    TargetType.CARD_DISCARD: "CARD_DISCARD",
                    TargetType.MEMBER_SELF: "MEMBER_SELF",
                }
                target_str = target_map.get(packed_slot, f"TARGET_{packed_slot}")

                # Params
                params = []
                # Bit 7 of attr is ALL
                is_all = (attr & 0x80) != 0
                if is_all:
                    params.append("ALL")

                # Colors/Groups in effects
                if name in ["ADD_HEARTS", "BUFF_POWER"]:
                    colors = {1: "PINK", 2: "RED", 3: "YELLOW", 4: "GREEN", 5: "BLUE", 6: "PURPLE"}
                    if (attr & 0x7F) in colors:
                        params.append(f"COLOR={colors[attr & 0x7F]}")

                param_str = ""
                if params:
                    param_str = " {" + ", ".join(params) + "}"

                effects.append(f"{name}({val}) -> {target_str}{param_str}")
            except ValueError:
                pass

    # Format components
    lines = []
    # Trigger? We usually can't tell trigger from bytecode alone
    # unless we associate it with the card.

    if costs:
        lines.append("COST: " + "; ".join(costs))
    if conditions:
        lines.append("CONDITION: " + ", ".join(conditions))
    if effects:
        lines.append("EFFECT: " + "; ".join(effects))

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: decompile_bytecode '<bytecode_json_array>'")
        return

    try:
        bc = json.loads(sys.argv[1])
        print(decompile(bc))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
