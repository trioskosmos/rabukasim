import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'trigger' in ability:
        trigger = ability.get('trigger', '')
        text = ability.get('primary_text_jp', '')
        if trigger == 'LIVE_START' and ('デッキの一番上' in text or 'topdeck' in text.lower()):
            print(f"Found LIVE_START with deck top:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:8000])
            break
