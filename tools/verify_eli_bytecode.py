import json
import os

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

member_db = data.get("member_db", {})
target_card_no = "PL!-pb1-011-R"
card = None

for cid, cdata in member_db.items():
    if cdata.get("card_no") == target_card_no:
        card = cdata
        break

if card:
    print(f"Card: {card['name']} ({card['card_no']}) | ID: {card.get('card_id')}")
    for i, ab in enumerate(card["abilities"]):
        print(f"Ability {i}:")
        bc = ab["bytecode"]
        # Look for 208 (0xD0) in bytecode
        # Structure: [opcode, val, attr, slot]
        for j in range(0, len(bc), 4):
            op = bc[j]
            val = bc[j+1]
            attr = bc[j+2]
            slot = bc[j+3]
            if op == 208:
                print(f"  [{j}] Op: {op}, Val: {val}, Attr: {attr} (0x{attr:04X}), Slot: {slot}")
                if attr & 0x8000:
                    print("  SUCCESS: UNIQUE_NAMES flag (0x8000) is SET.")
                else:
                    print("  FAILURE: UNIQUE_NAMES flag is NOT set.")
else:
    print(f"Card {target_card_no} not found in member_db.")
