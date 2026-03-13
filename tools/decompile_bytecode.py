#!/usr/bin/env python3
"""
Bytecode decompiler - converts bytecode to readable pseudocode.

This module consolidates bytecode decompilation onto the shared readable layer.
It uses the shared bytecode_readable module for decoding, ensuring consistency
across all tools and preventing drift from bytecode layout changes.

Default: Uses the shared decode_bytecode() function which handles 5-word chunks.
Custom decompile(): For backward compatibility, also provides a simplified 
    pseudocode decompiler that formats bytecode as "COST: X; CONDITION: Y; EFFECT: Z"
"""

import json
import os
import sys
from typing import List

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from engine.models.bytecode_readable import (
    CONDITION_NAMES,
    OPCODE_NAMES,
    decode_bytecode,
    decode_filter,
)
from engine.models.generated_metadata import TARGETS
from engine.models.opcodes import Opcode

# Build reverse lookup for targets from generated metadata
TARGET_REVERSE = {v: k for k, v in TARGETS.items()}


def decompile(bytecode: List[int]) -> str:
    """
    Decompile a bytecode sequence (list of ints) into simplified pseudocode.
    
    Format: "COST: X; CONDITION: Y; EFFECT: Z"
    
    This is a higher-level abstraction than decode_bytecode() which shows
    individual decoded chunks. This function groups instructions by type.
    
    Note: Uses shared OPCODE_NAMES, CONDITION_NAMES from bytecode_readable module
    to ensure consistency with other tools. All bytecode parsing uses 5-word chunks.
    """
    if not bytecode:
        return ""

    # Use shared decoded output (5-word chunks)
    full_decode = decode_bytecode(bytecode)

    conditions = []
    effects = []
    costs = []

    # Parse the 5-word chunks
    chunks = [bytecode[i : i + 5] for i in range(0, len(bytecode), 5)]

    for chunk in chunks:
        if len(chunk) < 5:
            chunk = chunk + [0] * (5 - len(chunk))

        op_val, val, attr_low, attr_high, slot = chunk
        a = ((attr_high & 0xFFFFFFFF) << 32) | (attr_low & 0xFFFFFFFF)

        # Handle Negated Conditions
        is_negated = False
        base_op = op_val
        if 1000 <= op_val < 1300:
            is_negated = True
            base_op = op_val - 1000

        if base_op == Opcode.NOP:
            continue
        if base_op == Opcode.RETURN:
            break

        # 1. Conditions (200-299)
        if 200 <= base_op <= 299:
            cond_type_name = CONDITION_NAMES.get(base_op, f"COND_{base_op}")

            # Extract comparison from slot
            comp_val = (slot >> 4) & 0x0F
            comp_map = {0: "GE", 1: "LE", 2: "GT", 3: "LT", 4: "EQ"}
            comp_str = comp_map.get(comp_val, "GE")

            params = []
            if val != 0:
                params.append(
                    f"MIN={val}" if comp_str == "GE" else f"VALUE={val}"
                )

            if cond_type_name == "COUNT_GROUP":
                try:
                    from engine.models.enums import Group

                    group_name = Group(a).to_japanese_name()
                    params.append(f'GROUP="{group_name}"')
                except:
                    params.append(f"GROUP_ID={a}")

            if cond_type_name == "HAS_COLOR":
                colors = {
                    1: "PINK",
                    2: "RED",
                    3: "YELLOW",
                    4: "GREEN",
                    5: "BLUE",
                    6: "PURPLE",
                }
                params.append(f"COLOR={colors.get(a, a)}")

            if comp_str != "GE":
                params.append(f"COMPARE={comp_str}")

            # Negation
            prefix = "NOT_" if is_negated else ""
            cond_str = f"{prefix}{cond_type_name}"
            if params:
                cond_str += " {" + ", ".join(params) + "}"
            conditions.append(cond_str)

        # 2. Effects (0-99)
        elif 0 <= base_op <= 99:
            # Special case: SWAP_CARDS with slot 1 is used for DISCARD_HAND cost
            if base_op == Opcode.SWAP_CARDS and slot == 1:
                costs.append(f"DISCARD_HAND({val})")
                continue

            # Get opcode name from shared dict
            name = OPCODE_NAMES.get(base_op, f"OP_{base_op}")

            # Target from lower 4 bits of slot
            target_value = slot & 0xF
            target_str = TARGET_REVERSE.get(target_value, f"TARGET_{target_value}")

            # Params - extract from attr
            params = []

            # Unit Filter (Bit 16 + Bits 17-23)
            if a & 0x10000:
                unit_id = (a >> 17) & 0x7F
                try:
                    from engine.models.enums import Unit

                    unit_name = Unit(unit_id).name
                    params.append(f"UNIT={unit_name}")
                except:
                    params.append(f"UNIT_ID={unit_id}")

            # Group Filter (Bit 4 + Bits 5-11)
            if a & 0x10:
                group_id = (a >> 5) & 0x7F
                try:
                    from engine.models.enums import Group

                    group_name = Group(group_id).to_japanese_name()
                    params.append(f'GROUP="{group_name}"')
                except:
                    params.append(f"GROUP_ID={group_id}")

            # Type Filter (Bits 2-3)
            type_val = (a >> 2) & 0x03
            if type_val == 1:
                params.append("TYPE=MEMBER")
            elif type_val == 2:
                params.append("TYPE=LIVE")

            # Cost Filter (Bit 24 + Bits 25-29 + Bit 30)
            if a & (1 << 24):
                cost_val = (a >> 25) & 0x1F
                cost_mode = "LE" if a & (1 << 30) else "GE"
                params.append(f"COST_{cost_mode}={cost_val}")

            # Color Filter (Bit 31)
            if a & (1 << 31):
                colors = {
                    1: "PINK",
                    2: "RED",
                    3: "YELLOW",
                    4: "GREEN",
                    5: "BLUE",
                    6: "PURPLE",
                }
                color_val = a & 0x7F
                if color_val in colors:
                    params.append(f"COLOR={colors[color_val]}")

            param_str = ""
            if params:
                param_str = " {" + ", ".join(params) + "}"

            effects.append(f"{name}({val}) -> {target_str}{param_str}")

    # Format components
    lines = []
    if costs:
        lines.append("COST: " + "; ".join(costs))
    if conditions:
        lines.append("CONDITION: " + ", ".join(conditions))
    if effects:
        lines.append("EFFECT: " + "; ".join(effects))

    return "\n".join(lines)


