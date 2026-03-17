"""Extract sample META_RULE abilities for analysis."""

import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    db = json.load(f)

print("=== META_RULE SAMPLES ===")
count = 0
for card_id, card in db["member_db"].items():
    for i, ab in enumerate(card.get("abilities", [])):
        bc = ab.get("bytecode", [])
        if 29 in bc:
            print(f"\n[{card['card_no']}] Ability {i}:")
            print(f"  Text: {ab.get('text', 'N/A')[:80]}...")
            print(f"  Bytecode: {bc[:20]}...")
            # Find the META_RULE params
            for j in range(0, len(bc), 4):
                if bc[j] == 29:
                    print(
                        f"  META_RULE at offset {j}: op=29, val={bc[j + 1] if j + 1 < len(bc) else '?'}, attr={bc[j + 2] if j + 2 < len(bc) else '?'}, target={bc[j + 3] if j + 3 < len(bc) else '?'}"
                    )
            count += 1
            if count >= 15:
                break
    if count >= 15:
        break

print("\n=== MISSING TRIGGER SAMPLES ===")
count = 0
for card_id, card in db["member_db"].items():
    for i, ab in enumerate(card.get("abilities", [])):
        trigger = ab.get("trigger")
        if trigger is None or trigger == 0:
            print(f"\n[{card['card_no']}] Ability {i}:")
            print(f"  Trigger: {trigger}")
            print(f"  Text: {ab.get('text', 'N/A')[:80]}...")
            print(f"  Bytecode: {ab.get('bytecode', [])[:12]}...")
            count += 1
            if count >= 10:
                break
    if count >= 10:
        break
