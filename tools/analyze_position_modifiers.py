#!/usr/bin/env python3
"""
Extract and analyze abilities with position modifiers (center, left, right).
"""
import json
import sys

# Position patterns to search for
POSITION_PATTERNS = [
    '{{center.png|センター}}',
    '【左サイド】',
    '【右サイド】',
    'ステージの左サイドエリア',
    'ステージの右サイドエリア'
]

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Search through unique abilities
results = []
for i, ability in enumerate(data['unique_abilities'], 1):
    full_text = ability.get('full_text', '')
    costless_text = ability.get('costless_text', '')
    
    # Check if any position pattern is present
    found_positions = []
    for pattern in POSITION_PATTERNS:
        if pattern in full_text or pattern in costless_text:
            found_positions.append(pattern)
    
    if found_positions:
        results.append({
            'index': i,
            'full_text': full_text,
            'triggerless_text': ability.get('triggerless_text', ''),
            'triggers': ability.get('triggers', ''),
            'costless_text': costless_text,
            'positions': found_positions,
            'effect': ability.get('effect'),
            'card_count': ability.get('card_count', 0)
        })

# Group by position
position_counts = {}
for result in results:
    for pos in result['positions']:
        position_counts[pos] = position_counts.get(pos, 0) + 1

# Create output structure
output = {
    'total_abilities_with_positions': len(results),
    'total_unique_abilities': len(data['unique_abilities']),
    'percentage': len(results) / len(data['unique_abilities']) * 100,
    'position_counts': position_counts,
    'abilities': results
}

# Write to JSON file
with open('data/position_modifiers_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# Print summary
print(f"Total abilities with position modifiers: {len(results)}")
print(f"Total unique abilities: {len(data['unique_abilities'])}")
print(f"Percentage: {len(results) / len(data['unique_abilities']) * 100:.1f}%")
print()
print("Position pattern counts:")
for pos, count in sorted(position_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {pos}: {count}")
print()
print(f"Output written to data/position_modifiers_analysis.json")
