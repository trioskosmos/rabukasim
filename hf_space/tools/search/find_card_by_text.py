import json


def find_card():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    target_text_1 = "このメンバーをステージから控え室に置く"
    target_text_2 = "ライブカードを1枚手札に加える"

    found = []

    for k, v in db.items():
        ability = v.get("ability", "")
        if target_text_1 in ability and target_text_2 in ability:
            print(f"MATCH: ID={k}, Name={v['name']}")
            print(f"  Ability: {ability[:100]}...")
            found.append(k)

    if not found:
        print("No matches found.")


if __name__ == "__main__":
    find_card()
