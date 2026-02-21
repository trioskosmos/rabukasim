import json
import re


def check_general_application():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = list(data.values()) if isinstance(data, dict) else data

    patterns = {
        "TRANSFORM_COLOR": {"regex": r"すべて\[(.*?)\]になる", "matches": []},
        "DISTINCT_NAMES": {"regex": r"名前の異なる", "matches": []},
        "NAMED_MEMBER_TARGET": {"regex": r"「(.*?)」.*?は", "matches": []},
    }

    for card in cards:
        text = card.get("ability", "")
        if not text:
            continue

        for name, info in patterns.items():
            if re.search(info["regex"], text):
                info["matches"].append(f"[{card.get('cardNumber')}] {card.get('name')}: {text[:100]}...")

    with open("generality_report.txt", "w", encoding="utf-8") as out:
        out.write("=" * 60 + "\n")
        out.write("GENERALITY CHECK REPORT\n")
        out.write("=" * 60 + "\n")

        for name, info in patterns.items():
            out.write(f"\n{name}: Found {len(info['matches'])} cards\n")
            for m in info["matches"][:5]:
                out.write(f"  - {m}\n")
            if len(info["matches"]) > 5:
                out.write(f"  ... and {len(info['matches']) - 5} more\n")

    print("Report written to generality_report.txt")


if __name__ == "__main__":
    check_general_application()
