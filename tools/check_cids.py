import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

member_db = data.get("member_db", {})

# Archetype 03: OnPlay -> Discard 1 from hand (optional) -> Look at top 3 of deck, choose 1
# Archetype 13: OnLiveStart -> Pay Energy -> Color Select -> Add Heart
# Let's find cards with these patterns

print("=== Looking for Archetype 03 pattern: OnPlay + Optional + Discard + Look/Choose ===")
for cid, card in member_db.items():
    for ab in card.get("abilities", []):
        bc = ab.get("bytecode", [])
        trigger = ab.get("trigger", 0)
        # OnPlay = trigger 1, Look for SELECT_MODE (58), MOVE_TO_DISCARD (81), LOOK_AND_CHOOSE (77)
        if trigger == 1 and 58 in bc and 81 in bc:
            print(f"  CID={cid} card_id={card.get('card_id',0)} card_no={card.get('card_no','?')} trigger={trigger} bc={bc[:24]}")

print()
print("=== Looking for Archetype 13 pattern: OnLiveStart + Pay Energy + Color Select + Add Heart ===")
for cid, card in member_db.items():
    for ab in card.get("abilities", []):
        bc = ab.get("bytecode", [])
        trigger = ab.get("trigger", 0)
        # OnLiveStart = trigger 2, O_PAY_ENERGY=64, O_COLOR_SELECT=45, O_ADD_HEARTS=12
        if trigger == 2 and 64 in bc and 45 in bc and 12 in bc:
            print(f"  CID={cid} card_id={card.get('card_id',0)} card_no={card.get('card_no','?')} trigger={trigger} bc={bc}")

print()
print("=== Also dump specific test CIDs: 130, 3130, 4332 ===")
for target_cid in ["130", "3130", "4332"]:
    if target_cid in member_db:
        card = member_db[target_cid]
        print(f"  CID={target_cid} card_id={card.get('card_id',0)} card_no={card.get('card_no','?')}")
        for i, ab in enumerate(card.get("abilities", [])):
            print(f"    Ab[{i}] trigger={ab.get('trigger',0)} bc={ab.get('bytecode',[][:24])}")
    else:
        print(f"  CID={target_cid} NOT FOUND in member_db")
