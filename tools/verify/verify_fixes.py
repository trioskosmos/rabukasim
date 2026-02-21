import json

def verify():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 265: PL!HS-PR-001-PR
    # 368: PL!HS-bp2-001-R
    # 815: PL!N-bp1-012-R＋
    # 1454: PL!SP-bp4-019-N

    targets = ["265", "368", "815", "1454"]
    results = {}
    
    for eid in targets:
        # Check both dbs
        card_data = data["member_db"].get(eid) or data["live_db"].get(eid)
        if card_data:
            results[eid] = {
                "card_no": card_data.get("card_no"),
                "abilities": card_data.get("abilities", [])
            }

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    verify()
