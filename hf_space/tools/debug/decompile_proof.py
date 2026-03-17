import os
import sys

sys.path.append(os.getcwd())

from engine.models.opcodes import Opcode


def decompile(bytecode):
    instructions = []
    # Bytecode is in chunks of 4: [Opcode, Value, Attr, Slot]
    for i in range(0, len(bytecode), 4):
        chunk = bytecode[i : i + 4]
        if len(chunk) < 4:
            break
        op_val, val, attr, slot = chunk
        try:
            op_name = Opcode(op_val).name
        except ValueError:
            op_name = f"UNKNOWN({op_val})"

        instructions.append({"opcode": op_name, "value": val, "attr": attr, "slot": slot})
    return instructions


def main():
    # Card 0, Ability 2 (Original)
    orig_bc = [21, 3, 0, 1, 18, 1, 0, 7, 16, 3, 0, 7, 21, 1, 0, 7, 1, 0, 0, 0]

    # Corrected BC (My proposed fix)
    # [Opcode.SWAP_CARDS, 3, 0, 1] - Cost (Discard 3)
    # [Opcode.BOOST_SCORE, 3, 0, 1] - Effect (Boost 3)
    # [Opcode.RETURN, 0, 0, 0]      - End
    new_bc = [21, 3, 0, 1, 16, 3, 0, 1, 1, 0, 0, 0]

    print("=== DECOMPILING ORIGINAL [SD1-001 Ability 2] ===")
    for i, instr in enumerate(decompile(orig_bc)):
        print(f"Instr {i}: {instr['opcode']}({instr['value']}) [Attr: {instr['attr']}, Slot: {instr['slot']}]")

    print("\n=== DECOMPILING CORRECTED [My Proposal] ===")
    for i, instr in enumerate(decompile(new_bc)):
        print(f"Instr {i}: {instr['opcode']}({instr['value']}) [Attr: {instr['attr']}, Slot: {instr['slot']}]")


if __name__ == "__main__":
    main()
