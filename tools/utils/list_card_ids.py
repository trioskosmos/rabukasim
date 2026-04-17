import json
import os


def list_card_ids():
    json_path = "data/cards.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_keys = sorted(data.keys())

    m_idx = 0
    l_idx = 1000
    e_idx = 2000

    print(f"{'Int ID':<8} | {'Card No':<20} | {'Type':<10} | {'Name'}")
    print("-" * 80)

    for key in sorted_keys:
        card_data = data[key]
        ctype = card_data.get("type")
        name = card_data.get("name", "Unknown")

        if ctype == "メンバー":
            curr_id = m_idx
            m_idx += 1
        elif ctype == "ライブ":
            curr_id = l_idx
            l_idx += 1
        elif ctype == "エネルギー":
            curr_id = e_idx
            e_idx += 1
        else:
            continue

        print(f"{curr_id:<8} | {key:<20} | {ctype:<10} | {name}")


if __name__ == "__main__":
    list_card_ids()
