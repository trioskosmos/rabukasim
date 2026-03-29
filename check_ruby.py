import json

# Check the actual frame structure in consolidated_abilities.json
with open('data/consolidated_abilities.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find Ruby card entry
for key, val in data.items():
    cards = val.get('card_refs', [])
    for card in cards:
        if card.get('card_id') == 423:
            print('=== Ruby Card 423 Entry ===')
            print('Key:', key[:80])
            print('\nTrigger:', val.get('trigger', 'N/A'))
            print('Pseudocode:', val.get('pseudocode', 'N/A'))
            print('\nRaw Frames (', len(val.get('frames', [])), '):')
            for i, fr in enumerate(val.get('frames', [])):
                print('  Frame', i, ':')
                for k, v in fr.items():
                    print('    ', k, ':', v)
            break
