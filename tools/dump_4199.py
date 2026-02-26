import json

def get_4199():
    with open('data/cards_compiled.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    for c in cards:
        if str(c.get('card_id', c.get('id', 'N/A'))) == '4199':
            print(f"ID {c.get('card_id', c.get('id', 'N/A'))} - {c.get('card_number')}: {c.get('ability_text_jp', '')}")
            print(json.dumps(c.get('abilities', c.get('ability', [])), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    get_4199()
