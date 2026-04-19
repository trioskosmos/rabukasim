import json

# Load authored frames
with open('data/ability_frame_source_authored.json', encoding='utf-8') as f:
    authored = json.load(f)

# Find card 459 by searching for Aqours and blade references
for ability in authored:
    if isinstance(ability, dict) and 'text' in ability:
        text = ability.get('text', '')
        if 'Aqours' in text and ('blade' in text.lower() or 'ブレード' in text):
            print("Found ability with Aqours and blade:")
            print(json.dumps(ability, indent=2, ensure_ascii=False)[:5000])
            break
