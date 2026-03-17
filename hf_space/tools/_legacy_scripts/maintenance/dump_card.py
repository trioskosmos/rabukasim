import json

try:
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Root keys: {list(data.keys())[:5]}")

    found = []

    # Check if compiled structure
    if "member_db" in data:
        print("Detected compiled structure (member_db). Searching inside...")
        source = data["member_db"]
    else:
        print("Assuming flat structure. Searching root...")
        source = data

    for k, v in source.items():
        # Handle if v is not dict (e.g. metadata)
        if isinstance(v, dict) and v.get("card_no") == "LL-bp3-001-R＋":
            found.append(v)

    with open("card_dump.json", "w", encoding="utf-8") as f:
        json.dump(found, f, indent=2, ensure_ascii=False)

    print(f"Dumped {len(found)} cards to card_dump.json")

except Exception as e:
    print(f"Error: {e}")
