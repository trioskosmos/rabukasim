#!/usr/bin/env python3
"""
Dump full comparison data: original ability text, semantics, and frames with all variables.
This script outputs the actual data from the JSON files without manual writing.
"""
import json
from pathlib import Path

# Load data
cards_file = Path("data/cards.json")
authored_frames_file = Path("data/ability_frame_source_authored.json")
converted_frames_file = Path("data/ability_frame_source.json")
extracted_abilities_file = Path("data/abilities_extracted_from_cards.json")

with open(cards_file, encoding='utf-8') as f:
    cards = json.load(f)

with open(authored_frames_file, encoding='utf-8') as f:
    authored_frames = json.load(f)

with open(converted_frames_file, encoding='utf-8') as f:
    converted_frames = json.load(f)

with open(extracted_abilities_file, encoding='utf-8') as f:
    extracted_abilities = json.load(f)

# Create lookup by card
authored_by_card = {}
for ability in authored_frames['abilities']:
    for ref in ability.get('card_refs', []):
        card_no = ref.get('card_no')
        if card_no:
            if card_no not in authored_by_card:
                authored_by_card[card_no] = []
            authored_by_card[card_no].append({
                'ability': ability,
                'ability_index': ref.get('ability_index', 0),
                'trigger': ref.get('trigger')
            })

converted_by_card = {}
for ability in converted_frames['abilities']:
    for ref in ability.get('card_refs', []):
        card_no = ref.get('card_no')
        if card_no:
            if card_no not in converted_by_card:
                converted_by_card[card_no] = []
            converted_by_card[card_no].append({
                'ability': ability,
                'ability_index': ref.get('ability_index', 0),
                'trigger': ref.get('trigger')
            })

extracted_by_card = {}
for ability in extracted_abilities['unique_abilities']:
    for card_ref in ability.get('cards', []):
        if ' | ' in card_ref:
            card_no = card_ref.split(' | ')[0]
            if card_no not in extracted_by_card:
                extracted_by_card[card_no] = []
            extracted_by_card[card_no].append(ability)

# Test patterns
test_patterns = [
    {
        'name': 'names_different',
        'pattern': '名前が異なる場合',
    },
    {
        'name': 'opponent_member_to_wait',
        'pattern': '相手のステージにいるコスト4以下のメンバー1人をウェイトにする',
    },
    {
        'name': 'waitroom_live_recovery',
        'pattern': '自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える',
    },
]

output_file = Path("tools/ability_extraction/full_comparison_dump.json")
dump_data = {}

for test in test_patterns:
    pattern = test['pattern']
    dump_data[test['name']] = {
        'pattern': pattern,
        'cards': []
    }
    
    # Find matching cards
    matching_cards = []
    for card_no, card in cards.items():
        ability = card.get('ability', '')
        if pattern in ability:
            matching_cards.append(card_no)
    
    # Process first 3 matching cards
    for card_no in matching_cards[:3]:
        card = cards[card_no]
        card_data = {
            'card_no': card_no,
            'name': card.get('name', ''),
            'ability_text': card.get('ability', ''),
            'authored_abilities': [],
            'converted_abilities': [],
            'extracted_abilities': []
        }
        
        # Get authored frames
        authored = authored_by_card.get(card_no, [])
        for auth_item in authored:
            card_data['authored_abilities'].append({
                'ability_index': auth_item['ability_index'],
                'trigger': auth_item['trigger'],
                'full_ability': auth_item['ability']
            })
        
        # Get converted frames
        converted = converted_by_card.get(card_no, [])
        for conv_item in converted:
            card_data['converted_abilities'].append({
                'ability_index': conv_item['ability_index'],
                'trigger': conv_item['trigger'],
                'full_ability': conv_item['ability']
            })
        
        # Get extracted semantics
        extracted = extracted_by_card.get(card_no, [])
        for ext_item in extracted:
            card_data['extracted_abilities'].append(ext_item)
        
        dump_data[test['name']]['cards'].append(card_data)

# Write to JSON
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(dump_data, f, ensure_ascii=False, indent=2)

print(f"Full comparison dump written to {output_file}")
print(f"Total patterns: {len(test_patterns)}")

# Also create a readable markdown version
md_file = Path("tools/ability_extraction/full_comparison_dump.md")
with open(md_file, 'w', encoding='utf-8') as f:
    f.write("# Full Comparison Dump\n\n")
    f.write("This document contains the actual data from the JSON files for cards matching test patterns.\n\n")
    
    for test in test_patterns:
        f.write(f"## Pattern: {test['name']}\n\n")
        f.write(f"**Pattern:** {test['pattern']}\n\n")
        
        pattern_data = dump_data[test['name']]
        f.write(f"**Cards found:** {len(pattern_data['cards'])}\n\n")
        
        for card_data in pattern_data['cards']:
            f.write(f"### Card: {card_data['card_no']} | {card_data['name']}\n\n")
            f.write(f"**Ability Text:**\n```\n{card_data['ability_text']}\n```\n\n")
            
            # Authored abilities
            f.write(f"**Authored Abilities ({len(card_data['authored_abilities'])}):**\n\n")
            for i, auth in enumerate(card_data['authored_abilities']):
                f.write(f"#### Authored Ability {i}\n\n")
                f.write(f"- **Trigger:** {auth['trigger']}\n")
                f.write(f"- **Ability Index:** {auth['ability_index']}\n")
                f.write(f"- **Full Ability Data:**\n```json\n{json.dumps(auth['full_ability'], ensure_ascii=False, indent=2)}\n```\n\n")
            
            # Converted abilities
            f.write(f"**Converted Abilities ({len(card_data['converted_abilities'])}):**\n\n")
            for i, conv in enumerate(card_data['converted_abilities']):
                f.write(f"#### Converted Ability {i}\n\n")
                f.write(f"- **Trigger:** {conv['trigger']}\n")
                f.write(f"- **Ability Index:** {conv['ability_index']}\n")
                f.write(f"- **Full Ability Data:**\n```json\n{json.dumps(conv['full_ability'], ensure_ascii=False, indent=2)}\n```\n\n")
            
            # Extracted semantics
            f.write(f"**Extracted Semantic Abilities ({len(card_data['extracted_abilities'])}):**\n\n")
            for i, ext in enumerate(card_data['extracted_abilities']):
                f.write(f"#### Extracted Ability {i}\n\n")
                f.write(f"- **Full Text:** {ext.get('full_text', '')}\n")
                f.write(f"- **Triggerless Text:** {ext.get('triggerless_text', '')}\n")
                f.write(f"- **Triggers:** {ext.get('triggers', 'N/A')}\n")
                f.write(f"- **Use Limit:** {ext.get('use_limit', 'N/A')}\n")
                f.write(f"- **Card Count:** {ext.get('card_count', 0)}\n")
                f.write(f"- **Cost:**\n```json\n{json.dumps(ext.get('cost'), ensure_ascii=False, indent=2)}\n```\n")
                f.write(f"- **Effect:**\n```json\n{json.dumps(ext.get('effect'), ensure_ascii=False, indent=2)}\n```\n\n")
            
            f.write("---\n\n")

print(f"Readable markdown version written to {md_file}")
