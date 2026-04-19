import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            card_no = ref.get('card_no', '')
            if 'PL!S-bp3-025-L' == card_no:
                print(f"Found PL!S-bp3-025-L:")
                print(json.dumps(ability, indent=2, ensure_ascii=False)[:8000])
                break
