import json
import os
import sys

# Mock Opcode for standalone run or try import
try:
    sys.path.append(os.getcwd())
    from engine.models.opcodes import Opcode
except:
    Opcode = None


def get_opcode_name(op_val):
    if Opcode:
        try:
            return Opcode(op_val).name
        except:
            pass
    return str(op_val)


def main():
    try:
        with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
            manual = json.load(f)
    except Exception as e:
        print(f"Error loading manual: {e}")
        return

    # Load Source Text from cards.json
    try:
        with open("data/cards.json", "r", encoding="utf-8") as f:
            raw_cards = json.load(f)
    except:
        raw_cards = {}

    # Load Bytecode from cards_compiled.json
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            comp_data = json.load(f)
            member_db = comp_data.get("member_db", {})
    except:
        member_db = {}

    # Map card_no -> ID for bytecode lookup
    # member_db is ID -> Data
    no_to_id_map = {}
    for cid, c in member_db.items():
        if "card_no" in c:
            no_to_id_map[c["card_no"]] = c

    keys = sorted(manual.keys())
    print(f"Total entries: {len(keys)}")

    for k in keys:
        print(f"=== KEY: {k} ===")

        # 1. Original Text
        raw = raw_cards.get(k, {})
        text = raw.get("ability", raw.get("text", "")).replace("\n", " ")
        if not text and k in no_to_id_map:
            # Fallback to compiled text
            text = no_to_id_map[k].get("ability_text", "")

        print(f"TXT: {text}")

        # 2. Bytecode
        cdata = no_to_id_map.get(k)
        if cdata:
            for i, ab in enumerate(cdata.get("abilities", [])):
                trig = ab.get("trigger", "?")
                bc = ab.get("bytecode", [])

                ops = []
                for j in range(0, len(bc), 4):
                    chunk = bc[j : j + 4]
                    if len(chunk) < 4:
                        break
                    opcode = chunk[0]
                    neg = False
                    if opcode >= 1000:
                        neg = True
                        opcode -= 1000

                    op_name = get_opcode_name(opcode)
                    ops.append(f"{'!' if neg else ''}{op_name}({chunk[1]},{chunk[2]},{chunk[3]})")

                print(f"ABC[{i}]: T={trig} | {'; '.join(ops)}")
        else:
            print("ABC: <MISSING IN COMPILED DB>")

        print("-" * 20)
        print("")


if __name__ == "__main__":
    main()
