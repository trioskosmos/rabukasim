#!/usr/bin/env python3
"""Find card_nos for the failing test characters."""
import json

with open('cards.json', 'r', encoding='utf-8') as f:
    cards_json = json.load(f)

# Find cards for test characters
test_chars = {
    '徒町 小鈴': [],
    '徒町小鈴': [],
    '黒澤 ルビィ': [],
    '黒澤ルビィ': [],
    '若菜 渉紀': [],
    '若菜渉紀': [],
}

for card_no, card in cards_json.items():
    name = card.get('name', '')
    for char in test_chars:
        if char in name:
            test_chars[char].append(card_no)

for char, cards in test_chars.items():
    if cards:
        print(f"\n{char}: {len(cards)} cards")
        for card_no in cards[:5]:
            print(f"  {card_no}")

# Also provide specific card_nos that should work
print("\n\nSpecific card_nos to use:")
print("- 徒町 小鈴: PL!HS-bp1-008-P")
print("- 黒澤 ルビィ: PL!S-bp2-004-P")
print("- 若菜 渉紀: (need to find)")
