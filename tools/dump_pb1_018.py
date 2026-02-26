import json

def get_pb1_018():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    for c in cards.values():
        num = c.get('card_number', '')
        if 'pb1-018' in num:
            print(f"ID {c.get('card_id', c.get('id', 'N/A'))} - {num}: {c.get('ability_text_jp', '')}")
            print(json.dumps(c.get('abilities', c.get('ability', [])), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    get_pb1_018()
