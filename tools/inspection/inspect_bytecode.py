import json
import os

from engine.models.opcodes import Opcode


def inspect_card():
    data_path = "data/cards_compiled.json"
    if not os.path.exists(data_path):
        print(f"Data not found at {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    member_db = full_data.get("member_db", {})

    target_card_no = "PL!HS-bp2-017-N"
    card = None
    card_id = None

    for cid, cdata in member_db.items():
        if cdata.get("card_no") == target_card_no:
            card = cdata
            card_id = cid
            break

    if not card:
        print(f"Card {target_card_no} not found in member_db")
        return

    print(f"Card: {target_card_no} (ID: {card_id})")

    abilities = card.get("abilities", [])
    for i, ab in enumerate(abilities):
        print(f"\nAbility {i}:")
        print(f"  Trigger: {ab.get('trigger')}")
        bytecode = ab.get("bytecode", [])
        print(f"  Bytecode: {bytecode}")

        # Decode bytecode
        for j in range(0, len(bytecode), 4):
            chunk = bytecode[j : j + 4]
            if not chunk or len(chunk) < 4:
                break
            op_val = chunk[0]
            negated = False
            if op_val >= 1000:
                negated = True
                op_val -= 1000

            try:
                op_name = Opcode(op_val).name
            except:
                op_name = f"UNKNOWN({op_val})"

            print(f"    [{j // 4}] {'NOT ' if negated else ''}{op_name} v={chunk[1]} a={chunk[2]} s={chunk[3]}")


if __name__ == "__main__":
    inspect_card()
