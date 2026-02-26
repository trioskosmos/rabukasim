import json

def main():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)

    print('Looking for cost <= 2 with ON_PLAY...')
    for cid, c in cards.items():
        if c.get('cost', 99) <= 2:
            for ab in c.get('abilities', []):
                if ab.get('trigger') == 1:
                    print(f"ID: {cid}, Name: {c['name']}, No: {c['card_no']}")
                    break

if __name__ == '__main__':
    main()
