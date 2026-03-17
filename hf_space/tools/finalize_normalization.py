import json


def normalize_pseudocode():
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Final normalization map based on audit report
    repl_map = {
        "メンバー": "MEMBER",
        "エネルギー": "ENERGY",
        "ウェイト": "WAIT",
        "ドロー": "DRAW",
        "ライブカード": "LIVE_CARD",
        "合計25": "25",
        "合計6": "6",
        "合計8": "8",
        "コスト10以上": "10",
        "ブレード追加": "ADD_BLADES",
        "手札2を捨てる": "2",
        "ENERGY2を支払う": "2",
    }

    modified_count = 0
    for card_no, entry in data.items():
        pseudo = entry.get("pseudocode", "")
        old_pseudo = pseudo

        # Apply literal replacements
        for old, new in repl_map.items():
            pseudo = pseudo.replace(old, new)

        if pseudo != old_pseudo:
            entry["pseudocode"] = pseudo
            modified_count += 1

    with open("data/manual_pseudocode.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Final normalization: {modified_count} entries updated.")


if __name__ == "__main__":
    normalize_pseudocode()
