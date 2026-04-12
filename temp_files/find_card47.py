import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    content = f.read()
    # Strip BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]
    data = json.loads(content)

# Fix PL!N-bp5-003-R PAY_ENERGY_DYNAMIC - remove is_optional flag
for ability in data['abilities']:
    for card_ref in ability.get('card_refs', []):
        if 'PL!N-bp5-003-R' in card_ref.get('card_no', ''):
            for frame in ability.get('frames', []):
                if frame.get('op') == 'PAY_ENERGY_DYNAMIC':
                    if 'attr' in frame and isinstance(frame['attr'], dict):
                        if 'is_optional' in frame['attr']:
                            del frame['attr']['is_optional']
                            if not frame['attr']:
                                del frame['attr']
                    print(f"Fixed PAY_ENERGY_DYNAMIC for {card_ref['card_no']}")

with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("File updated")
