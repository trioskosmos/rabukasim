import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
abilities = data.get('abilities', [])
for i, ab in enumerate(abilities):
    cards = ab.get('card_refs', [])
    for card in cards:
        card_no = card.get('card_no', '')
        if card_no.startswith('PL!S-pb1-009'):
            print(f'Ability #{i}: {card_no}')
            print(f"Text: {ab.get('primary_text_jp', '')[:100]}")
            frames = ab.get('frames', [])
            print(f'Frames: {[f["op"] for f in frames]}')
            print()
