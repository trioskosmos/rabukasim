import json
import sys

def dump_cards():
    names = [
        "夢が僕らの太陽さ",
        "Love U my friends",
        "MY舞☆TONIGHT",
        "Poppin' Up!",
        "Eutopia"
    ]
    
    try:
        with open('data/cards.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    found = {}
    
    # cards.json structure is { "CARD_NO": { ... } }
    for key, card in data.items():
        if card.get('name') in names:
            # We want to find the one that matches the IDs in report if possible,
            # but we don't have the mapping from Card ID (int) to ID (string) here easily without compiling.
            # But the report uses integer IDs.
            # Let's just dump all matches by name.
            name = card.get('name')
            if name not in found:
                found[name] = []
            found[name].append(card)

    print(json.dumps(found, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    dump_cards()
