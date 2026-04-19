import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            card_no = ref.get('card_no', '')
            if 'bp2-006' in card_no and ability.get('trigger') == 'LIVE_START':
                print(f"Found bp2-006 LIVE_START:")
                print(json.dumps(ability, indent=2, ensure_ascii=False)[:8000])
                break
