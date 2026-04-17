"""Find cards with hand-based cost reduction abilities."""

import json

with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Find cards with hand-based cost reduction
for card_id, card in cards.items():
    ability = card.get('ability', '')
    if ability and '手札' in ability and ('コスト' in ability or '安く' in ability or '減る' in ability or '減らす' in ability):
        print(f"Card ID: {card_id}")
        print(f"Name: {card.get('name', '')}")
        print(f"Ability: {ability}")
        print()
