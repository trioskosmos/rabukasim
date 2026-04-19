import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'card_refs' in ability:
        for ref in ability['card_refs']:
            if '628' in str(ref.get('card_id', '')) and ability.get('trigger') == 'LIVE_START':
                print(f"Found card 628 LIVE_START:")
                print(json.dumps(ability, indent=2, ensure_ascii=False)[:8000])
                break
