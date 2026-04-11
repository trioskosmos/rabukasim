import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
abilities = data.get('abilities', [])
for i, ab in enumerate(abilities):
    cards = ab.get('card_refs', [])
    for card in cards:
        card_no = card.get('card_no', '')
        if card_no == 'LL-PR-004-PR':
            print(f'Ability #{i}: {card_no}')
            text = ab.get('primary_text_jp', '')
            print(f'Text: {text[:150]}')
            frames = ab.get('frames', [])
            print(f'Frames:')
            for f in frames:
                print(f'  {f["op"]}: {f.get("value", "")}')
            print()