def main():
    """
    CLI entry point for bytecode decompilation.
    
    Usage: decompile_bytecode.py '<bytecode_json_array>' [--full]
    
    The script accepts bytecode as a JSON array on the command line.
    
    Args:
        bytecode_json_array: JSON-encoded list of integers, e.g., '[101, 1, 3, 0, 0]'
        --full: If specified, use full decode_bytecode() output instead of simplified format
    """
    if len(sys.argv) < 2:
        print("Bytecode Decompiler - Consolidation onto Shared Readable Layer")
        print()
        print("Usage: decompile_bytecode.py '<bytecode_json_array>' [--full]")
        print()
        print("Arguments:")
        print("  bytecode_json_array  JSON-encoded list of integers")
        print("  --full               Use full decode_bytecode() output (default: simplified format)")
        print()
        print("Examples:")
        print("  decompile_bytecode.py '[101, 1, 3, 0, 0]'")
        print("  decompile_bytecode.py '[101, 1, 3, 0, 0]' --full")
        return

    use_full = "--full" in sys.argv
    bytecode_arg = sys.argv[1]

    try:
        bc = json.loads(bytecode_arg)

        if not isinstance(bc, list):
            print(f"Error: Expected JSON array, got {type(bc)}")
            return

        if use_full:
            # Use full decoded bytecode output (5-word chunks with legend)
            result = decode_bytecode(bc)
        else:
            # Use simplified pseudocode format
            result = decompile(bc)

        print(result)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
