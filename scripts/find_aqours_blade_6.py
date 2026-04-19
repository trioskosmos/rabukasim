import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'primary_text_jp' in ability:
        text = ability.get('primary_text_jp', '')
        if 'Aqours' in text and ('ブレード' in text or 'blade' in text.lower()) and ('6' in text or '六' in text):
            print(f"Found Aqours + blade + 6:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
            break
