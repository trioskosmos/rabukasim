import json
import os


def generate_old_mapping():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_keys = sorted(data.keys())
    mapping = {}

    m_idx = 0
    l_idx = 30000  # Original compiler logic
    e_idx = 40000

    for key in sorted_keys:
        item = data[key]
        ctype = item.get("type", "")

        # Mimic old variants logic
        variants = [{"card_no": key}]
        if "rare_list" in item and isinstance(item["rare_list"], list):
            for r in item["rare_list"]:
                v_no = r.get("card_no")
                if v_no and v_no != key:
                    variants.append({"card_no": v_no})

        for v in variants:
            v_no = v["card_no"]
            if "メンバー" in ctype or "Member" in ctype:
                mapping[v_no] = m_idx
                m_idx += 1
            elif "ライブ" in ctype or "Live" in ctype:
                mapping[v_no] = l_idx
                l_idx += 1
            else:
                mapping[v_no] = e_idx
                e_idx += 1

    os.makedirs("reports", exist_ok=True)
    with open("reports/old_id_map.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(mapping)} mappings to reports/old_id_map.json")


if __name__ == "__main__":
    generate_old_mapping()
