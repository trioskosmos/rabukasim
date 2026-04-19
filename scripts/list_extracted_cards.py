import json

with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    extracted = json.load(f)

print(f"Total cards in extracted: {len(extracted)}")
print(f"Card IDs: {list(extracted.keys())[:20]}")

if '47' in extracted:
    print("\nCard 47 found")
else:
    print("\nCard 47 NOT found")
    # Try to find a card with similar ID
    for card_id in extracted.keys():
        if '47' in str(card_id):
            print(f"Found card with 47 in ID: {card_id}")
