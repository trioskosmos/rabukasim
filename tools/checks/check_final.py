# -*- coding: utf-8 -*-
import json
from pathlib import Path


def main():
    data_path = Path("data/cards_compiled.json")
    data = json.loads(data_path.read_text(encoding="utf-8"))

    ids = ["544", "226", "312", "665", "84", "537", "642"]
    for cid in ids:
        m = data["member_db"].get(cid)
        if not m:
            continue
        print(f"=== {cid}: {m.get('card_no')} ===")
        for i, a in enumerate(m.get("abilities", [])):
            print(f"Ability {i}: {a.get('raw_text')}")
            print(f"  Effects: {a.get('effects')}")
            print(f"  Costs: {a.get('costs')}")
            print("-" * 20)


if __name__ == "__main__":
    main()
