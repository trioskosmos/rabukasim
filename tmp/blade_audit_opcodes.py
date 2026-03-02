import json
import os

C_COUNT_BLADES = 224
C_BLADE_COMPARE = 221
C_TOTAL_BLADES = 222 # Wait, is there a TOTAL_BLADES opcode?

def audit():
    cards_compiled_path = "data/cards_compiled.json"
    if not os.path.exists(cards_compiled_path):
        print("cards_compiled.json not found")
        return

    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = []
    
    for db_key in ["member_db", "live_db"]:
        db = data.get(db_key, {})
        for cid, card_data in db.items():
            card_no = card_data.get("card_no", "Unknown")
            name = card_data.get("name", "Unknown")
            for i, ability in enumerate(card_data.get("abilities", [])):
                bytecode = ability.get("bytecode", [])
                for j in range(0, len(bytecode), 5):
                    if j + 4 >= len(bytecode):
                        break
                    
                    op = bytecode[j]
                    if op in [224, 221, 222]:
                        slot = bytecode[j+4] & 0x0F
                        status = "CHOICE" if slot == 10 else f"SLOT_{slot}"
                        report.append(f"Card {card_no} ({name}) - Op {op} - Slot: {status}")

    with open("reports/blade_opcodes.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("Done")

if __name__ == "__main__":
    audit()
