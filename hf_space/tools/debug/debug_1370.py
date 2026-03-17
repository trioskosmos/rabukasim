import json
import os

from engine.game.data_loader import CardDataLoader


def check_card_1370():
    path = "data/cards_compiled.json"
    print(f"Checking {path}...")
    if not os.path.exists(path):
        print("File not found!")
        return

    loader = CardDataLoader(path)
    try:
        m, l, e = loader.load()
        print(f"Loaded {len(m)} members.")
        if 1370 in m:
            print("Card 1370 SUCCESFULLY LOADED into member dict.")
            card = m[1370]
            print(f"Card No: {card.card_no}")
            print(f"Abilities: {len(card.abilities)}")
        else:
            print("Card 1370 NOT FOUND in member dict.")
            keys = sorted(list(m.keys()))
            print(f"Max ID: {keys[-1]}")
            # Find if it's there as string?
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "1370" in data.get("member_db", {}):
                    print("Found '1370' as string key in raw JSON.")
                else:
                    print("'1370' NOT in raw JSON member_db.")
    except Exception as ex:
        print(f"Error during loading: {ex}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    check_card_1370()
