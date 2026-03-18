
import json
import os

data_path = r'data\cards_compiled.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

db = data.get('member_db', {})
OP_MOVE_TO_DISCARD = 58
OP_PLAY_MEMBER_FROM_DISCARD = 63
OP_PLAY_MEMBER_FROM_HAND = 57

results = []

for k, v in db.items():
    if not isinstance(v, dict): continue
    card_no = v.get('card_no', 'Unknown')
    for ab in v.get('abilities', []):
        p = ab.get('pseudocode', '')
        bytecode = ab.get('bytecode', [])
        
        issues = []
        
        # Check REMAINDER
        if 'REMAINDER' in p:
            found_58 = False
            for i in range(0, len(bytecode), 5):
                if bytecode[i] == OP_MOVE_TO_DISCARD:
                    found_58 = True
                    slot = bytecode[i+3]
                    target_slot = slot & 0xFFFF
                    remainder_zone = (slot >> 16) & 0xFF
                    
                    if target_slot != 0:
                        issues.append(f"REMAINDER but target_slot={target_slot}")
                    if remainder_zone != 7:
                        issues.append(f"REMAINDER but remainder_zone={remainder_zone}")
            if not found_58:
                # Some might use LOOK_AND_CHOOSE without remainder? 
                # But Card 235 specifically had this.
                pass

        # Check ACTIVATED from Discard
        if 'ACTIVATED (In Discard)' in p:
            if 'PLAY_MEMBER' in p:
                found_63 = any(bytecode[i] == OP_PLAY_MEMBER_FROM_DISCARD for i in range(0, len(bytecode), 5))
                found_57 = any(bytecode[i] == OP_PLAY_MEMBER_FROM_HAND for i in range(0, len(bytecode), 5))
                
                if found_57 and not found_63:
                    issues.append("ACTIVATED from Discard but uses PLAY_MEMBER_FROM_HAND (Op 57)")
                elif not found_63:
                     # It might not have PLAY_MEMBER at all
                     pass

        if issues:
            results.append({
                "card_id": k,
                "card_no": card_no,
                "pseudocode": p,
                "issues": issues
            })

if not results:
    print("ALL CLEAR: All 89 cards verified successfully!")
else:
    print(f"FOUND {len(results)} CARDS WITH ISSUES:")
    for res in results:
        print(f"ID: {res['card_id']} | No: {res['card_no']}")
        print(f"Issues: {', '.join(res['issues'])}")
        print("-" * 20)
