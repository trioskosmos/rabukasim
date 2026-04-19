#!/usr/bin/env python3
"""
Compare authored semantic output vs converted parser output for test patterns.
This script finds cards matching the test patterns in test_parsers.py and compares
the authored frames with the extracted semantic output.
"""
import json
import sys
from pathlib import Path

# Load data
cards_file = Path("data/cards.json")
authored_frames_file = Path("data/ability_frame_source_authored.json")
extracted_abilities_file = Path("data/abilities_extracted_from_cards.json")

with open(cards_file, encoding='utf-8') as f:
    cards = json.load(f)

with open(authored_frames_file, encoding='utf-8') as f:
    authored_frames = json.load(f)

with open(extracted_abilities_file, encoding='utf-8') as f:
    extracted_abilities = json.load(f)

# Test patterns from test_parsers.py
test_patterns = [
    {
        'name': 'multi_branch_cost_total',
        'pattern': 'コストの合計が、6の場合',
        'description': 'Multi-branch cost total conditions'
    },
    {
        'name': 'count_based_conditions',
        'pattern': 'ブレードハートを持たないメンバーカードが1枚以上ある場合',
        'description': 'Count-based conditions (1枚 vs 2枚)'
    },
    {
        'name': 'is_not_conditions',
        'pattern': "μ'sのカードの場合",
        'description': 'Is/is-not conditions (μ\'s vs not μ\'s)'
    },
    {
        'name': 'surplus_heart',
        'pattern': '余剰ハートを持たない場合',
        'description': 'Surplus heart conditions (none vs 2+)'
    },
    {
        'name': 'nested_conditional',
        'pattern': 'コスト10以上のブレードハートを持たない『虹ヶ咲』のメンバー',
        'description': 'Nested conditional chain'
    },
    {
        'name': 'opponent_member_to_wait',
        'pattern': '相手のステージにいるコスト4以下のメンバー1人をウェイトにする',
        'description': 'Opponent member to wait'
    },
    {
        'name': 'waitroom_live_recovery',
        'pattern': '自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える',
        'description': 'Waitroom live recovery'
    },
    {
        'name': 'choice_pattern',
        'pattern': '以下から1つを選ぶ',
        'description': 'Choice patterns'
    },
    {
        'name': 'both_players',
        'pattern': '自分と相手はそれぞれ',
        'description': 'Both-players abilities'
    },
    {
        'name': 'exclusion_pattern',
        'pattern': 'このメンバー以外のメンバー',
        'description': 'Exclusion pattern (以外)'
    },
    {
        'name': 'card_negation',
        'pattern': 'ブレードハートを持たないメンバーカード',
        'description': 'Card negation (持たない)'
    },
    {
        'name': 'names_different',
        'pattern': '名前が異なる場合',
        'description': 'Names different condition'
    },
]

print("=" * 80)
print("COMPARISON: Authored Semantic vs Converted Parser Output")
print("=" * 80)
print()

# Create a lookup for authored frames by card
authored_by_card = {}
for ability in authored_frames['abilities']:
    for ref in ability.get('card_refs', []):
        card_no = ref.get('card_no')
        if card_no:
            if card_no not in authored_by_card:
                authored_by_card[card_no] = []
            authored_by_card[card_no].append({
                'ability': ability,
                'ability_index': ref.get('ability_index', 0)
            })

# Create a lookup for extracted abilities by card
extracted_by_card = {}
for ability in extracted_abilities['unique_abilities']:
    for card_ref in ability.get('cards', []):
        # Parse card reference format: "CARD_NO | NAME (ab#N)"
        if ' | ' in card_ref:
            card_no = card_ref.split(' | ')[0]
            if card_no not in extracted_by_card:
                extracted_by_card[card_no] = []
            extracted_by_card[card_no].append(ability)

# For each test pattern, find matching cards and compare
for test in test_patterns:
    pattern = test['pattern']
    print(f"\n{'=' * 80}")
    print(f"Test Pattern: {test['name']} - {test['description']}")
    print(f"Pattern: {pattern}")
    print(f"{'=' * 80}")
    
    # Find cards matching this pattern
    matching_cards = []
    for card_no, card in cards.items():
        ability = card.get('ability', '')
        if pattern in ability:
            matching_cards.append(card_no)
    
    if not matching_cards:
        print("No matching cards found in cards.json")
        continue
    
    print(f"Found {len(matching_cards)} matching cards")
    
    # Analyze first 3 matching cards
    for card_no in matching_cards[:3]:
        card = cards[card_no]
        print(f"\n--- Card: {card_no} | {card.get('name', 'Unknown')} ---")
        print(f"Ability: {card.get('ability', '')[:200]}...")
        
        # Get authored frames for this card
        authored = authored_by_card.get(card_no, [])
        # Get extracted abilities for this card
        extracted = extracted_by_card.get(card_no, [])
        
        print(f"\nAuthored frames: {len(authored)} abilities")
        print(f"Extracted abilities: {len(extracted)} abilities")
        
        if authored:
            print(f"\nAuthored frame structure (first ability):")
            first_authored = authored[0]['ability']
            print(f"  Primary text: {first_authored.get('primary_text_jp', '')[:100]}...")
            print(f"  Trigger: {first_authored.get('trigger', 'N/A')}")
            print(f"  Frames count: {len(first_authored.get('frames', []))}")
            if first_authored.get('frames'):
                print(f"  First frame op: {first_authored['frames'][0].get('op', 'N/A')}")
        
        if extracted:
            print(f"\nExtracted ability structure (first ability):")
            first_extracted = extracted[0]
            print(f"  Full text: {first_extracted.get('full_text', '')[:100]}...")
            print(f"  Triggers: {first_extracted.get('triggers', 'N/A')}")
            print(f"  Has cost: {first_extracted.get('cost') is not None}")
            print(f"  Has effect: {first_extracted.get('effect') is not None}")
            if first_extracted.get('effect'):
                effect = first_extracted['effect']
                if isinstance(effect, dict):
                    print(f"  Effect action: {effect.get('action', 'N/A')}")
                    print(f"  Effect keys: {list(effect.keys())[:5]}")
        
        # Comparison
        print(f"\nComparison:")
        if authored and extracted:
            print(f"  ✓ Both authored and extracted data available")
            print(f"  → Authored has {len(authored)} frame-based abilities")
            print(f"  → Extracted has {len(extracted)} semantic abilities")
            print(f"  → Note: Direct comparison requires semantic-to-frame conversion")
        elif authored:
            print(f"  ⚠ Only authored frames available (no extraction)")
        elif extracted:
            print(f"  ⚠ Only extracted semantic available (no authored frames)")
        else:
            print(f"  ✗ Neither authored nor extracted data available")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("The test patterns in test_parsers.py are synthetic test cases designed to")
print("validate parser logic for specific Japanese ability text patterns.")
print()
print("To properly compare authored vs converted output:")
print("1. The authored data uses frame-based representation (ability_frame_source_authored.json)")
print("2. The extracted data uses semantic representation (abilities_extracted_from_cards.json)")
print("3. Direct comparison requires running semantic-to-frame conversion on extracted data")
print()
print("Next steps:")
print("- Run semantic_to_frame_converter.py on abilities_extracted_from_cards.json")
print("- Compare the generated frames with ability_frame_source_authored.json")
print("- Identify gaps in the conversion process")
