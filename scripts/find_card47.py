import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    content = f.read()
    # Strip BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]
    data = json.loads(content)

# Apply RECOVER_LIVE special_id=4 fix for all PL!HS-bp5-001-* cards
for ability in data['abilities']:
    for card_ref in ability.get('card_refs', []):
        card_no = card_ref.get('card_no', '')
        if 'PL!HS-bp5-001-' in card_no:
            for frame in ability.get('frames', []):
                if frame.get('op') == 'RECOVER_LIVE':
                    if 'attr' in frame and isinstance(frame['attr'], dict):
                        if frame['attr'].get('special_id') == 'Same Name':
                            frame['attr']['special_id'] = 4
                            print(f"Changed RECOVER_LIVE special_id from 'Same Name' to 4 for {card_no}")

with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("File updated")
