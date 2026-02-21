import json

with open("engine/data/cards.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("debug_cards_dump.json", "w", encoding="utf-8") as f:
    json.dump(
        {"pb1-008-R": data.get("PL!-pb1-008-R"), "pb1-011-P＋": data.get("PL!SP-pb1-011-P＋")},
        f,
        ensure_ascii=False,
        indent=2,
    )
