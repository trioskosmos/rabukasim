import json

with open("data/cards.json", encoding="utf-8") as f:
    cards = json.load(f)

problem_cards = ["PL!HS-bp2-001-R", "PL!S-bp3-008-R", "PL!-bp3-026-L", "PL!S-bp3-024-L", "PL!-pb1-002-R"]
for card_id in problem_cards:
    card = cards.get(card_id, {})
    print(f"=== {card_id}: {card.get('name', 'Unknown')} ===")
    print(card.get("ability", "No ability")[:300])
    print()
