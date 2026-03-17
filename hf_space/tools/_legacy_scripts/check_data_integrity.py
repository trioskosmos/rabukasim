import json


def check_integrity():
    with open("engine/data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    anomalies = []
    for card_no, card in data.items():
        ability = card.get("ability", "")
        if "\r" in ability:
            anomalies.append((card_no, "Has CR (\\r)", ability))
        if "\0" in ability:
            anomalies.append((card_no, "Has Null byte", ability))
        # Check for weird spaces or control chars
        for i, char in enumerate(ability):
            if ord(char) < 32 and char not in "\n\r\t":
                anomalies.append((card_no, f"Has Ctrl char {ord(char)} at pos {i}", ability))
                break

    print(f"Total cards: {len(data)}")
    print(f"Anomalies found: {len(anomalies)}")

    for card_no, msg, text in anomalies[:20]:
        print(f"--- {card_no} ---")
        print(f"Issue: {msg}")
        print(f"Repr: {repr(text)}")
        print()


if __name__ == "__main__":
    check_integrity()
