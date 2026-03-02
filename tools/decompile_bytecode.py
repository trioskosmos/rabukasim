import json
import os
import sys

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from engine.models.generated_metadata import CONDITIONS, OPCODES, TARGETS
from engine.models.opcodes import Opcode

# Build reverse lookup dictionaries
OPCODE_REVERSE = {v: k for k, v in OPCODES.items()}
CONDITION_REVERSE = {v: k for k, v in CONDITIONS.items()}
TARGET_REVERSE = {v: k for k, v in TARGETS.items()}


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
            # Use reverse lookup from CONDITIONS dict
            cond_type_name = CONDITION_REVERSE.get(op_val, f"COND_{op_val}")

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

        # 2. Effects (0-99)
        elif 0 <= op_val <= 99:
            # Special case: COST?
            # In Ability.compile, SWAP_CARDS with slot 1 is used for DISCARD_HAND cost
            if op_val == Opcode.SWAP_CARDS and packed_slot == 1:
                costs.append(f"DISCARD_HAND({val})")
                continue

            # Get opcode name using reverse lookup
            name = OPCODE_REVERSE.get(op_val, f"OP_{op_val}")

            # Target - reverse lookup from TARGETS dict
            # Target is stored in lower 4 bits of packed_slot
            target_value = packed_slot & 0xF
            target_str = TARGET_REVERSE.get(target_value, f"TARGET_{target_value}")

            # Params - extract from attr
            params = []

            # Unit Filter (Bit 16 + Bits 17-23)
            if attr & 0x10000:
                unit_id = (attr >> 17) & 0x7F
                try:
                    from engine.models.enums import Unit

                    unit_name = Unit(unit_id).name
                    params.append(f"UNIT={unit_name}")
                except:
                    params.append(f"UNIT_ID={unit_id}")

            # Group Filter (Bit 4 + Bits 5-11)
            if attr & 0x10:
                group_id = (attr >> 5) & 0x7F
                try:
                    from engine.models.enums import Group

                    group_name = Group(group_id).to_japanese_name()
                    params.append(f'GROUP="{group_name}"')
                except:
                    params.append(f"GROUP_ID={group_id}")

            # Type Filter (Bits 2-3)
            type_val = (attr >> 2) & 0x03
            if type_val == 1:
                params.append("TYPE=MEMBER")
            elif type_val == 2:
                params.append("TYPE=LIVE")

            # Cost Filter (Bit 24 + Bits 25-29 + Bit 30)
            if attr & (1 << 24):
                cost_val = (attr >> 25) & 0x1F
                cost_mode = "LE" if attr & (1 << 30) else "GE"
                params.append(f"COST_{cost_mode}={cost_val}")

            # Color Filter (Bit 31)
            if attr & (1 << 31):
                colors = {1: "PINK", 2: "RED", 3: "YELLOW", 4: "GREEN", 5: "BLUE", 6: "PURPLE"}
                color_val = attr & 0x7F
                if color_val in colors:
                    params.append(f"COLOR={colors[color_val]}")

            param_str = ""
            if params:
                param_str = " {" + ", ".join(params) + "}"

            effects.append(f"{name}({val}) -> {target_str}{param_str}")

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
