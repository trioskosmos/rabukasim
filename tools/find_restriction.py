import json

def find_cards_with_restriction():
    with open('data/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    for c in cards:
        text = c.get('ability_text_jp', '')
        if '登場できない' in text or '置くことはできない' in text:
            print(f"{c['card_number']}: {c.get('name')} - Cost: {c.get('cost')}")
            print(f"Text: {text}\n")

if __name__ == '__main__':
    find_cards_with_restriction()
