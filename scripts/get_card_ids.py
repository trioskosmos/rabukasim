import json

# Load cards.json
with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Mismatched cards from comparison
mismatched = [
    'PL!-bp3-025-L', 'PL!N-bp5-010-R', 'PL!N-bp5-010-AR',
    'PL!HS-bp1-003-R+', 'PL!HS-bp1-003-P', 'PL!HS-bp1-003-P+',
    'PL!-PR-007-PR', 'PL!-PR-009-PR', 'PL!S-bp3-012-N',
    'PL!N-bp1-003-R+', 'PL!N-bp1-003-P', 'PL!N-bp1-003-P+'
]

print('Card IDs for mismatched cards:')
for card_no in mismatched:
    if card_no in cards:
        card = cards[card_no]
        print(f'{card_no}: ID={card.get("id")}, Name={card.get("name")}')
    else:
        print(f'{card_no}: NOT FOUND')
