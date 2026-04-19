import json

data = json.load(open('data/ability_frame_source_authored.json', encoding='utf-8'))
abilities = data.get('abilities', [])

for ability in abilities:
    if isinstance(ability, dict) and 'primary_text_jp' in ability:
        text = ability.get('primary_text_jp', '')
        if 'デッキの一番上' in text or 'topdeck' in text.lower():
            print(f"Found ability with deck top reference:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:8000])
            break
