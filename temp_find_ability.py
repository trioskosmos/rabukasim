import json

with open('C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

abilities = data.get('abilities', [])

for i, ab in enumerate(abilities):
    cards = ab.get('card_refs', [])
    for card in cards:
        if card.get('card_id') == 462 and card.get('ability_index') == 1:
            print(f'Found ability #{i} for card 462, ability_index=1')
            print(f"Text: {ab.get('primary_text_jp', '')}")
            print(f"Trigger: {ab.get('trigger')}")
            print(f"Frames:")
            for j, frame in enumerate(ab.get('frames', [])):
                print(f"  {j}: {frame}")
            print()
            # Print approximate byte offset
            print(f"Looking for this entry in file...")
            break
