import json

# Read cards.json
with open('cards.json', 'r', encoding='utf-8') as f:
    cards_data = json.load(f)

# Read ability_frame_source.json
with open('ability_frame_source.json', 'r', encoding='utf-8') as f:
    abilities_data = json.load(f)

# Get first ability
first_ability = abilities_data['abilities'][0]
card_example = first_ability['source_ability_texts'][0]['card_examples'][0]
card_no = card_example.split(' | ')[0]

# Write to file instead of printing
with open('debug_output.txt', 'w', encoding='utf-8') as f:
    f.write(f'Card example: {card_example}\n')
    f.write(f'Extracted card_no: {card_no}\n')
    f.write(f'Exists in cards.json: {card_no in cards_data}\n')
    
    # Show similar keys
    similar_keys = [k for k in list(cards_data.keys())[:50] if 'PL!S' in k or 'bp2' in k]
    f.write(f'Similar keys: {similar_keys}\n')
    
    # Show first 20 card_no keys from cards.json
    f.write(f'First 20 card_no keys from cards.json: {list(cards_data.keys())[:20]}\n')

print('Debug output written to debug_output.txt')
