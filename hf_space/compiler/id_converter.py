import json
import os
import sys


def load_db():
    compiled_path = "engine/data/cards_compiled.json"
    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found.")
        return None
    try:
        with open(compiled_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        print(f"Load Error: {e}")
        return None


def convert(query):
    full_db = load_db()
    if not full_db:
        return

    # Handle member_db and live_db
    member_db = full_db.get("member_db", {})
    live_db = full_db.get("live_db", {})
    dbs = [member_db, live_db]

    print(f"Total cards loaded: Members {len(member_db)}, Lives {len(live_db)}")

    # Try numeric ID
    if query.isdigit():
        for db in dbs:
            if query in db:
                card = db[query]
                print(f"ID {query} -> {card.get('card_no')} ({card.get('name')})")
                abis = card.get("abilities", [])
                print(f"Parsed {len(abis)} abilities.")
                for i, a in enumerate(abis):
                    print(f"  [{i}] Trig:{a.get('trigger')} | {a.get('raw_text')}")
                return

    # Try Card No or Search
    matches = []
    for db in dbs:
        for cid, card in db.items():
            card_no = str(card.get("card_no", ""))
            name = str(card.get("name", ""))

            if card_no.lower() == query.lower():
                print(f"Card No {card_no} -> ID {cid} ({name})")
                abis = card.get("abilities", [])
                print(f"Parsed {len(abis)} abilities.")
                for i, a in enumerate(abis):
                    print(f"  [{i}] Trig:{a.get('trigger')} | {a.get('raw_text')}")
                return

            if query.lower() in card_no.lower() or query in name:
                matches.append((cid, card_no, name))

    if matches:
        print(f"Found {len(matches)} matches:")
        for m in matches[:15]:
            print(f"  ID {m[0]} | {m[1]} | {m[2]}")
        if len(matches) > 15:
            print("  ...")
    else:
        print(f"No matches found for '{query}'.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python compiler/id_converter.py <ID or CardNo>")
    else:
        convert(sys.argv[1])
