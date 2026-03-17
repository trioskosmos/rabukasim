import json


def find_life_lead_cards():
    cards_path = "engine/data/cards.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    print("Cards with 'Life > Opponent' or similar:")
    count = 0
    for cid, card in cards.items():
        ability = card.get("ability", "")
        if "ライフが相手より" in ability:
            print(f"{card.get('card_no')}: {ability}")
            count += 1
            if count >= 10:
                break


if __name__ == "__main__":
    find_life_lead_cards()
