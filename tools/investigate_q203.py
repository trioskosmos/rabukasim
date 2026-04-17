import json

data = json.load(open('data/cards_compiled.json', encoding='utf-8'))
card = data['live_db'].get('358')

if card:
    print('Card:', card['card_no'], '-', card['name'])
    print('Original text:', card['original_text'][:200] + '...')
    print('Abilities:', len(card['abilities']))
    for i, ab in enumerate(card['abilities']):
        print('\nAbility', i)
        print('  Raw text:', ab['raw_text'][:200] + '...')
        if ab.get('frame_program'):
            frames = ab['frame_program']['frames']
            print('  Frames:', len(frames))
            for f in frames[:5]:
                print('    op=', f['op'], ', value=', f.get('value', 'N/A'))
else:
    print('Card 358 not found')
