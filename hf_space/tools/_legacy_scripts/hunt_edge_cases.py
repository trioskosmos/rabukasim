import json
import re


def hunt():
    with open("c:/Users/trios/.gemini/antigravity/scratch/loveca-copy/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = list(data.values()) if isinstance(data, dict) else data

    patterns = {
        "Negative/Cost Mod": r"[－ー-]\d+",
        "Optional (May)": r"てもよい",
        "Opponent Hand": r"相手の手札",
        "Look at Deck": r"山札.*見て|デッキ.*見て",
        "Colors (Text/Icon)": r"『(赤|青|緑|黄|紫|ピンク|赤色|青色|緑色|黄色|紫色|ピンク色)』|icon_(red|blue|green|yellow|purple|pink)",
        "Once per Turn": r"1ターンに1回|ターン終了時まで.*回のみ|回に限る",
        "Global Effects": r"すべての",
        "Negation": r"でない場合|ではない場合|以外",
    }

    results = {k: [] for k in patterns}

    for card in cards:
        if not isinstance(card, dict):
            continue
        ability = card.get("ability", "")
        if not ability:
            continue

        for name, p in patterns.items():
            if re.search(p, ability):
                results[name].append({"id": card.get("card_no"), "name": card.get("name"), "text": ability})

    print("=== Edge Case Hunt Results ===\n")
    for name, found in results.items():
        print(f"{name}: {len(found)} instances")
        # Print top 2 examples
        for item in found[:2]:
            print(f"  - [{item['id']}] {item['name']}: {item['text'].replace('\n', ' / ')[:100]}...")
        print("")


if __name__ == "__main__":
    hunt()
