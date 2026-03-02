
import json
import os

# Opcode constants
C_COUNT_BLADES = 224
C_COUNT_HEARTS = 223
C_COUNT_STAGE = 203
C_BLADE_COMPARE = 221

# Slot constants
SLOT_LEFT = 0
SLOT_CENTER = 1
SLOT_RIGHT = 2
SLOT_CONTEXT = 4
SLOT_CHOICE = 10

def audit():
    cards_compiled_path = "data/cards_compiled.json"
    if not os.path.exists(cards_compiled_path):
        print("cards_compiled.json not found")
        return

    with open(cards_compiled_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = []
    report.append("=== Slot-Aware Condition Audit ===")
    
    for card_no, card_data in data.items():
        name = card_data.get("name", "Unknown")
        for i, ability in enumerate(card_data.get("abilities", [])):
            bytecode = ability.get("bytecode", [])
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
                    if slot == 0 and area == 0:
                        # Slot 0 with area 0 is "Left Slot" in stage. 
                        # This might be intended, or it might be a missing target (defaulting to 0).
                        # We should flag it if the card text implies selecting someone or checking a specific member.
                        status = "POTENTIAL MISSING TARGET (Defaults to Left Slot)"
                    
                    report.append(f"Card {card_no} ({name}) - Ability {i} - Op {op}: Slot={slot}, Area={area}, Comp={comp} [{status}]")

    with open("reports/final_blade_audit.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"Audit complete. Report written to reports/final_blade_audit.txt")

if __name__ == "__main__":
    audit()
