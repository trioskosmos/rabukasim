import json

path = "data/cards_compiled.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

for db_name in ["member_db", "live_db"]:
    db = data.get(db_name, {})
    for cid, card in db.items():
        for i, ab in enumerate(card.get("abilities", [])):
            if "bytecode" in ab:
                for j, val in enumerate(ab["bytecode"]):
                    if not isinstance(val, int):
                        print(
                            f"BAD BYTECODE at {db_name}.{cid} ({card.get('card_no')}): Ability {i}, Index {j}, Value={repr(val)}, Type={type(val)}"
                        )
            # Also check for other fields if needed
