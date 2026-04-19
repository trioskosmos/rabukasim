import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    extracted = json.load(f)

# Find card 47
for card_id, card_data in extracted.items():
    if card_id == '47':
        print(f"Card 47 found")
        print(json.dumps(card_data, indent=2, ensure_ascii=False))
        break
