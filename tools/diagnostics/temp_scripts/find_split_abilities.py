#!/usr/bin/env python3
"""Find abilities that were split from multi-trigger cards."""

import json

with open('c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/data/abilities_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Group by card to find split abilities
card_abilities = {}
for ability in data['abilities']:
    cards = ability['source_ability_texts'][0]['cards']
    for card in cards:
        card_id = card.split(' | ')[0]
        if card_id not in card_abilities:
            card_abilities[card_id] = []
        card_abilities[card_id].append({
            'trigger': ability['trigger'],
            'jp': ability['source_ability_texts'][0]['jp'][:100]
        })

# Find cards with multiple abilities (split)
split_cards = {k: v for k, v in card_abilities.items() if len(v) > 1}

print(f"Cards with split abilities: {len(split_cards)}")
print("=" * 60)

# Show first 5 examples
for i, (card_id, abilities) in enumerate(list(split_cards.items())[:5]):
    print(f"\nCard: {card_id}")
    for j, ability in enumerate(abilities):
        print(f"  [{j+1}] {ability['trigger']}: {ability['jp']}...")
