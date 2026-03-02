
import json
import os

# Opcode constants (Updated to match logic.rs and common sense)
C_COUNT_BLADES = 224
C_COUNT_HEARTS = 223
C_COUNT_STAGE = 203

def audit():
    cards_compiled_path = "data/cards_compiled.json"
    if not os.path.exists(cards_compiled_path):
        print("cards_compiled.json not found")
        return

    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = []
    report.append("=== Slot-Aware Condition Audit (Corrected) ===")
    
    # cards_compiled.json has "member_db" and "live_db"
    for db_key in ["member_db", "live_db"]:
        db = data.get(db_key, {})
        for cid, card_data in db.items():
            card_no = card_data.get("card_no", "Unknown")
            name = card_data.get("name", "Unknown")
            for i, ability in enumerate(card_data.get("abilities", [])):
                bytecode = ability.get("bytecode", [])
                # Bytecode is a list of integers here, 5 integers per instruction
                for j in range(0, len(bytecode), 5):
                    if j + 4 >= len(bytecode):
                        break
                    
                    op = bytecode[j]
                    val = bytecode[j+1]
                    attr_low = bytecode[j+2]
                    attr_high = bytecode[j+3]
                    packed_slot = bytecode[j+4]
                    
                    # Unpack slot
                    slot = packed_slot & 0x0F
                    comp = (packed_slot >> 4) & 0x0F
                    area = (packed_slot >> 28) & 0x07
                    
                    is_target_opcode = op in [C_COUNT_BLADES, C_COUNT_HEARTS, C_COUNT_STAGE]
                    
                    if is_target_opcode:
                        status = "OK"
                        # Context Area is 4. If slot is 0 and area is 0, it's Left Slot.
                        # Choice Target is 10.
                        if slot == 0 and area == 0:
                            status = "DEFAULT LEFT SLOT"
                        elif slot == 10:
                            status = "CHOICE TARGET"
                        elif slot == 4:
                            status = "CONTEXT AREA"
                        
                        report.append(f"Card {card_no} ({name}) - Ability {i} - Op {op}: Slot={slot}, Area={area}, Comp={comp} [{status}]")

    with open("reports/final_blade_audit.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"Audit complete. Report written to reports/final_blade_audit.txt")

if __name__ == "__main__":
    audit()
