import json

cards_data = json.load(open('data/cards.json', encoding='utf-8'))

# Check the card with the truncated ability
card_id = "PL!-sd1-009-SD"
if card_id in cards_data:
    card = cards_data[card_id]
    print(f"Card: {card['name']}")
    print(f"Ability: {card.get('ability', 'N/A')}")
    print(f"Ability length: {len(card.get('ability', ''))}")
    print()
    
# Check a few more cards
for card_id, card in list(cards_data.items())[:5]:
    if card.get('ability'):
        print(f"{card_id}: {card['name']}")
        print(f"  Ability: {card['ability'][:100]}...")
        print()
