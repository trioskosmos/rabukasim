import json


def main():
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    abilities = []
    for card_no, data in cards.items():
        text = data.get("ability", "")
        if text:
            abilities.append((card_no, data.get("name", ""), text, len(text)))

    abilities.sort(key=lambda x: x[3], reverse=True)

    print("Top 10 Longest Abilities:")
    for i in range(min(10, len(abilities))):
        c_no, name, text, length = abilities[i]
        print(f"{i + 1}. {c_no} ({name}) - {length} chars")
        print(f"   Text: {text}")
        print("-" * 20)


if __name__ == "__main__":
    main()
