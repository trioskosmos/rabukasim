import json

with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find abilities by card number
target_cards = ['PL!S-bp2-001-P', 'PL!S-pb1-009-P+']

for idx, ability in enumerate(data['abilities']):
    for ref in ability.get('card_refs', []):
        if ref.get('card_no') in target_cards:
            print(f"\n{'='*70}")
            print(f"ABILITY #{idx} - {ref.get('card_no')}")
            print(f"Name: {ref.get('name', 'N/A')}")
            print(f"{'='*70}")
            print(f"\nJapanese Text:")
            print(ability.get('primary_text_jp', 'N/A'))
            print(f"\nTrigger: {ability.get('trigger', 'N/A')}")
            print(f"\nFrames ({len(ability.get('frames', []))} total):")
            for i, frame in enumerate(ability.get('frames', [])):
                print(f"\n  [{i}] {frame.get('op', 'UNKNOWN')}")
                if 'value' in frame:
                    print(f"      value: {frame['value']}")
                if 'attr' in frame:
                    print(f"      attr: {frame['attr']}")
                if 'slot' in frame:
                    print(f"      slot: {frame['slot']}")
            print()
