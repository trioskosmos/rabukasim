import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'trigger' in ability:
        trigger = ability.get('trigger', '')
        text = ability.get('primary_text_jp', '')
        if trigger == 'LIVE_START' and 'Aqours' in text:
            print(f"Found LIVE_START with Aqours:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
            break
