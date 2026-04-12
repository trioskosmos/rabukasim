import json

# Read cards.json to get correct Japanese text
with open('cards.json', 'r', encoding='utf-8') as f:
    cards_data = json.load(f)

# Read ability_frame_source.json
with open('ability_frame_source.json', 'r', encoding='utf-8') as f:
    abilities_data = json.load(f)

# Create a mapping from card_no to correct Japanese text
card_no_to_text = {}
for card_no, card_info in cards_data.items():
    if 'ability' in card_info:
        card_no_to_text[card_no] = card_info['ability']

# Now fix the mojibake in abilities
fixed_count = 0
not_found_count = 0
for ability in abilities_data['abilities']:
    # Get card_no from source_ability_texts card_examples
    if 'source_ability_texts' in ability and len(ability['source_ability_texts']) > 0:
        source = ability['source_ability_texts'][0]
        if 'card_examples' in source and len(source['card_examples']) > 0:
            # card_examples format: "PL!S-bp2-004-P | 黒澤ダイヤ (ab#0)"
            # Extract card_no (part before " | ")
            card_example = source['card_examples'][0]
            if ' | ' in card_example:
                card_no = card_example.split(' | ')[0]
                if card_no in card_no_to_text:
                    correct_text = card_no_to_text[card_no]
                    # Replace primary_text_jp and source_ability_texts
                    if 'primary_text_jp' in ability:
                        ability['primary_text_jp'] = correct_text
                    if 'source_ability_texts' in ability and len(ability['source_ability_texts']) > 0:
                        ability['source_ability_texts'][0]['jp'] = correct_text
                    fixed_count += 1
                else:
                    print(f"Card no {card_no} not found in card_no_to_text")
                    not_found_count += 1

# Write the fixed file
with open('ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(abilities_data, f, ensure_ascii=False, indent=2)

print(f'Fixed {fixed_count} abilities')
print(f'Not found in cards.json: {not_found_count} abilities')
print(f'No card_examples: {no_card_examples}')
print(f'No pipe separator: {no_pipe}')
