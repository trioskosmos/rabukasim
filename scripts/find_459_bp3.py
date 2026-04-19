import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            card_no = ref.get('card_no', '')
            if 'bp3-025' in card_no:
                print(f"Found bp3-025 (card 459):")
                print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
                break
