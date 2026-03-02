import json
import os

def audit():
    path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\cards_compiled.json"
    if not os.path.exists(path):
        print("Compiled data not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = []
    # Opcodes: 224 (BLADES), 223 (HEARTS), 140 (STAGE)
    target_opcodes = {223, 224, 140}
    
    for card_no, card in data.items():
        if "abilities" not in card:
            continue
            
        for i, ability in enumerate(card["abilities"]):
            if "conditions" not in ability:
                continue
                
            for cond in ability["conditions"]:
                opcode = cond.get("opcode")
                if opcode in target_opcodes:
                    slot = cond.get("slot", 0)
                    slot_val = slot & 0xFF
                    report.append({
                        "card_no": card_no,
                        "ability": i,
                        "opcode": opcode,
                        "slot_packed": slot,
                        "slot_resolved": slot_val,
                        "pseudocode": card.get("pseudocode", "N/A")
                    })

    # Print summary
    print(f"Total targeted/count conditions found: {len(report)}")
    print("-" * 50)
    for entry in report:
        if entry["slot_resolved"] == 10: # Choice Target
            print(f"[MATCH] {entry['card_no']} (Ab {entry['ability']}): Op {entry['opcode']}, Slot {entry['slot_resolved']}")
        elif entry["slot_resolved"] > 0 and entry["slot_resolved"] <= 3:
            print(f"[STAGE] {entry['card_no']} (Ab {entry['ability']}): Op {entry['opcode']}, Slot {entry['slot_resolved']}")
        # Skip printing all Slot 0 ones unless we want to find potential errors
        elif "CHOICE_TARGET" in entry["pseudocode"] or "SELECT_MEMBER" in entry["pseudocode"]:
             print(f"[POTENTIAL MISSING TARGET] {entry['card_no']} (Ab {entry['ability']}): Op {entry['opcode']}, Slot {entry['slot_resolved']}")
             print(f"  Code: {entry['pseudocode']}")

if __name__ == "__main__":
    audit()
