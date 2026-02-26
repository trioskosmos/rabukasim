import json
import sys

def find_cards():
    with open('data/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)

    targets = ['pb1-023', 'bp2-024', 'bp3-005']
    for card in cards:
        num = card.get('card_number', '')
        for t in targets:
            if t in num:
                print(f"{num}: ID {card.get('id', 'N/A')}")

if __name__ == '__main__':
    find_cards()
