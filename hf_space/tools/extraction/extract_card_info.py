import json

target_ids = ["PL!-sd1-001-SD", "PL!HS-PR-007-PR", "PL!S-PR-004-PR", "PL!S-PR-003-PR", "PL!S-PR-008-PR"]

try:
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with open("card_info_utf8.txt", "w", encoding="utf-8") as outfile:
        found = 0
        for cid in target_ids:
            if cid in data:
                card = data[cid]
                outfile.write(f"--- {cid} ({card.get('name', 'Unknown')}) ---\n")
                outfile.write(f"Ability: {card.get('ability', 'None')}\n")
                outfile.write(f"FAQ: {json.dumps(card.get('faq', []), ensure_ascii=False)}\n")
                found += 1
            else:
                outfile.write(f"--- {cid} NOT FOUND ---\n")
        outfile.write(f"\nFound {found}/{len(target_ids)} cards.\n")

except Exception as e:
    print(f"Error: {e}")
