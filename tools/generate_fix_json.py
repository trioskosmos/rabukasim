import json
import re
import os

def main():
    # Load cards
    with open("data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    # Load audit report
    issues = []
    with open("reports/audit_look_and_choose.txt", "r", encoding="utf-8") as f:
        for line in f:
            if ": Uses" in line:
                card_no = line.split(":")[0].strip().replace("- ", "")
                issues.append(card_no)

    fixes = {}
    
    # Regex for "Look X"
    # JP: デッキの上から(\d+)枚見て
    # Regex for "Choose Y"
    # JP: (\d+)枚まで選び or (\d+)枚選び
    # Regex for "Add to Hand"
    # JP: 手札に加え
    
    for cid in issues:
        if cid not in cards:
            continue
            
        data = cards[cid]
        text = data.get("ability", "")
        
        # Parse Look Count
        look_match = re.search(r"デッキの上から(\d+)枚見て", text)
        look_count = look_match.group(1) if look_match else "3" # Default 3?
        
        # Parse Choose Count
        choose_match = re.search(r"(\d+)枚(まで)?選び", text)
        choose_count = choose_match.group(1) if choose_match else "1"
        
        # Heuristic for "Choose up to" vs "Choose exactly" is handled by choose_count logic usually
        # But opcode supports "choose_count".
        
        # Construct Psuedocode
        # LOOK_AND_CHOOSE_REVEAL(3, TARGET=HAND, destination="discard")
        # Or LOOK_AND_CHOOSE_REVEAL(3) {TARGET=HAND, REMAINDER="DISCARD"}
        # Parser V2 supports params in () or {}?
        # Usage: LOOK_AND_CHOOSE_REVEAL(3, choose_count=1) -> "Look 3, choose 1"
        # Where does it go? TARGET determines it.
        # "Add to Hand" -> TARGET=HAND.
        
        # If text has "手札に加え", Target=HAND.
        target = ""
        if "手札に加え" in text:
            target = "TARGET=HAND"
        
        # Check for specific filters?
        # "すべてのメンバー" -> ALL
        # "《Live》" -> TYPE_LIVE
        # "《Member》" -> TYPE_MEMBER
        
        filter_str = ""
        if "《Live》" in text or "《ライブ》" in text:
             filter_str = ", CARD_TYPE=LIVE"
        elif "《Member》" in text or "《メンバー》" in text:
             filter_str = ", CARD_TYPE=MEMBER"
             
        # Construct entry
        # We use a safe generic template, allowing manual refinement if needed.
        pseudo = f'LOOK_AND_CHOOSE_REVEAL({look_count}, choose_count={choose_count}{filter_str}) {{TARGET=HAND, REMAINDER="DISCARD"}}'
        
        fixes[cid] = {"pseudocode": pseudo}
        print(f"Generated fix for {cid}: {pseudo}")

    # Output to file
    with open("data/generated_fixes.json", "w", encoding="utf-8") as f:
        json.dump(fixes, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
